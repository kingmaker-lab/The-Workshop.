# frozen_string_literal: true
require "json"
require "optparse"
require "rbconfig"

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
        help                 Esta ajuda

      Opções:
        --json               Saída estruturada (info, inspect, hash, labs)
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
      when nil, "help", "--help", "-h"
        @out.puts HELP
        0
      when "info" then info(args)
      when "inspect" then inspect_file(args)
      when "hash" then hash_file(args)
      when "labs" then labs(args)
      else
        @err.puts "Comando desconhecido: #{command.inspect}"
        @err.puts "Use 'orion help'."
        2
      end
    rescue OptionParser::ParseError, ArgumentError, Orion::Files::InvalidFile, SystemCallError => e
      @err.puts "orion: #{e.message}"
      2
    end

    private

    def parse_json(args)
      json = false
      OptionParser.new { |opts| opts.on("--json", "Saída JSON") { json = true } }.parse!(args)
      raise ArgumentError, "argumentos inesperados: #{args.join(' ')}" unless args.empty?
      json
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
        project: "Ruby Orion",
        version: Orion::VERSION,
        ruby: RUBY_DESCRIPTION,
        engine: defined?(RUBY_ENGINE) ? RUBY_ENGINE : "ruby",
        platform: RUBY_PLATFORM,
        architecture: RbConfig::CONFIG["host_cpu"]
      }, json: json)
      0
    end

    def inspect_file(args)
      json = false
      OptionParser.new { |opts| opts.on("--json") { json = true } }.parse!(args)
      raise ArgumentError, "informe exatamente um arquivo" unless args.length == 1
      emit(Orion::Files.inspect(args.fetch(0)), json: json)
      0
    end

    def hash_file(args)
      json = false
      algorithm = "sha256"
      expected = nil
      OptionParser.new do |opts|
        opts.on("--json") { json = true }
        opts.on("--algorithm ALG", Orion::Files::ALGORITHMS.keys) { |value| algorithm = value }
        opts.on("--verify HEX") { |value| expected = value }
      end.parse!(args)
      raise ArgumentError, "informe exatamente um arquivo" unless args.length == 1
      result = Orion::Files.hash(args.fetch(0), algorithm: algorithm)
      if expected
        length = Orion::Files::ALGORITHMS.fetch(algorithm).hexdigest("".b).length
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
        @out.puts "RUBY ORION / LABORATÓRIOS"
        entries.each { |entry| @out.puts "#{entry[:id]} · #{entry[:title]} [#{entry[:status]}] | #{entry[:pillar]}" }
      end
      0
    end
  end
end
