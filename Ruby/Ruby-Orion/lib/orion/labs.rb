# frozen_string_literal: true
module Orion
  module Labs
    module_function

    def entries
      [
        { id: "001", title: "Modelo de objetos Ruby", pillar: "Alnitak / Learn", status: "available", path: "labs/001-object-model" },
        { id: "002", title: "Processos e IPC", pillar: "Alnilam / Build", status: "planned", path: nil },
        { id: "003", title: "Sockets TCP", pillar: "Mintaka / Explore", status: "planned", path: nil }
      ]
    end
  end
end
