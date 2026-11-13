export function normalizePhone(value) {
  const digits = String(value ?? "").replace(/\D/g, "");
  return /^55\d{10,11}$/.test(digits) ? digits : null;
}
export function formatBRL(value) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(value);
}
export function buildWhatsAppMessage(services) {
  const items = Array.isArray(services) ? services : [];
  const lines = [
    "Olá! Vim pela The Workshop Store e gostaria de solicitar um orçamento.",
    "",
    "Serviços de interesse:"
  ];
  if (items.length) {
    for (const item of items) {
      lines.push("• " + item.title + " (a partir de " + formatBRL(item.price) + (item.period ? "/" + item.period : "") + ")");
    }
  } else {
    lines.push("• Atendimento ou projeto personalizado.");
  }
  lines.push("", "Podemos conversar sobre o escopo, o prazo e os valores finais?", "Entendo que os preços apresentados são estimativas iniciais.");
  return lines.join(String.fromCharCode(10));
}
export function whatsappUrl(rawPhone, services) {
  const phone = normalizePhone(rawPhone);
  if (!phone) return null;
  const url = new URL("https://wa.me/" + phone);
  url.searchParams.set("text", buildWhatsAppMessage(services));
  return url.toString();
}
