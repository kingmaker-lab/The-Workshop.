# frozen_string_literal: true
module Orion
  module System
    Result = Struct.new(:task, :name, :status, :exit_code, :duration_ms,
                        :timed_out, :stdout, :stderr, :stdout_truncated,
                        :stderr_truncated, keyword_init: true) do
      def success?
        status == 'completed'
      end

      def to_h
        members.to_h { |key| [key, self[key]] }
      end
    end
  end
end
