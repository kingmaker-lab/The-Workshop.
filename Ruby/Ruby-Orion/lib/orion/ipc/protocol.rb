# frozen_string_literal: true
require 'json'
module Orion
  module IPC
    class ProtocolError < StandardError; end

    module Protocol
      NAME = 'orion-ipc'
      VERSION = 1
      TYPES = %w[request response error].freeze
      MAX_FRAME_BYTES = 4096

      module_function

      def encode(type:, payload:)
        raise ProtocolError, 'tipo de mensagem inválido' unless TYPES.include?(type)
        raise ProtocolError, 'payload precisa ser um objeto JSON' unless payload.is_a?(Hash)
        frame = JSON.generate({ protocol: NAME, version: VERSION, type: type, payload: payload }) + "\n"
        raise ProtocolError, 'mensagem excede 4 KiB' if frame.bytesize > MAX_FRAME_BYTES
        frame
      rescue JSON::GeneratorError, Encoding::InvalidByteSequenceError => e
        raise ProtocolError, "mensagem JSON inválida: #{e.class}"
      end

      def decode(frame)
        raise ProtocolError, 'mensagem precisa terminar em newline' unless frame.is_a?(String) && frame.end_with?("\n")
        raise ProtocolError, 'mensagem excede 4 KiB' if frame.bytesize > MAX_FRAME_BYTES
        text = frame.dup.force_encoding(Encoding::UTF_8)
        raise ProtocolError, 'mensagem não é UTF-8' unless text.valid_encoding?
        parsed = JSON.parse(text, max_nesting: 16)
        unless parsed.is_a?(Hash) && parsed.keys.sort == %w[payload protocol type version] &&
               parsed['protocol'] == NAME && parsed['version'] == VERSION &&
               TYPES.include?(parsed['type']) && parsed['payload'].is_a?(Hash)
          raise ProtocolError, 'contrato de mensagem inválido'
        end
        parsed
      rescue JSON::ParserError, JSON::NestingError => e
        raise ProtocolError, "JSON inválido: #{e.class}"
      end
    end
  end
end
