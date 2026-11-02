# The Workshop Security Division / CTF Arena

MVP 0.1: sete desafios simulados (Base64, ROT13, HTML, logs HTTP, XOR, JavaScript e JSON), com pontuação permanente em Cloudflare D1.

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
