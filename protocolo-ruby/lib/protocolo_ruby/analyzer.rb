# frozen_string_literal: true
require 'digest'
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
        schema_version: '0.1.0', filename: File.basename(filename.to_s).byteslice(0, 128),
        size_bytes: data.bytesize,
        hashes: { sha256: Digest::SHA256.hexdigest(data), sha1: Digest::SHA1.hexdigest(data), md5: Digest::MD5.hexdigest(data) },
        format: format, entropy: entropy.round(4), strings: strings,
        indicators: {
          urls: text.scan(%r{https?://[a-zA-Z0-9._~:/?#\[\]@!$&'()*+,;=%-]+}).uniq.first(100),
          ipv4: text.scan(/\b(?:\d{1,3}\.){3}\d{1,3}\b/).uniq.select { |ip| ip.split('.').all? { |n| n.to_i <= 255 } }.first(100)
        },
        status: 'indeterminate', note: 'Static analysis only; not a malware verdict.'
      }
    end
  end
end
