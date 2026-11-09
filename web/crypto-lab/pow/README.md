# EXP-002 — Proof-of-Work Miner
**The Workshop Crypto Lab · 2026-11-09 · [Experimento público](https://workshop-labs.pages.dev/crypto-lab/pow/)**

Simulador educativo 100% client-side, sem servidores de mineração, wallets, tokens ou blockchain pública. A execução usa `Web Worker` e `crypto.subtle.digest('SHA-256')`.

## Protocolo demonstrativo
Cada bloco minerado contém `index`, `previousHash`, `data`, `difficulty`, `nonce` e `hash`.

A serialização canônica usada no PoW é:
```js
const payload = JSON.stringify([index, previousHash, data, difficulty, nonce]);
// hash = hex(SHA-256(UTF8(payload)))
// condição: hash.startsWith('0'.repeat(difficulty))
```
Dificuldades: 1–4 zeros hexadecimais, probabilidades teóricas por tentativa de 1/16, 1/256, 1/4096 e 1/65536, respectivamente. Essas são médias estatísticas e não garantias.

O bloco gênese é uma âncora sintética com `difficulty=0` e `nonce=0`. Cada bloco minerado aponta ao hash registrado do anterior.

## Proteções e limitações
- 500.000 tentativas por bloco (pode encerrar sem encontrar solução); no máximo cinco blocos minerados.
- Cancelamento termina o worker; mineração é local e não envia dados para APIs externas.
- Validação independente recalcula hashes, confere nonce, dificuldade, índices e ligação ao bloco anterior.
- Os blocos são armazenados apenas na memória desta página e desaparecem ao recarregar.
- Não implementa consenso distribuído, incentivos, ajuste dinâmico de dificuldade ou segurança de um protocolo de produção; prefixos hexadecimais são um alvo simplificado.

## Testes e publicação
```bash
node --test web/crypto-lab/pow/tests/pow.test.cjs
# Servidor local em web/crypto-lab: python3 -m http.server 8000
# Abra http://localhost:8000/pow/
```

Integração com o Pages em `web/crypto-lab/workshop-labs-integration-worker.js`. O worker retém rotas do Ouroboros, ARGUS e demais páginas por proxy ao snapshot original `104f1000` e entrega apenas o Crypto Lab como rotas adicionais. **Estratégia temporária**: migração futura para pacote de deploy completo e reproduzível.

Deploy de produção: `8bf689ec-7006-4e52-807d-b0ac402a0969` (2026-11-09). Rollback da integração anterior: `b321939a-d200-4bf9-b553-e1d28b6ae152`.
