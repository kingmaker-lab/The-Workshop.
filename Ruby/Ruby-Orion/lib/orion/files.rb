# frozen_string_literal: true
require "digest"

module Orion
  module Files
    SAMPLE_BYTES = 4096
    CHUNK_BYTES = 64 * 1024
    ALGORITHMS = { "sha256" => Digest::SHA256, "sha512" => Digest::SHA512 }.freeze

    class InvalidFile < StandardError; end

    module_function

    def with_regular_file(path)
      raise InvalidFile, "caminho vazio" if path.to_s.empty?
      info = File.lstat(path)
      raise InvalidFile, "links simbólicos não são aceitos" if info.symlink?
      raise InvalidFile, "somente arquivos regulares são aceitos" unless info.file?

      flags = File::RDONLY
      flags |= File::NOFOLLOW if defined?(File::NOFOLLOW)
      flags |= File::NONBLOCK if defined?(File::NONBLOCK)
      File.open(path, flags) do |io|
        raise InvalidFile, "arquivo alterado durante a abertura" unless io.stat.file?
        yield io
      end
    rescue Errno::ELOOP
      raise InvalidFile, "links simbólicos não são aceitos"
    end

    def inspect(path)
      with_regular_file(path) do |io|
        sample = io.read(SAMPLE_BYTES) || "".b
        {
          name: File.basename(path),
          size_bytes: io.stat.size,
          signature: signature(sample),
          entropy_sample: entropy(sample),
          sampled_bytes: sample.bytesize
        }
      end
    end

    def hash(path, algorithm: "sha256")
      digest_type = ALGORITHMS.fetch(algorithm) { raise ArgumentError, "algoritmo inválido: #{algorithm}" }
      with_regular_file(path) do |io|
        digest = digest_type.new
        while (chunk = io.read(CHUNK_BYTES))
          digest.update(chunk)
        end
        { name: File.basename(path), algorithm: algorithm, digest: digest.hexdigest, size_bytes: io.stat.size }
      end
    end

    def signature(bytes)
      return "ELF" if bytes.start_with?("\x7fELF".b)
      if bytes.start_with?("MZ".b)
        offset = bytes.byteslice(0x3c, 4)&.unpack1("V")
        return "PE" if offset && offset + 4 <= bytes.bytesize && bytes.byteslice(offset, 4) == "PE\0\0".b
        return "MZ (possível PE)"
      end
      return "PNG" if bytes.start_with?("\x89PNG\r\n\x1a\n".b)
      return "PDF" if bytes.start_with?("%PDF-".b)
      return "ZIP" if bytes.start_with?("PK\x03\x04".b)
      return "GIF" if bytes.start_with?("GIF87a".b, "GIF89a".b)
      "desconhecida"
    end

    def entropy(bytes)
      return 0.0 if bytes.empty?
      frequencies = Array.new(256, 0)
      bytes.each_byte { |b| frequencies[b] += 1 }
      total = bytes.bytesize.to_f
      -frequencies.sum do |count|
        next 0.0 if count.zero?
        probability = count / total
        probability * Math.log2(probability)
      end.round(4)
    end
  end
end
