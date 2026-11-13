import { CATEGORIES, SERVICES } from "./catalog.mjs";
import { formatBRL, normalizePhone, whatsappUrl } from "./whatsapp.mjs";

const config = window.WORKSHOP_STORE || {};
const phone = normalizePhone(config.whatsapp);
const byId = new Map(SERVICES.map((service) => [service.id, service]));
const state = { category: "all", query: "", selected: new Set() };
const $ = (id) => document.getElementById(id);

function element(tag, className, textValue) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (textValue !== undefined) node.textContent = textValue;
  return node;
}
function comparable(value) {
  return String(value).toLocaleLowerCase("pt-BR").normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}
function contactAnchor(anchor, items) {
  const href = whatsappUrl(phone, items);
  if (!href) {
    anchor.removeAttribute("href");
    anchor.setAttribute("aria-disabled", "true");
    anchor.removeAttribute("target");
    anchor.removeAttribute("rel");
    anchor.title = "Contato via WhatsApp em configuração.";
    return;
  }
  anchor.href = href;
  anchor.target = "_blank";
  anchor.rel = "noopener noreferrer";
  anchor.removeAttribute("aria-disabled");
  anchor.removeAttribute("title");
}
function chosenServices() {
  return [...state.selected].map((id) => byId.get(id)).filter(Boolean);
}

function renderFilters() {
  const root = $("filtros");
  root.replaceChildren();
  for (const category of CATEGORIES) {
    const button = element("button", "filter", category.label);
    button.type = "button";
    button.setAttribute("aria-pressed", String(state.category === category.id));
    button.addEventListener("click", () => {
      state.category = category.id;
      renderFilters();
      renderCatalog();
    });
    root.append(button);
  }
}

function renderCatalog() {
  const root = $("grade");
  root.replaceChildren();
  const results = SERVICES.filter((service) => {
    if (state.category !== "all" && state.category !== service.category) return false;
    const label = CATEGORIES.find((category) => category.id === service.category)?.label || "";
    return comparable(service.title + " " + service.description + " " + label).includes(comparable(state.query));
  });
  $("resultado").textContent = results.length + (results.length === 1 ? " SERVIÇO DISPONÍVEL" : " SERVIÇOS DISPONÍVEIS");
  $("sem-resultados").hidden = results.length > 0;
  const fragment = document.createDocumentFragment();
  for (const service of results) {
    const category = CATEGORIES.find((item) => item.id === service.category);
    const card = element("article", "card");
    const head = element("div", "card-head");
    const icon = element("span", "card-icon", service.icon);
    icon.setAttribute("aria-hidden", "true");
    head.append(icon);
    if (service.tag) head.append(element("span", "card-tag", service.tag));
    const categoryLabel = element("span", "card-category", category?.label || "");
    const title = element("h3", "", service.title);
    const description = element("p", "card-desc", service.description);
    const footer = element("div", "card-footer");
    const priceGroup = element("div");
    priceGroup.append(element("span", "price-label", "A PARTIR DE"));
    const price = element("strong", "price", formatBRL(service.price));
    if (service.period) price.append(element("small", "", " /" + service.period));
    priceGroup.append(price);
    const actions = element("div", "card-actions");
    const add = element("button", "add", state.selected.has(service.id) ? "✓ Selecionado" : "+ Adicionar");
    add.type = "button";
    add.setAttribute("aria-pressed", String(state.selected.has(service.id)));
    add.setAttribute("aria-label", (state.selected.has(service.id) ? "Remover " : "Adicionar ") + service.title + (state.selected.has(service.id) ? " do pedido" : " ao pedido"));
    add.addEventListener("click", () => {
      if (state.selected.has(service.id)) state.selected.delete(service.id);
      else state.selected.add(service.id);
      renderCatalog();
      renderCart();
    });
    const direct = element("a", "direct", "Orçar no WhatsApp ↗");
    contactAnchor(direct, [service]);
    actions.append(add, direct);
    footer.append(priceGroup, actions);
    card.append(head, categoryLabel, title, description, footer);
    fragment.append(card);
  }
  root.append(fragment);
}
function renderCart() {
  const selected = chosenServices();
  $("cart-count").textContent = String(selected.length);
  const list = $("itens");
  list.replaceChildren();
  if (!selected.length) list.append(element("li", "empty", "Nenhum serviço selecionado. Comece pelo catálogo."));
  for (const service of selected) {
    const li = element("li");
    li.append(element("span", "", service.title));
    const remove = element("button", "", "×");
    remove.type = "button";
    remove.setAttribute("aria-label", "Remover " + service.title);
    remove.addEventListener("click", () => {
      state.selected.delete(service.id);
      renderCatalog();
      renderCart();
    });
    li.append(remove);
    list.append(li);
  }
  const fixed = selected.filter((x) => !x.period).reduce((sum, x) => sum + x.price, 0);
  const monthly = selected.filter((x) => x.period).reduce((sum, x) => sum + x.price, 0);
  $("total").textContent = formatBRL(fixed) + (monthly ? " + " + formatBRL(monthly) + "/mês" : "");
  $("limpar-pedido").disabled = selected.length === 0;
  const checkout = $("enviar-pedido");
  contactAnchor(checkout, selected);
  checkout.textContent = selected.length ? "Solicitar orçamento ↗" : "Pedir atendimento ↗";
  $("estado-contato").textContent = phone
    ? "A conversa será aberta no WhatsApp. Nenhum pagamento é realizado aqui."
    : "Contato via WhatsApp em configuração. Atendimento ainda não disponível por este site.";
}
function init() {
  renderFilters();
  renderCatalog();
  renderCart();
  $("busca").addEventListener("input", (event) => {
    state.query = event.target.value.trim();
    renderCatalog();
  });
  $("limpar-pedido").addEventListener("click", () => {
    state.selected.clear();
    renderCatalog();
    renderCart();
  });
  $("cart-toggle").addEventListener("click", () => {
    $("resumo").scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
  });
  $("ano").textContent = String(new Date().getFullYear());
  for (const id of ["whatsapp-hero", "contato-geral"]) contactAnchor($(id), []);
}
init();
