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
  { id: "pc-manutencao", category: "assistencia", title: "Manutenção preventiva", description: "Revisão básica de saúde do sistema, atualizações e recomendações de backup.", price: 119, icon: "✚" },
  { id: "auto-planilha", category: "automacao", title: "Automação de planilhas", description: "Reduza trabalho repetitivo com fórmulas, scripts e rotinas de organização de dados.", price: 129, tag: "Popular", icon: "▦" },
  { id: "auto-script", category: "automacao", title: "Script personalizado", description: "Pequenas rotinas em Python, Shell ou JavaScript com objetivo e escopo definidos.", price: 149, icon: "⌨" },
  { id: "auto-bot", category: "automacao", title: "Bot para Discord", description: "Bot sob medida para comandos, avisos e rotinas de comunidades ou equipes.", price: 199, icon: "◇" },
  { id: "auto-integracao", category: "automacao", title: "Integração entre sistemas", description: "Conexão simples entre APIs e ferramentas para evitar cópia manual de informações.", price: 249, icon: "⤳" },
  { id: "web-ajuste", category: "web", title: "Correção rápida de site", description: "Ajustes visuais, responsividade, formulários ou pequenos bugs em páginas existentes.", price: 89, tag: "Entrada rápida", icon: "✦" },
  { id: "web-landing", category: "web", title: "Landing page profissional", description: "Página de apresentação com design responsivo, conteúdo fornecido e botão de contato.", price: 399, icon: "▤" },
  { id: "web-hospedagem", category: "web", title: "Configuração de hospedagem", description: "Domínio, DNS, publicação inicial e HTTPS em provedores compatíveis.", price: 149, icon: "☁" },
  { id: "web-manutencao", category: "web", title: "Cuidados mensais com site", description: "Pequena janela mensal de manutenção e verificação, com limites combinados.", price: 79, period: "mês", icon: "↻" },
  { id: "sec-check", category: "seguranca", title: "Check-up de segurança digital", description: "Revisão orientada de senhas, MFA, backups e exposição básica do seu ambiente.", price: 129, tag: "Preventivo", icon: "⛨" },
  { id: "sec-hardening", category: "seguranca", title: "Hardening de sistema", description: "Melhorias de configuração de Windows ou Linux com autorização e escopo definidos.", price: 179, icon: "⬡" },
  { id: "sec-site", category: "seguranca", title: "Revisão de segurança de site", description: "Avaliação autorizada de configurações e riscos comuns, com recomendações práticas.", price: 249, icon: "◉" },
  { id: "sec-monitor", category: "seguranca", title: "Monitoramento básico de site", description: "Acompanhamento de disponibilidade e vencimento de certificado, com alertas definidos.", price: 89, period: "mês", icon: "◎" }
]);
