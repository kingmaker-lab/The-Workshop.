# frozen_string_literal: true
require 'digest'
require_relative 'binary_inspector'
module ProtocoloRuby
  class Analyzer
    MAX_BYTES = 20 * 1024 * 1024
    def analyze(bytes, filename: 'sample.bin')
      raise ArgumentError, 'Invalid input' unless bytes.is_a?(String) && !bytes.empty? && bytes.bytesize <= MAX_BYTES
      data = bytes.b
      strings = data.scan(/[\x20-\x7e]{5,}/n).first(100).map { |s| s.byteslice(0, 160).dup.force_encoding('UTF-8').scrub }
      counts = Array.new(256, 0)
      data.each_byte { |byte| counts[byte] += 1 }
      entropy = counts.sum { |n| n.zero? ? 0.0 : (p = n.to_f / data.bytesize; -p * Math.log2(p)) }
      format = if data.start_with?('MZ') then 'PE (MZ header)'
               elsif data.start_with?("\x7fELF".b) then 'ELF'
               elsif data.start_with?('%PDF-') then 'PDF'
               elsif data.start_with?("PK\x03\x04".b) then 'ZIP'
               else 'Unknown' end
      text = strings.join("\n")
      {
        schema_version: '0.4.0', filename: File.basename(filename.to_s).byteslice(0, 128),
        size_bytes: data.bytesize,
        hashes: { sha256: Digest::SHA256.hexdigest(data), sha1: Digest::SHA1.hexdigest(data), md5: Digest::MD5.hexdigest(data) },
        format: format, binary_header: BinaryInspector.inspect(data),
        hex_preview: BinaryInspector.hex_preview(data), entropy: entropy.round(4), strings: strings,
        indicators: {
          urls: text.scan(%r{https?://[a-zA-Z0-9._~:/?#\[\]@!$&'()*+,;=%-]+}).uniq.first(100),
          ipv4: text.scan(/\b(?:\d{1,3}\.){3}\d{1,3}\b/).uniq.select { |ip| ip.split('.').all? { |n| n.to_i <= 255 } }.first(100)
        },
        findings: investigative_hints(data, entropy, text),
        status: 'indeterminate', note: 'Static evidence only; findings are not a malware verdict.'
      }
    end
    private

    def investigative_hints(data, entropy, text)
      findings = []
      if data.bytesize >= 1024 && entropy >= 7.2
        findings << { code: 'HIGH_ENTROPY', confidence: 'low', evidence: "Shannon entropy #{entropy.round(3)} bits/byte" }
      end
      urls = text.scan(%r{https?://[^\s"'<>]+}).uniq
      findings << { code: 'URL_STRINGS', confidence: 'informational', evidence: "#{urls.size} URL(s) in printable strings" } unless urls.empty?
      hdr = BinaryInspector.inspect(data)
      if %w[PE ELF].include?(hdr[:type]) && !hdr[:valid_header]
        findings << { code: 'INVALID_EXECUTABLE_HEADER', confidence: 'low', evidence: hdr[:reason] }
      end
      findings
    end
  end
end
