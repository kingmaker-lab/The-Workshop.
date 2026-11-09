# EXP-003: Wallets & Digital Signatures
**The Workshop Crypto Lab · 2026-11-09 · [Experimento público](https://workshop-labs.pages.dev/crypto-lab/signatures/)**

Demonstração didática de carteiras temporárias, assinaturas ECDSA P-256, verificação criptográfica e ledger local com unidades **fictícias**. Não é compatível com Bitcoin, Ethereum ou qualquer rede real.

## Como usar
1. Abra `https://workshop-labs.pages.dev/crypto-lab/signatures/` em HTTPS.
2. Duas carteiras efêmeras são criadas automaticamente; cada uma começa com **100 unidades fictícias**, sem emissão on-chain.
3. Escolha remetente, destinatário e um valor inteiro entre 1 e 100; clique em **Assinar e transferir**.
4. Veja a assinatura, o nonce e a chave pública. Use **Auditar histórico**.
5. Use **Adulterar valor** ou **Repetir transação** para observar a rejeição; **Limpar histórico** restaura os saldos iniciais.

## Protocolo
- Chaves ECDSA P-256 via Web Crypto API, `extractable=false` ao gerar; apenas chave pública SPKI é exportada.
- Endereço: `wk_` + SHA-256 hexadecimal dos bytes públicos SPKI (identificador demonstrativo, sem formato real de wallet).
- Payload assinado em UTF-8: `JSON.stringify(["THE_WORKSHOP_EXP003_V1", from, to, amount, nonce])`. O marcador de domínio reduz confusão entre protocolos nesta demonstração.
- `crypto.subtle.sign/verify({name:"ECDSA",hash:"SHA-256"})`.
- O remetente é conferido pela derivação do endereço a partir da chave pública importada.
- Nonces monotônicos por remetente, iniciando em 1; replay ou nonce fora de ordem invalida o histórico a partir do ponto de falha.
- O auditor reconstrói saldos e nonces do zero, verifica assinatura e saldo antes de aceitar cada operação; no máximo 20 registros.

## Limites de segurança e escopo
- Não usa chaves, tokens, saldos ou dinheiro reais. Não pede seed phrase nem senha.
- A chave privada não pode ser exportada pela Web Crypto API, **mas** scripts maliciosos executando na mesma origem ainda poderiam solicitar assinaturas enquanto a sessão existir; este não é um cofre seguro.
- Todos os registros e chaves estão na memória da página e desaparecem ao recarregar. Não há contas, D1, KV, armazenamento ou APIs de transferência.
- A carteira não prova identidade civil. Não há blockchain, rede, consenso, mecanismo global contra gasto duplo, transações externas ou smart contracts.
- A emissão de 100 unidades é predefinida no ambiente local de simulação e não tem valor econômico.
- Os exemplos de tampering/replay servem para observação, não executam ataques em sistemas externos.

## Testes
```bash
node --test web/crypto-lab/signatures/tests/protocol.test.cjs
# Para testar manualmente no navegador:
cd web/crypto-lab && python3 -m http.server 8000
# Abra http://localhost:8000/signatures/
```
`tests/browser-smoke.js` e `tests/ui-smoke.js` foram executados na **prévia HTTPS**, em rotas de testes temporárias **não publicadas em produção**. Os 15 testes do protocolo e os 10 testes da interface passaram.

## Deploy e compatibilidade
- Production: `2fe64c41-5f98-4752-ac6d-41c58d3c0138` (2026-11-09).
- Rollback anterior: `8bf689ec-7006-4e52-807d-b0ac402a0969` (EXP-002).
- Worker de integração: `../workshop-labs-integration-worker.js`.
- Ouroboros, ARGUS, CERBERUS e EXP-001/002 são preservados via roteamento legado para a implantação imutável `104f1000`.
- A dependência desse snapshot é temporária. A próxima evolução arquitetural deve consolidar todos os arquivos e funções num build reproduzível com smoke tests e rollback.
