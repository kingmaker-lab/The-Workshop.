# The Workshop Security Division / CTF Arena

MVP 0.2: quinze desafios simulados de encoding, web, redes, SQL, logs defensivos, DNS, Python e criptografia, com 1855 pontos possíveis e pontuação permanente em Cloudflare D1.

## Modelo de segurança
- Desafios confinados a artefatos fictícios apresentados pelo portal. Não existe sandbox de exploração real, shell ou execução arbitrária.
- Flags WS{...} personalizadas para cada jogador e desafio via HMAC SHA-256 e segredo exclusivo mantido na Cloudflare.
- Validação e ranking exclusivamente no servidor; submissões duplicadas não somam pontos.
- Perfil com pseudônimo, sem e-mail. Sessões em cookie HttpOnly, Secure, SameSite Strict; chave de recuperação de uso continuado exibida apenas na criação.
- Política CSP restrita, sem dependências de terceiros, DOM tratado via textContent e limite básico de tentativas por perfil.
- Não recolha dados pessoais nos codinomes.

## Limitações beta
Não há anti-Sybil, CAPTCHA/Turnstile ou rate limiting por IP na criação das contas. O ranking é recreativo, não adequado a competições com prêmios. A recuperação revoga sessões anteriores. A chave de recuperação não pode ser novamente exibida. A aplicação não autoriza testes contra outros domínios da organização.

## Deploy
Arquivo worker.mjs contém placeholders __INLINE_HTML__, __INLINE_CSS__, __INLINE_JS__ que devem ser substituídos por JSON.stringify de index.html, styles.css e app.js antes do upload à Cloudflare Worker.
Bindings: DB para D1 workshop-security-ctf; FLAG_SECRET como secret_text de 32 caracteres ou mais, nunca versionado.
Inicialize o banco usando schema.sql.

## Roadmap
Turnstile e limites distribuídos, moderação dos codinomes, novas categorias e níveis, painel administrativo e auditoria antifraude.


## Mascote oficial: Argus
Argus é o guardião da Security Division e acompanha o onboarding da arena. A arte oficial está em `assets/argus.avif` (AVIF responsivo, 1672 × 941), carregada no próprio domínio como `/assets/argus.avif`. O Oni permanece como anfitrião na seção original, sem mudanças de fluxo.

## Compilação reproduzível
Execute `node web/workshop-security/build.mjs` antes de publicar com `wrangler deploy --config web/workshop-security/wrangler.toml` (ajuste o diretório de trabalho conforme o Wrangler). O build injeta HTML/CSS/JS e AVIF no Worker, mantendo o conteúdo servido por rotas `GET` de mesma origem. `FLAG_SECRET` deve continuar configurado como segredo, nunca versionado. Testes: `node --test web/workshop-security/tests/argus.test.mjs`.

## Expansão v0.2 | 8 novas missões
Bits na Escuridão (60), Rota Percentual (85), Fragmentos de Rede (120), Consulta das Evidências (130), Detector de Eventos (140), Sussurros no DNS (160), Python sob a Lupa (180) e O Cofre das Camadas (210). Não altera IDs ou pontos das sete missões originais. Nenhuma migração de D1. Todos os exercícios permanecem restritos a conteúdo sintético, com flags vinculadas ao jogador e validadas no backend. Filtros no catálogo são exclusivamente visuais. Testes: `node --test web/workshop-security/tests/challenges-v02.test.mjs`.
