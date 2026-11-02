/** Discord application commands. Use in the guild only; no DM or privileged intents. */
export const commands = [
  { name: 'heart', type: 1, description: '🐾 Aprenda ciência, código e robótica com Heart', contexts: [0], integration_types: [0], options: [
    { name: 'pergunta', description: 'Sua dúvida de tecnologia (até 240 caracteres)', type: 3, required: true, min_length: 2, max_length: 240 },
  ] },
  { name: 'blade', type: 1, description: '🛡️ Conselhos de navegação segura de Blade', contexts: [0], integration_types: [0], options: [
    { name: 'assunto', description: 'Escolha um tema de segurança digital', type: 3, required: true, choices: [
      { name: 'Senhas e autenticação', value: 'senha' }, { name: 'Golpes e links', value: 'golpe' },
      { name: 'Privacidade', value: 'privacidade' }, { name: 'Respeito e proteção', value: 'respeito' },
    ] },
  ] },
  { name: 'ghost', type: 1, description: '👻 Resolva um desafio de lógica com Gh0st', contexts: [0], integration_types: [0], options: [
    { name: 'codigo', description: 'Escolha o desafio', type: 3, required: true, choices: [
      { name: '1. Portão lógico', value: '1' }, { name: '2. ROT13', value: '2' }, { name: '3. Laço', value: '3' },
    ] },
    { name: 'resposta', description: 'Opcional: envie uma resposta para verificar', type: 3, required: false, max_length: 100 },
  ] },
  { name: 'workshop', type: 1, description: '🐺 Conheça os bots da The Workshop', contexts: [0], integration_types: [0] },
];
