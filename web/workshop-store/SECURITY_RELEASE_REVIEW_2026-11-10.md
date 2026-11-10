# The Workshop Store v0.1 — Segurança e Release Gate

**Data de revisão:** 2026-11-10 (America/Sao_Paulo)  
**Escopo:** `web/workshop-store/` e Worker independente `workshop-store-preview`  
**Baseline:** `docs/SECURITY_RELEASE_GATE.md`  
**Revisor:** revisão automatizada assistida, pendente de aceite do proprietário comercial.

## Resultado e decisão

**DECISÃO: CONDITIONAL APPROVAL — SOMENTE PREVIEW.**
A loja pode continuar acessível como prévia de homologação. **O lançamento comercial definitivo, o merge e links no hub ficam BLOQUEADOS** até resolver as pendências comerciais e realizar aceite visual/operacional em dispositivo real.

**Ambiente:** https://workshop-store-preview.wolfpackworkshop.workers.dev/

## Checklist principal

| Item | Estado | Evidência / observação |
| --- | --- | --- |
| Diff e escopo isolados | PASS | Apenas `web/workshop-store` + CI; sem alteração dos Apps Labs, Kids ou CTF. |
| Build estático reproduzível | PASS | `node web/workshop-store/build.mjs`, validação do Worker em CI. |
| Testes automatizados | PASS | `node --test web/workshop-store/tests/*.test.mjs`; suíte cobre catálogo, links WhatsApp, GET/HEAD, 404/405, MIME, CSP, cache, caminhos herdados e não reflexão. |
| Entrada não confiável | PASS (escopo atual) | Busca é tratada com `textContent`, não `innerHTML`; catálogo controlado por código; WhatsApp via `URLSearchParams` e telefone validado por allowlist. |
| Rotas não cadastradas | PASS | Correção `Object.hasOwn(FILES, url.pathname)` impede aceitar chaves de `Object.prototype` como rotas. |
| Métodos permitidos | PASS (CI) | Somente GET/HEAD; POST retorna 405 com `Allow`; testes sobre Worker montado. |
| Segurança HTTP (externa) | PASS (rotas verificadas) | Browser Rendering da Cloudflare confirmou GET 200, CSP, HSTS, Referrer-Policy, no-sniff e X-Frame-Options na home; checagem posterior confirmou COOP e `X-Robots-Tag` na página de privacidade. |
| Prevenção de clickjacking | PASS | `frame-ancestors 'none'`, `X-Frame-Options: DENY`. |
| XSS / injeção de conteúdo | PASS (código e testes limitados) | CSP sem scripts inline, sem reflexão de query, HTML dinâmico via `textContent`; não substitui teste de invasão. |
| Dependências JS em produção | PASS | Sem dependências de terceiros carregadas pela loja. Worker usa apenas APIs Web nativas. |
| Secrets / tokens públicos | PASS (inspeção de fonte) | Nenhum segredo necessário. Número do WhatsApp é intencionalmente público; nenhuma credencial privada deve ser inserida na configuração. |
| Dados pessoais | MITIGADO | Sem checkout/cadastro, porém Cloudflare pode processar dados técnicos; aviso de privacidade ajustado para não afirmar ausência total de tratamento. |
| Segurança do WhatsApp | PASS (código) | `wa.me` fixo, parâmetros de mensagem codificados; `target=_blank` usa `rel=noopener noreferrer`. Envio depende de ação do usuário. |
| Isolamento de preview | PASS | Worker próprio, subdomínio independente e `X-Robots-Tag: noindex, nofollow, noarchive` no preview. |
| Visual desktop e mobile | PASS (verificação de primeira dobra) | Capturas visuais obtidas com Browser Rendering em 1366×900 e 390×844. Layout consistente, botões e textos legíveis. |
| Testes reais de navegação/clique em celular | PENDENTE | Requer QA humano da jornada completa de seleção e abertura do WhatsApp em dispositivo real. |
| Fornecedor e oferta em conformidade com regras de consumo | BLOQUEADOR | Identificação pública do fornecedor, canais de contato, condições de execução/pagamento/cancelamento e preços adicionais precisam de revisão antes do lançamento. |
| Preços e capacidade de atendimento | BLOQUEADOR | R$49–399 iniciais e R$79/89 por mês devem ser aceitos pelo responsável; avaliar custos, escopo, SLA e limites de suporte. |
| ASan/UBSan | N/A | Site estático JS/HTML/CSS, nenhum binário C produzido neste módulo. |
| Teste externo de 404/405/HEAD | NÃO VERIFICADO | Verificado na suíte do Worker; validação HTTP externa desses cenários ainda não concluída. |
| Portas abertas / filesystem local | N/A | Worker sem disco, sem shell, sem endpoints locais expostos. |
| Logs / observabilidade | OBSERVAÇÃO | O Cloudflare pode emitir métricas/logs técnicos da infraestrutura; revisão de retenção/permissões e WAF deve fazer parte da operação. |

## Evidências

- PR: https://github.com/kingmaker-lab/The-Workshop./pull/39
- CI: workflow `Workshop Store - validacao da vitrine`; sintaxe, build e testes executados com sucesso para revisão do código.
- Deploy Cloudflare Worker: versão `c37f8685-13bd-43a5-a9b3-d2d3722c7b20` publicada às 13:46:51 UTC, 100% do tráfego da prévia.
- Browser Rendering da Cloudflare em 2026-11-10: `/` → HTTP 200, título `The Workshop Store | Tecnologia que resolve`, catálogo carregado, novos títulos e link para a política de privacidade. `/privacidade.html` → HTTP 200 e `X-Robots-Tag` no preview.

## Modelo de ameaças resumido

**Ativos:** integridade da vitrine, telefone comercial, reputação, dados voluntariamente informados no WhatsApp.  
**Superfície pública:** HTTP GET/HEAD de arquivos estáticos via Workers; links externos (WhatsApp, Labs, GitHub).  
**Não existe:** conta, sessão, cookie da aplicação, formulário de upload, banco de pedidos, gateway financeiro, endpoint de escrita.  
**Ameaças prioritárias:** XSS/alteração de conteúdo por commit indevido, dependências de CI, arquivos/rotas inesperadas, desinformação comercial, phishing com cópia visual do site, abuso de contato público.  
**Controles:** PR, CI, CSP, allowlist de rotas, sem reflexão dinâmica, headers e independência da infraestrutura.

## Pendências para aprovar produção

- [ ] Validar preços de referência, tempo máximo por tarefa, exclusões, custos de domínio/peças/deslocamento e limitação de contratos recorrentes.
- [ ] Informar e publicar os dados e condições do fornecedor aplicáveis à oferta ao consumidor, evitando expor CPF/endereço residencial sem decisão consciente.
- [ ] Revisar política de tratamento e guarda de conversas recebidas via WhatsApp, finalidade e eventual retenção.
- [ ] Testar manualmente em Android/iOS: catálogo, filtros, seleção múltipla, mensagem WhatsApp, teclado e links.
- [ ] Revisar controles da conta Cloudflare/GitHub: MFA, privilégios mínimos, proteção de branch, auditoria de alterações e regras WAF/rate-limit conforme riscos.
- [ ] Confirmar GET/HEAD/404/405 com HTTP externo na versão final, após deploy.
- [ ] Registrar aceite explícito para merge/produção e depois adicionar links no hub.

**Revisão necessária para cada versão futura**, inclusive alterações de preço, telefone, headers ou rotas. Nenhuma marcação PASS significa produto isento de risco.
