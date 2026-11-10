export const CATEGORIES = Object.freeze([
  { id: "all", label: "Todos" },
  { id: "assistencia", label: "Assistência técnica" },
  { id: "automacao", label: "Automação" },
  { id: "web", label: "Sites & sistemas" },
  { id: "seguranca", label: "Segurança digital" }
]);

export const SERVICES = Object.freeze([
  { id: "pc-diagnostico", category: "assistencia", title: "Diagnóstico remoto", description: "Avaliação inicial de lentidão, erros, falhas de software e orientações sobre próximos passos.", price: 49, tag: "Comece aqui", icon: "⌘" },
  { id: "pc-otimizacao", category: "assistencia", title: "Otimização do computador", description: "Revisão de inicialização, programas, espaço em disco e ajustes de desempenho de software.", price: 89, icon: "⚙" },
  { id: "pc-config", category: "assistencia", title: "Instalação e configuração", description: "Configuração de programas, periféricos e ferramentas de produtividade compatíveis.", price: 69, icon: "◈" },
  { id: "pc-manutencao", category: "assistencia", title: "Manutenção preventiva de software", description: "Revisão de sistema, atualizações e orientações de backup. Não inclui peças nem serviço presencial.", price: 119, icon: "✚" },
  { id: "auto-planilha", category: "automacao", title: "Automação básica de planilhas", description: "Automatize uma rotina simples com fórmulas ou scripts em planilha existente.", price: 129, tag: "Popular", icon: "▦" },
  { id: "auto-script", category: "automacao", title: "Script simples personalizado", description: "Uma rotina pequena em Python, Shell ou JavaScript, com escopo e entregáveis combinados.", price: 149, icon: "⌨" },
  { id: "auto-bot", category: "automacao", title: "Bot básico para Discord", description: "Configuração inicial de comandos ou avisos. Hospedagem e manutenção contínua à parte.", price: 199, icon: "◇" },
  { id: "auto-integracao", category: "automacao", title: "Integração entre sistemas", description: "Conexão simples entre APIs e ferramentas para evitar cópia manual de informações.", price: 249, icon: "⤳" },
  { id: "web-ajuste", category: "web", title: "Correção pontual de site", description: "Um ajuste visual ou correção simples em página existente, após análise do problema.", price: 89, tag: "Entrada rápida", icon: "✦" },
  { id: "web-landing", category: "web", title: "Landing page essencial", description: "Página responsiva de apresentação com conteúdo fornecido e contato. Domínio à parte.", price: 399, icon: "▤" },
  { id: "web-hospedagem", category: "web", title: "Configuração de hospedagem", description: "Publicação inicial, DNS e HTTPS. Domínio, planos do provedor e renovações são cobrados à parte.", price: 149, icon: "☁" },
  { id: "web-manutencao", category: "web", title: "Cuidados mensais com site", description: "Verificações e pequenas manutenções dentro de franquia mensal contratada. Sem suporte ilimitado.", price: 79, period: "mês", icon: "↻" },
  { id: "sec-check", category: "seguranca", title: "Check-up de segurança digital", description: "Revisão orientada de senhas, MFA, backups e exposição básica do seu ambiente.", price: 129, tag: "Preventivo", icon: "⛨" },
  { id: "sec-hardening", category: "seguranca", title: "Hardening básico de sistema", description: "Revisão inicial de configurações de Windows ou Linux, com autorização e escopo definidos.", price: 179, icon: "⬡" },
  { id: "sec-site", category: "seguranca", title: "Revisão básica de segurança web", description: "Checagem autorizada de configurações comuns e recomendações. Não equivale a pentest completo.", price: 249, icon: "◉" },
  { id: "sec-monitor", category: "seguranca", title: "Monitoramento básico de site", description: "Alertas de indisponibilidade e certificado, conforme escopo. Sem SLA de resposta imediata.", price: 89, period: "mês", icon: "◎" }
]);
