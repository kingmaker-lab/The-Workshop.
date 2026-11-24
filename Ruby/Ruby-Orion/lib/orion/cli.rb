# frozen_string_literal: true
require 'json'
require 'optparse'
require 'rbconfig'
require 'stringio'

module Orion
  class CLI
    HELP = <<~TEXT.freeze
      RUBY ORION · The Workshop
      Three Stars. Infinite Possibilities.

      Uso: orion <comando> [opções]

      Comandos:
        info                 Ambiente de execução Ruby
        inspect ARQUIVO      Assinatura e entropia de amostra de arquivo
        hash ARQUIVO         SHA-256/SHA-512 com leitura em blocos
        labs                 Laboratórios disponíveis e planejados
        process list         Lista tarefas de processo locais cadastradas
        process run 002      Executa o laboratório de processos com timeout
        ipc demo             Troca mensagens JSON via pipes entre processos Ruby
        help                 Esta ajuda
        version              Versão do Ruby Orion

      Opções:
        --json               Saída estruturada
        --timeout SEGUNDOS   Entre 0.1 e 30 segundos (padrão: 5)
        --algorithm ALG      sha256 ou sha512 (hash)
        --verify HEX         Confere digest esperado (hash)
    TEXT

    def initialize(out: $stdout, err: $stderr)
      @out = out
      @err = err
    end

    def run(argv)
      args = argv.dup
      command = args.shift
      case command
      when nil, 'help', '--help', '-h'
        @out.puts HELP
        0
      when 'version', '--version', '-v'
        @out.puts "Ruby Orion #{Orion::VERSION}"
        0
      when 'info' then info(args)
      when 'inspect' then inspect_file(args)
      when 'hash' then hash_file(args)
      when 'labs' then labs(args)
      when 'process' then process_command(args)
      when 'ipc' then ipc_command(args)
      else
        @err.puts "Comando desconhecido: #{command.inspect}"
        @err.puts "Use 'orion help'."
        2
      end
    rescue OptionParser::ParseError, ArgumentError, Orion::Files::InvalidFile,
           Orion::System::Runner::InvalidInput, Orion::IPC::ProtocolError,
           SystemCallError => e
      @err.puts "orion: #{e.message}"
      2
    end

    private

    def parse_json(args)
      json = false
      OptionParser.new { |opts| opts.on('--json', 'Saída JSON') { json = true } }.parse!(args)
      raise ArgumentError, "argumentos inesperados: #{args.join(' ')}" unless args.empty?
      json
    end

    def parse_run_options(args)
      json = false
      timeout = Orion::System::Runner::DEFAULT_TIMEOUT
      OptionParser.new do |opts|
        opts.on('--json', 'Saída JSON') { json = true }
        opts.on('--timeout SECONDS', Float, 'Timeout em segundos') { |value| timeout = value }
      end.parse!(args)
      raise ArgumentError, "argumentos inesperados: #{args.join(' ')}" unless args.empty?
      unless timeout.finite? && timeout.between?(0.1, Orion::System::Runner::MAX_TIMEOUT)
        raise ArgumentError, 'timeout deve estar entre 0.1 e 30 segundos'
      end
      [json, timeout]
    end

    def emit(payload, json: false)
      if json
        @out.puts JSON.pretty_generate(payload)
      else
        payload.each { |key, value| @out.puts "#{key.to_s.tr('_', ' ')}: #{value}" }
      end
    end

    def info(args)
      json = parse_json(args)
      emit({
        project: 'Ruby Orion',
        version: Orion::VERSION,
        ruby: RUBY_DESCRIPTION,
        engine: defined?(RUBY_ENGINE) ? RUBY_ENGINE : 'ruby',
        platform: RUBY_PLATFORM,
        architecture: RbConfig::CONFIG['host_cpu']
      }, json: json)
      0
    end

    def inspect_file(args)
      json = false
      OptionParser.new { |opts| opts.on('--json') { json = true } }.parse!(args)
      raise ArgumentError, 'informe exatamente um arquivo' unless args.length == 1
      emit(Orion::Files.inspect(args.fetch(0)), json: json)
      0
    end

    def hash_file(args)
      json = false
      algorithm = 'sha256'
      expected = nil
      OptionParser.new do |opts|
        opts.on('--json') { json = true }
        opts.on('--algorithm ALG', Orion::Files::ALGORITHMS.keys) { |value| algorithm = value }
        opts.on('--verify HEX') { |value| expected = value }
      end.parse!(args)
      raise ArgumentError, 'informe exatamente um arquivo' unless args.length == 1
      result = Orion::Files.hash(args.fetch(0), algorithm: algorithm)
      if expected
        length = Orion::Files::ALGORITHMS.fetch(algorithm).hexdigest(''.b).length
        raise ArgumentError, "digest esperado deve ter #{length} caracteres hexadecimais" unless expected.match?(/\A[0-9a-fA-F]+\z/) && expected.length == length
        result[:verified] = (result[:digest] == expected.downcase)
      end
      emit(result, json: json)
      result.fetch(:verified, true) ? 0 : 1
    end

    def labs(args)
      json = parse_json(args)
      entries = Orion::Labs.entries
      if json
        @out.puts JSON.pretty_generate(entries)
      else
        @out.puts 'RUBY ORION / LABORATÓRIOS'
        entries.each { |entry| @out.puts "#{entry[:id]} · #{entry[:title]} [#{entry[:status]}] | #{entry[:pillar]}" }
      end
      0
    end

    def process_command(args)
      subcommand = args.shift
      case subcommand
      when 'list'
        json = parse_json(args)
        tasks = Orion::Tasks::Registry.list(kind: 'process')
        json ? @out.puts(JSON.pretty_generate(tasks)) : tasks.each { |task| @out.puts "#{task[:id]} · #{task[:name]}" }
        0
      when 'run'
        id = args.shift
        raise ArgumentError, 'informe o id da tarefa (ex.: 002)' if id.nil?
        json, timeout = parse_run_options(args)
        result = Orion::System::Supervisor.new.run(id: id, kind: 'process', timeout: timeout)
        emit(result.to_h, json: json)
        exit_status(result)
      else
        raise ArgumentError, "subcomando process desconhecido: #{subcommand.inspect}"
      end
    end

    def ipc_command(args)
      subcommand = args.shift
      raise ArgumentError, "subcomando ipc desconhecido: #{subcommand.inspect}" unless subcommand == 'demo'
      json, timeout = parse_run_options(args)
      input = Orion::IPC::Protocol.encode(type: 'request', payload: { values: [8, 13, 21] })
      result = Orion::System::Supervisor.new.run(id: '003', kind: 'ipc', timeout: timeout, input: input)
      response = nil
      if result.success? && !result.stdout_truncated
        response = Orion::IPC::Channel.new(input: StringIO.new(result.stdout), output: StringIO.new).read
        raise Orion::IPC::ProtocolError, 'resposta IPC inesperada' unless response && response.fetch('type') == 'response'
      end
      output = { task: result.task, status: result.status, exit_code: result.exit_code,
                 duration_ms: result.duration_ms, timed_out: result.timed_out,
                 stdout_truncated: result.stdout_truncated, stderr_truncated: result.stderr_truncated,
                 response: response && response['payload'] }
      emit(output, json: json)
      exit_status(result)
    end

    def exit_status(result)
      return 124 if result.timed_out
      result.success? ? 0 : 1
    end
  end
end
