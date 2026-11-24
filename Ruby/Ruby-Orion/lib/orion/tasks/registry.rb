# frozen_string_literal: true
module Orion
  module Tasks
    Task = Struct.new(:id, :name, :kind, :script, keyword_init: true)

    class Registry
      PROJECT_ROOT = File.expand_path('../../..', __dir__)
      ENTRIES = {
        '002' => { name: 'Process Lifecycle', kind: 'process', path: 'labs/002-process-lifecycle/worker.rb' },
        '003' => { name: 'IPC Pipes', kind: 'ipc', path: 'labs/003-ipc-pipes/worker.rb' }
      }.freeze

      def self.list(kind: nil)
        ENTRIES.filter_map do |id, entry|
          next if kind && entry[:kind] != kind
          { id: id, name: entry[:name], kind: entry[:kind] }
        end
      end

      def self.fetch(id, kind: nil)
        data = ENTRIES.fetch(id.to_s) { raise ArgumentError, 'tarefa não cadastrada' }
        raise ArgumentError, 'tarefa incompatível com este comando' if kind && data[:kind] != kind
        Task.new(id: id.to_s, name: data[:name], kind: data[:kind],
                 script: File.join(PROJECT_ROOT, data[:path]))
      end
    end
  end
end
