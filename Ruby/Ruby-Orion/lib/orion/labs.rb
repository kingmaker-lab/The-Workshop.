# frozen_string_literal: true
module Orion
  module Labs
    module_function

    def entries
      [
        { id: '001', title: 'Modelo de objetos Ruby', pillar: 'Alnitak / Learn', status: 'available', path: 'labs/001-object-model' },
        { id: '002', title: 'Ciclo de vida dos processos', pillar: 'Alnilam / Build', status: 'available', path: 'labs/002-process-lifecycle' },
        { id: '003', title: 'Comunicação IPC com pipes', pillar: 'Alnilam / Build', status: 'available', path: 'labs/003-ipc-pipes' },
        { id: '004', title: 'Sockets TCP e protocolos', pillar: 'Mintaka / Explore', status: 'planned', path: nil }
      ]
    end
  end
end
