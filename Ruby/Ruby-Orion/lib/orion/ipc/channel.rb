# frozen_string_literal: true
require_relative 'protocol'
module Orion
  module IPC
    class Channel
      def initialize(input:, output:)
        @input = input
        @output = output
      end

      def read
        line = @input.gets("\n", Protocol::MAX_FRAME_BYTES + 1)
        return nil if line.nil?
        Protocol.decode(line)
      end

      def write(type:, payload:)
        @output.write(Protocol.encode(type: type, payload: payload))
        @output.flush
      end
    end
  end
end
