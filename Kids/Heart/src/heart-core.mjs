// Heart Kids Core: deterministic, no model calls, no memory, no tools.
export const STARTERS = [
  { label: "Missão de lógica 🧩", prompt: "Quero um desafio de lógica" },
  { label: "Robôs 🤖", prompt: "Como funciona um robô?" },
  { label: "Senhas seguras 🔒", prompt: "Como criar uma senha segura?" }
];
const option = (label, prompt) => ({ label, prompt });
const result = (reply, options = STARTERS, category = "learning") => ({
  reply, options, category, bot: "Heart", mode: "guided"
});
const normalized = (v) => v.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
export function answer(message) {
  if (typeof message !== "string" || !message.trim() || message.length > 220) {
    return result("Vamos usar uma pergunta curtinha, com até 220 letras? 🐾", STARTERS, "limit");
  }
  const m = normalized(message.trim());
  // Avoid taking, reflecting, or persisting personal data.
  if (/[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/i.test(message) ||
      /(?:\+?\d[\d\s().-]{7,}\d)/.test(message) ||
      /\b(meu (nome completo|endereco|telefone|cpf|rg|cep)|minha (escola|rua|senha)|onde eu moro|meu whatsapp)\b/.test(m)) {
    return result("Sua privacidade é importante! 💙 Não compartilhe nome completo, telefone, endereço, escola ou senhas aqui. Vamos escolher uma aventura?", STARTERS, "privacy");
  }
  if (/\b(quero morrer|me matar|me machucar|suicid|abuso|assedi|me bate|me machucou|me ameac|violencia em casa|estou em perigo|alguem me feriu)\b/.test(m)) {
    return result("Sinto muito que algo difícil esteja acontecendo. 💙 Conte agora a um adulto de confiança que possa ajudar você. Se estiver em perigo imediato, peça ajuda a alguém por perto ou aos serviços de emergência da sua região.", [], "safety");
  }
  if (/\b(encontrar voce|te visitar|seu endereco|mandar foto|foto minha|guardar segredo|so voce me entende|nao conte pra ninguem)\b/.test(m)) {
    return result("Eu sou um personagem virtual, não uma pessoa. 🐺 Não guardamos segredos que possam colocar você em risco. Para assuntos pessoais, converse com um adulto de confiança.", STARTERS, "boundaries");
  }
  if (/\b(bomba|fabricar arma|machucar alguem|roubar|invadir conta|roubar senha|criar virus|malware|pornografia)\b/.test(m)) {
    return result("Esse assunto não é uma missão segura para crianças. Podemos aprender a proteger computadores e pessoas, ou tentar um desafio de lógica! 🛡️", [option("Senhas seguras 🔒", "Como criar uma senha segura?"), STARTERS[0]], "safety");
  }
  if (/\b(triste|sozinh|ansios|medo|chatead|ninguem gosta|estou chorando)\b/.test(m)) {
    return result("Sinto muito que você esteja passando por isso. 💙 Seus sentimentos importam. Que tal contar a um adulto de confiança o que está acontecendo? Se quiser, também podemos fazer uma missão tranquila.", [STARTERS[0]], "wellbeing");
  }
  const logicAnswer = m.match(/^resposta da missao de logica:\s*([abc])$/);
  if (logicAnswer) {
    return logicAnswer[1] === "b" ?
      result("Acertou! 🎉 O comando REPITA ajuda o robô a executar a mesma ação várias vezes. Quer outra aventura?", STARTERS, "quiz") :
      result("Boa tentativa! 🧩 A dica é procurar a opção que repete o mesmo movimento 3 vezes. Tente de novo!", [
        option("Tentar A", "Resposta da missão de lógica: A"),
        option("Tentar B", "Resposta da missão de lógica: B"),
        option("Tentar C", "Resposta da missão de lógica: C")
      ], "quiz");
  }
  const mathAnswer = m.match(/^resposta da missao de matematica:\s*([abc])$/);
  if (mathAnswer) {
    return mathAnswer[1] === "b" ?
      result("Isso! 2 + 3 = 5 ⭐ A matemática também ajuda a programar robôs!", STARTERS, "quiz") :
      result("Quase! Conte duas estrelinhas e depois mais três. Quantas há no total?", [
        option("A: 4", "Resposta da missão de matemática: A"),
        option("B: 5", "Resposta da missão de matemática: B"),
        option("C: 6", "Resposta da missão de matemática: C")
      ], "quiz");
  }
  if (/\b(desafio|missao|quiz|logica|algoritmo|programac|codigo|repetic|loop|se e senao|if)\b/.test(m)) {
    return result("Missão de lógica! 🐾 Um robô precisa dar 3 passos. Qual comando resolve melhor?\nA) PULE\nB) REPITA 3 VEZES: ANDE\nC) DESLIGUE", [
      option("A: pule", "Resposta da missão de lógica: A"),
      option("B: repita", "Resposta da missão de lógica: B"),
      option("C: desligue", "Resposta da missão de lógica: C")
    ], "quiz");
  }
  if (/\b(matematica|somar|conta|numeros|adi[cç]ao)\b/.test(m)) {
    return result("Missão das estrelas ⭐ Se temos 2 estrelas e encontramos mais 3, quantas são ao todo?", [
      option("A: 4", "Resposta da missão de matemática: A"),
      option("B: 5", "Resposta da missão de matemática: B"),
      option("C: 6", "Resposta da missão de matemática: C")
    ], "quiz");
  }
  if (/\b(robo|robotica|eletronica|sensor|arduino)\b/.test(m)) {
    return result("Um robô combina peças, sensores e instruções. 🤖 O sensor percebe algo, e o programa decide o que fazer. Por exemplo: SE estiver escuro, ENTÃO acenda uma luz!", [
      option("Desafio de lógica 🧩", "Quero um desafio de lógica"),
      option("Aprender matemática ⭐", "Quero uma missão de matemática")
    ], "robotics");
  }
  if (/\b(senha|internet|seguranca|privacidade|hacker|hackear)\b/.test(m)) {
    return result("Na internet, proteja seus segredos! 🔒 Use senhas longas, nunca compartilhe códigos e peça ajuda a um adulto antes de abrir links desconhecidos. Hacking ético começa com permissão e respeito.", [
      option("Desafio de lógica 🧩", "Quero um desafio de lógica"),
      option("Conhecer robôs 🤖", "Como funciona um robô?")
    ], "security");
  }
  if (/\b(planeta|espaco|estrela|sol|lua|astronomia|ciencia)\b/.test(m)) {
    return result("A ciência é cheia de perguntas incríveis! 🌌 A Terra é um planeta que gira em torno do Sol. Quer usar matemática para contar estrelas?", [
      option("Contar estrelas ⭐", "Quero uma missão de matemática"), STARTERS[0]
    ], "science");
  }
  if (/\b(quem e voce|voce e humano|voce e real|como se chama)\b/.test(m)) {
    return result("Eu sou o Heart, um lobinho virtual da Workshop Kids! 🐺 Sou um programa com respostas educativas, não sou humano nem sei tudo. Vamos aprender juntos?", STARTERS, "identity");
  }
  if (/\b(oi|ola|bom dia|boa tarde|boa noite|auuu|hello)\b/.test(m)) {
    return result("Auuuu! 🐺💙 Eu sou o Heart, seu guia de aventuras tecnológicas! Escolha uma missão para começar.", STARTERS, "hello");
  }
  return result("Que pergunta interessante! 🐺 Ainda estou aprendendo a guiar aventuras sobre alguns assuntos. Podemos explorar lógica, robótica, matemática, ciência ou segurança na internet.", STARTERS, "fallback");
}
