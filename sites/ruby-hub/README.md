# 💎 Ruby Hub | The Workshop Ruby Initiative

> **One language. Many worlds.**

Portal estático e independente que centraliza projetos desenvolvidos com Ruby no ecossistema The Workshop.

## Escopo da v0.1

- Catálogo versionado em `data/projects.json` (schema v1).
- Busca semântica simples por nome, tecnologia, área e descrição.
- Filtros dinâmicos por categoria.
- Detalhes individuais por rota hash (`#project/raven`), compartilháveis.
- Links de código apenas para fontes verificadas; projetos sem URL pública aparecem como "em validação".
- Layout responsivo, navegação por teclado e respeito a `prefers-reduced-motion`.
- Sem dependências de terceiros, analytics, cookies, contas ou execução de código remoto.
- Validador em Ruby e CI restrito ao diretório.

## Uso local

```sh
cd sites/ruby-hub
python3 -m http.server 8000
# Acesse http://localhost:8000
ruby scripts/validate_registry.rb
```

Servir por HTTP(S) é necessário porque o navegador lê o arquivo JSON com `fetch`.

## Cadastrar projeto

Adicione uma entrada em `data/projects.json` com `id` (slug único), `name`, `category`, `status`, `kind`, `description`, `stack` (incluindo Ruby), `repo` e `site`. Use `null` para URLs ainda não confirmadas. URLs aceitas: HTTPS de `github.com` ou dos domínios explicitamente aprovados no validador e no cliente. Execute:

```sh
ruby sites/ruby-hub/scripts/validate_registry.rb
```

O portal gera filtros e cards sem alterações manuais no HTML.

## Hospedagem

`sites/ruby-hub/` é a raiz de publicação estática, adequada a Cloudflare Workers Static Assets ou Pages Direct Upload. Configurar o serviço de hospedagem separadamente; commit no GitHub **não significa deploy**. `_headers` aplica cabeçalhos de segurança no Cloudflare Pages compatível (em outros hosts, configurá-los no servidor).

## Segurança e privacidade

O site apenas cataloga projetos. **Não executa código Ruby arbitrário**, não abre conexão com ferramentas privadas e não incorpora aplicações via iframe. Dados do registro são renderizados via DOM/textContent, não HTML não confiável. Links externos são restritos a HTTPS e abertos com `noopener noreferrer`. Não publicar URLs de repositórios privados, segredos ou endpoints administrativos.

## Próximos passos

- Verificar endpoint público e repositório do Protocolo Ruby antes de ativar botões de acesso.
- Publicar o Ruby Hub em uma rota própria, com testes de acessibilidade e smoke test HTTP.
- Estabelecer o Ruby Atlas como projeto independente e adicioná-lo ao registro quando existir.
- Automatizar releases públicos a partir de metadados verificados, sem dar ao site acesso a tokens.

**The Workshop** • Build. Break. Understand. Rebuild.
