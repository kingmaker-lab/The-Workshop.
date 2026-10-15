// Gerado de source/vulpes77/lib/vulpes77.rb por export_vulpes.rb
export const DATA = {
  "version": "0.1.0",
  "network": {
    "10.77.0.1": {
      "name": "GATEWAY",
      "ports": {
        "443": "edge-dashboard",
        "53": "dns-snapshot"
      }
    },
    "10.77.0.12": {
      "name": "WEB-01",
      "ports": {
        "80": "public-site",
        "8080": "telemetry-console"
      }
    },
    "10.77.0.23": {
      "name": "LOG-01",
      "ports": {
        "9200": "log-archive"
      }
    },
    "10.77.0.44": {
      "name": "SEC-CTRL",
      "ports": {
        "8443": "response-console"
      }
    }
  },
  "port_order": {
    "10.77.0.1": [
      443,
      53
    ],
    "10.77.0.12": [
      80,
      8080
    ],
    "10.77.0.23": [
      9200
    ],
    "10.77.0.44": [
      8443
    ]
  },
  "files": {
    "10.77.0.1:443": {
      "welcome.txt": "[EDGE] Gateway de treinamento. Nenhuma conexão externa é realizada.\nAtivos: WEB-01, LOG-01, SEC-CTRL.\n"
    },
    "10.77.0.1:53": {
      "zones.txt": "web-01.lab 10.77.0.12\nlog-01.lab 10.77.0.23\nsec-ctrl.lab 10.77.0.44\n"
    },
    "10.77.0.12:80": {
      "index.html": "<h1>NEXUS LAB</h1>\n<!-- O servidor de telemetria responde em :8080 -->\n"
    },
    "10.77.0.12:8080": {
      "readme.txt": "WEB-01 / telemetria\nO identificador de uma transmissão suspeita está codificado em Base64.\nUse 'cat traffic.log' e 'decode b64 <valor>'.\n",
      "traffic.log": "02:13:52 GET /health code=200\n02:14:07 POST /telemetry destination=203.0.113.7 beacon_id_b64=TklHSFRKQVI= code=202\n02:14:09 GET /health code=200\n",
      "notes.txt": "203.0.113.0/24 é um bloco reservado para documentação.\nEsta telemetria, assim como os hosts, é completamente fictícia.\n"
    },
    "10.77.0.23:9200": {
      "readme.txt": "[IR] Alerta: WEB-01 apresentou egress suspeito às 02:14:07.\nCorrelacione o event_id de egress.log com auth.log.\nEnvie o nome da conta responsável, não o ID.\n",
      "auth.log": "02:13:43 user=ana src=10.77.0.81 event_id=E-105 result=ok\n02:13:59 user=svc-bridge src=10.77.0.99 event_id=E-441 result=ok\n02:14:01 user=svc-backup src=10.77.0.71 event_id=E-883 result=ok\n",
      "egress.log": "02:14:07 host=WEB-01 destination=203.0.113.7 event_id=E-441 verdict=alert\n02:17:22 host=GATEWAY destination=198.51.100.3 event_id=E-883 verdict=allow\n"
    },
    "10.77.0.44:8443": {
      "runbook.txt": "RUNBOOK DE RESPOSTA - NEXUS LAB\n1. Identifique o host impactado em incident.json.\n2. Isole apenas o host comprometido: contain <IP>.\n3. Registre o ticket: submit <ticket>.\nA quarentena é somente uma mudança no estado deste jogo.\n",
      "incident.json": "{\n  \"ticket\": \"IR-2607\",\n  \"severity\": \"high\",\n  \"host\": \"10.77.0.12\",\n  \"actor\": \"svc-bridge\",\n  \"required_action\": \"isolate_host\"\n}",
      "dashboard.txt": "SEGMENTO NEXUS\nWEB-01: incidente aberto\nLOG-01: preservado para análise\nGATEWAY: operação normal\n"
    }
  },
  "missions": [
    {
      "title": "01 / O ECO FANTASMA",
      "lead": "Uma transmissão inesperada saiu do servidor WEB-01.\\nEncontre o identificador secreto do beacon sem sair da rede simulada.",
      "target": "Localizar e decodificar o beacon_id; enviar o codinome.",
      "hint": "scan 10.77.0.12 -> connect 10.77.0.12:8080 -> cat traffic.log -> decode b64 <token>",
      "answer": "NIGHTJAR",
      "unlock": [
        "10.77.0.1",
        "10.77.0.12"
      ],
      "outro": "Beacon identificado! Agora precisamos atribuir a atividade a uma identidade."
    },
    {
      "title": "02 / SOMBRAS NOS LOGS",
      "lead": "A equipe SOC recuperou dois arquivos de eventos.\\nCorrelacione a transmissão suspeita com a autenticação que a precedeu.",
      "target": "Encontrar a conta relacionada ao evento suspeito e enviar o nome da conta.",
      "hint": "scan 10.77.0.23 -> connect 10.77.0.23:9200 -> cat egress.log -> grep E-441 auth.log",
      "answer": "svc-bridge",
      "unlock": [
        "10.77.0.1",
        "10.77.0.12",
        "10.77.0.23"
      ],
      "outro": "A identidade foi correlacionada. Um último passo: contenção responsável."
    },
    {
      "title": "03 / SILÊNCIO OPERACIONAL",
      "lead": "O atacante ainda pode estar ativo no host comprometido.\\nLeia o runbook e isole somente a máquina afetada.\\nDepois registre o ticket de incidente.",
      "target": "Conter o host correto e submeter o ID do ticket.",
      "hint": "scan 10.77.0.44 -> connect 10.77.0.44:8443 -> cat incident.json -> contain 10.77.0.12 -> submit IR-2607",
      "answer": "IR-2607",
      "unlock": [
        "10.77.0.1",
        "10.77.0.12",
        "10.77.0.23",
        "10.77.0.44"
      ],
      "outro": "INCIDENTE CONTIDO. A rede NEXUS está novamente sob controle."
    }
  ]
};
