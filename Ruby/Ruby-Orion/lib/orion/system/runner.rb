# frozen_string_literal: true
require 'open3'
require 'rbconfig'
require_relative 'result'

module Orion
  module System
    # For local, trusted Ruby scripts only. This is NOT a security sandbox.
    class Runner
      DEFAULT_TIMEOUT = 5.0
      MAX_TIMEOUT = 30.0
      DEFAULT_OUTPUT_BYTES = 32 * 1024
      MAX_INPUT_BYTES = 8 * 1024
      GRACE_SECONDS = 0.3
      READER_JOIN_SECONDS = 0.6

      class InvalidInput < StandardError; end

      def run(task:, timeout: DEFAULT_TIMEOUT, input: nil, max_output_bytes: DEFAULT_OUTPUT_BYTES)
        validate!(task, timeout, input, max_output_bytes)
        start = monotonic
        timed_out = false
        captured = {}
        result_status = nil

        spawn_opts = { chdir: project_root, unsetenv_others: true, close_others: true }
        spawn_opts[:pgroup] = true unless windows?
        environment = { 'LANG' => 'C.UTF-8', 'LC_ALL' => 'C.UTF-8' }

        # Two distinct argv strings ensure no shell parsing of child scripts or args.
        Open3.popen3(environment, RbConfig.ruby, task.script, spawn_opts) do |stdin, stdout, stderr, waiter|
          writers = []
          readers = {
            stdout: Thread.new { drain(stdout, max_output_bytes) },
            stderr: Thread.new { drain(stderr, max_output_bytes) }
          }
          begin
            writers << Thread.new { write_input(stdin, input) }
            remaining = [timeout.to_f - (monotonic - start), 0.0].max
            if !waiter.join(remaining)
              timed_out = true
              stop_child(waiter.pid, waiter, group: !windows?)
            end
            result_status = waiter.value unless waiter.alive?
          ensure
            safe_close(stdin)
            stop_child(waiter.pid, waiter, group: !windows?) if waiter.alive?
            writers.each { |thread| thread.join(READER_JOIN_SECONDS) || thread.kill }
            readers.each do |name, thread|
              unless thread.join(READER_JOIN_SECONDS)
                safe_close(name == :stdout ? stdout : stderr)
                thread.join(READER_JOIN_SECONDS)
              end
              captured[name] = thread.value if !thread.alive?
              captured[name] ||= ['', true]
            end
          end
        end

        exit_code = result_status&.exitstatus
        status = timed_out ? 'timed_out' : (exit_code == 0 ? 'completed' : 'failed')
        Result.new(task: task.id, name: task.name, status: status,
                   exit_code: exit_code, duration_ms: ((monotonic - start) * 1000).round,
                   timed_out: timed_out, stdout: captured.fetch(:stdout)[0],
                   stderr: captured.fetch(:stderr)[0],
                   stdout_truncated: captured.fetch(:stdout)[1],
                   stderr_truncated: captured.fetch(:stderr)[1])
      end

      private

      def project_root
        File.expand_path('../../..', __dir__)
      end

      def monotonic
        Process.clock_gettime(Process::CLOCK_MONOTONIC)
      end

      def windows?
        RbConfig::CONFIG.fetch('host_os').match?(/mswin|mingw|cygwin/i)
      end

      def validate!(task, timeout, input, output_limit)
        raise InvalidInput, 'tarefa inválida' unless task.respond_to?(:script) && task.respond_to?(:name) && task.respond_to?(:id)
        raise InvalidInput, 'script da tarefa precisa ser um arquivo Ruby local' unless task.script.is_a?(String) && File.file?(task.script) && File.extname(task.script) == '.rb'
        raise InvalidInput, 'timeout deve estar entre 0.1 e 30 segundos' unless timeout.is_a?(Numeric) && timeout.finite? && timeout.between?(0.1, MAX_TIMEOUT)
        raise InvalidInput, 'entrada precisa ser texto' unless input.nil? || input.is_a?(String)
        raise InvalidInput, 'entrada excede 8 KiB' if input && input.bytesize > MAX_INPUT_BYTES
        raise InvalidInput, 'limite de saída inválido' unless output_limit.is_a?(Integer) && output_limit.between?(1, DEFAULT_OUTPUT_BYTES)
      end

      def drain(io, limit)
        output = +''.b
        truncated = false
        loop do
          bytes = io.readpartial(4096)
          available = [limit - output.bytesize, 0].max
          output << bytes.byteslice(0, available) if available.positive?
          truncated ||= bytes.bytesize > available
        end
      rescue EOFError, IOError, Errno::EBADF
        [output.force_encoding(Encoding::UTF_8).scrub, truncated]
      end

      def write_input(io, input)
        io.write(input) unless input.nil?
      rescue Errno::EPIPE, IOError
        nil
      ensure
        safe_close(io)
      end

      def stop_child(pid, waiter, group:)
        signal(pid, 'TERM', group: group)
        return if waiter.join(GRACE_SECONDS)
        signal(pid, 'KILL', group: group)
        waiter.join(1.0)
      end

      def signal(pid, name, group:)
        Process.kill(name, group ? -pid : pid)
      rescue Errno::ESRCH, Errno::EPERM
        nil
      end

      def safe_close(io)
        io.close unless io.closed?
      rescue IOError
        nil
      end
    end
  end
end
