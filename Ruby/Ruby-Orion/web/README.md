# 💎 Ruby Orion Studio | Interactive Environments

**The Workshop Ruby Initiative · Orion v0.2 · Studio Preview v0.1**

Ambientes práticos para a linguagem Ruby, sem acesso remoto ao executor de processos do Orion CLI.

## O que existe

1. **Ruby Playground:** editor de código, stdin, stdout/stderr, execução de Ruby 3.4 via Ruby WASM dentro de um Web Worker, interrupção, timeout, snippets.
2. **Orion Labs:** três laboratórios carregáveis e editáveis com saída esperada, EXP-001 (objetos), EXP-002 (estados de processo) e EXP-003 (JSON IPC).
3. **File Lab:** reconhecimento heurístico de arquivos, entropia amostral, SHA-256 e SHA-512 por Web Crypto API, apenas no navegador.

EXP-002 no Studio é uma **simulação do ciclo de vida**, não criação de processos OS. EXP-003 demonstra **mensagens JSON**, não pipes reais. Para processos e IPC reais, use a CLI instalada localmente.

## Ambiente local

```sh
cd Ruby/Ruby-Orion/web
ruby scripts/validate_site.rb
ruby scripts/build-worker.rb
node --check assets/studio.js
node --check assets/ruby-worker.js
node --check dist/worker.mjs
python3 -m http.server 8080
# http://localhost:8080
```

A execução real de Ruby/WASM exige internet na primeira inicialização para consultar a versão fixa do runtime no CDN. Sem essa dependência, o editor ainda abre, mas executar código retorna um erro visível.

## Modelo de segurança

- Aplicação e frontend estão em Worker separado, sem tokens, cookies de sessão ou acesso a recursos administrativos.
- **Nenhum código do editor é enviado ao servidor Orion ou executado na CLI/Cloudflare.**
- Código Ruby roda em um Web Worker do navegador, com limites de tamanho, saída e tempo. Interrupção encerra o Worker.
- Importação externa limitada a `cdn.jsdelivr.net`, fixada na versão `2.10.1` do projeto oficial ruby.wasm (`@ruby/wasm-wasi` + CRuby `3.4`).
- Política CSP limita fontes de script, workers, execução WebAssembly e conexões. Não há `unsafe-eval` JavaScript.
- Resultados do Ruby são renderizados via `textContent`, sem `innerHTML`.
- File Lab usa APIs do navegador, não envia arquivos a terceiros, recusa arquivos maiores que 8 MiB.
- Nenhum laboratório permite execução de comandos do sistema por um servidor.
- **Aviso:** WebAssembly e Web Workers não constituem isolamento absoluto. O runtime de terceiros opera no contexto do Worker; não cole credenciais, informações privadas ou código deliberadamente hostil.

## Publicação

`ruby scripts/build-worker.rb` gera `web/dist/worker.mjs`, um bundle de recursos estáticos do Studio para Cloudflare Workers. Este arquivo é gerado e ignorado pelo Git.

O deployment oficial fica em um Worker independente do Ruby Hub, Protocolo Ruby e Wolfpack. Publicar uma alteração no GitHub não implica atualização automática da Cloudflare.

## Roadmap

- Studio Preview: playground, três laboratórios e File Lab.
- Studio v0.2: histórico opcional exportável, editor com diagnósticos, testes interativos extras.
- Studio v0.3: runtime hospedado no próprio domínio com versão/hash controlados, reduzindo dependência do CDN.
- Mintaka: experimentos de sockets em ambiente próprio, sem disponibilizar acesso à rede local de visitantes.

Referência: https://ruby.github.io/ruby.wasm/
