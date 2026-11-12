const form = document.querySelector("#chat");
const input = document.querySelector("#message");
const messages = document.querySelector("#messages");
const suggestions = document.querySelector("#suggestions");
const send = document.querySelector("#send");
const starterOptions = [
  { label: "Missão de lógica 🧩", prompt: "Quero um desafio de lógica" },
  { label: "Robôs 🤖", prompt: "Como funciona um robô?" },
  { label: "Senhas seguras 🔒", prompt: "Como criar uma senha segura?" }
];
function addMessage(text, who) {
  const p = document.createElement("p");
  p.className = "bubble " + who;
  p.textContent = text;
  messages.appendChild(p);
  messages.scrollTop = messages.scrollHeight;
}
function showChoices(choices) {
  suggestions.replaceChildren();
  (Array.isArray(choices) ? choices : []).slice(0, 3).forEach((choice) => {
    if (!choice || typeof choice.label !== "string" || typeof choice.prompt !== "string") return;
    const button = document.createElement("button");
    button.className = "suggestion";
    button.type = "button";
    button.textContent = choice.label.slice(0, 70);
    button.addEventListener("click", () => sendMessage(choice.prompt));
    suggestions.appendChild(button);
  });
}
async function sendMessage(message) {
  if (!message || message.length > 220 || send.disabled) return;
  addMessage(message, "visitor");
  input.value = "";
  send.disabled = true;
  suggestions.replaceChildren();
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "omit",
      cache: "no-store",
      body: JSON.stringify({ message })
    });
    if (!res.ok) throw new Error("Falha na resposta");
    const data = await res.json();
    addMessage(String(data.reply || "Vamos tentar outra pergunta?"), "bot");
    showChoices(data.options);
  } catch {
    addMessage("Opa! 🐾 Não consegui responder agora. Peça ajuda a um adulto e tente novamente.", "bot");
    showChoices(starterOptions);
  } finally {
    send.disabled = false;
    input.focus();
  }
}
form.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage(input.value.trim());
});
showChoices(starterOptions);
