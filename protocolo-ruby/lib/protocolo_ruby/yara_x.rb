# frozen_string_literal: true
require 'open3'
require 'timeout'
require 'tempfile'

module ProtocoloRuby
  # Optional adapter. Run only inside an isolated worker.
  class YaraX
    def initialize(rules_path:, executable: 'yr', timeout_seconds: 10)
      @rules_path = File.realpath(rules_path)
      raise ArgumentError, 'Rules must be a regular file' unless File.file?(@rules_path)
      @executable = executable
      @timeout_seconds = Integer(timeout_seconds)
      raise ArgumentError, 'Invalid timeout' unless (1..120).cover?(@timeout_seconds)
    end

    def scan(bytes)
      raise ArgumentError, 'Invalid sample' unless bytes.is_a?(String) && bytes.bytesize.between?(1, 20 * 1024 * 1024)
      Tempfile.create(['ruby-sample-', '.bin']) do |sample|
        sample.binmode
        sample.write(bytes)
        sample.flush
        stdout, stderr, status = Timeout.timeout(@timeout_seconds) do
          Open3.capture3(@executable, 'scan', @rules_path, sample.path)
        end
        # yr scan returns 1 when rules matched
        raise "YARA-X CLI failed: #{stderr.byteslice(0, 240)}" unless [0, 1].include?(status.exitstatus)
        { engine: 'YARA-X', matches: stdout.lines.map(&:strip).reject(&:empty?).first(100), verdict: 'indeterminate' }
      end
    rescue Timeout::Error
      raise 'YARA-X scan timed out'
    end
  end
end
