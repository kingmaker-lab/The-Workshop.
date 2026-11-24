# frozen_string_literal: true
require_relative 'runner'
require_relative '../tasks/registry'

module Orion
  module System
    class Supervisor
      def initialize(runner: Runner.new)
        @runner = runner
      end

      # External callers can select only a statically registered task id.
      def run(id:, kind:, timeout: Runner::DEFAULT_TIMEOUT, input: nil)
        task = Orion::Tasks::Registry.fetch(id, kind: kind)
        @runner.run(task: task, timeout: timeout, input: input)
      end
    end
  end
end
