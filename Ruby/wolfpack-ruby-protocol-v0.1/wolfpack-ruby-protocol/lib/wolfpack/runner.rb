# frozen_string_literal: true

require 'open3'
require 'rbconfig'

module Wolfpack
  RunResult = Struct.new(:output, :error, :status, :timed_out, keyword_init: true)

  # Executa Ruby digitado pelo próprio jogador em um novo processo local.
  # NÃO É SANDBOX DE SEGURANÇA: código não confiável nunca deve ser executado.
  class Runner
    DEFAULT_TIMEOUT = 3.0
    MAX_OUTPUT_BYTES = 16_384

    def initialize(timeout: DEFAULT_TIMEOUT)
      @timeout = timeout
    end

    def run(source, stdin_data: '')
      stdout_text = +''
      stderr_text = +''
      exit_status = nil
      timed_out = false

      Open3.popen3(RbConfig.ruby, '--disable-gems', '-e', "# encoding: UTF-8\n#{source}", pgroup: true) do |input, out, err, waiter|
        begin
          input.write(stdin_data)
        rescue Errno::EPIPE
          # O programa pode ter terminado sem ler a entrada.
        ensure
          input.close unless input.closed?
        end

        streams = { out => stdout_text, err => stderr_text }
        deadline = Process.clock_gettime(Process::CLOCK_MONOTONIC) + @timeout

        until streams.empty?
          remaining = deadline - Process.clock_gettime(Process::CLOCK_MONOTONIC)
          if remaining <= 0
            timed_out = true
            break
          end

          ready = IO.select(streams.keys, nil, nil, remaining)
          unless ready
            timed_out = true
            break
          end

          ready[0].each do |stream|
            chunk = stream.read_nonblock(4096, exception: false)
            if chunk.nil?
              streams.delete(stream)
            elsif chunk != :wait_readable
              streams[stream] << chunk
            end
          end

          if stdout_text.bytesize + stderr_text.bytesize > MAX_OUTPUT_BYTES
            timed_out = true
            stderr_text << "\nSaída excedeu #{MAX_OUTPUT_BYTES} bytes.\n"
            break
          end
        end

        if timed_out
          begin
            Process.kill('KILL', -waiter.pid)
          rescue Errno::ESRCH
            # O processo já foi finalizado.
          end
        end
        exit_status = waiter.value.exitstatus
      end

      RunResult.new(output: stdout_text, error: stderr_text, status: exit_status, timed_out: timed_out)
    rescue SystemCallError => e
      RunResult.new(output: '', error: "Falha ao iniciar Ruby: #{e.message}", status: nil, timed_out: false)
    end
  end

  CheckResult = Struct.new(:success, :feedback, :case_number, keyword_init: true)

  class Validator
    def initialize(runner: Runner.new)
      @runner = runner
    end

    def check(lesson, source)
      return CheckResult.new(success: false, feedback: 'O código está vazio.') if source.strip.empty?

      lesson.requirements.each do |pattern, message|
        unless source.match?(pattern)
          return CheckResult.new(success: false, feedback: "Conceito ainda não aplicado: #{message}")
        end
      end

      lesson.cases.each_with_index do |(input, expected), i|
        result = @runner.run(source, stdin_data: input)
        if result.timed_out
          return CheckResult.new(success: false, feedback: 'Execução interrompida após o limite de tempo/saída. Confira seus loops.', case_number: i + 1)
        end
        unless result.status == 0
          description = result.error.lines.first(6).join.strip
          return CheckResult.new(success: false, feedback: "Ruby encontrou um erro:\n#{description}", case_number: i + 1)
        end
        if normalize(result.output) != normalize(expected)
          return CheckResult.new(
            success: false,
            feedback: "Resultado esperado:\n#{expected.strip}\n\nSeu programa exibiu:\n#{result.output.strip.empty? ? '(nada)' : result.output.strip}",
            case_number: i + 1
          )
        end
      end
      CheckResult.new(success: true, feedback: "#{lesson.cases.length} teste(s) passaram! Código validado.")
    end

    private

    def normalize(value)
      value.gsub("\r\n", "\n").sub(/\n\z/, '')
    end
  end
end
