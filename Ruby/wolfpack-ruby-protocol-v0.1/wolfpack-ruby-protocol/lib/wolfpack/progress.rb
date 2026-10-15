# frozen_string_literal: true

require 'fileutils'
require 'json'

module Wolfpack
  class Progress
    DEFAULT_PATH = File.join(Dir.home, '.wolfpack_ruby', 'progress.json')
    attr_reader :codename, :completed

    def initialize(path: ENV.fetch('WOLFPACK_SAVE_PATH', DEFAULT_PATH))
      @path = path
      @codename = nil
      @completed = []
      load_file
    end

    def codename=(value)
      @codename = value.to_s.strip[0, 24]
      save
    end

    def done?(id)
      @completed.include?(id)
    end

    def complete!(id)
      return false if done?(id)

      @completed << id
      @completed.sort!
      save
      true
    end

    def reset!
      @codename = nil
      @completed = []
      save
    end

    def xp
      @completed.length * 100
    end

    private

    def load_file
      return unless File.file?(@path)

      data = JSON.parse(File.read(@path))
      @codename = data['codename'].to_s[0, 24] if data['codename'].is_a?(String)
      @completed = Array(data['completed']).select { |id| id.is_a?(Integer) && (1..12).cover?(id) }.uniq.sort
    rescue JSON::ParserError, SystemCallError
      warn 'WolfPack: save inválido ou inacessível; iniciando uma nova campanha.'
    end

    def save
      FileUtils.mkdir_p(File.dirname(@path))
      temp_path = "#{@path}.tmp.#{$$}"
      File.write(temp_path, JSON.pretty_generate({ version: 1, codename: @codename, completed: @completed }))
      File.rename(temp_path, @path)
    ensure
      File.delete(temp_path) if defined?(temp_path) && File.exist?(temp_path)
    end
  end
end
