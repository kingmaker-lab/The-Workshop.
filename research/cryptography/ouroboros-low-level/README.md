# Ouroboros Low Level — C + Assembly x86-64

> The Workshop / WolfPack Crypto Lab  
> **Status:** [EXPERIMENT] — pesquisa autoral, não validada para proteção de dados reais.

Experimento mínimo de uma máquina de estados circular em C e Assembly x86-64. Esta documentação descreve o funcionamento informado pelo autor; não equivale a auditoria independente do código-fonte.

## 1. Máquina de estados em baixo nível

`ouroboros_step` recebe o estado em `RDI`, aplica as operações `XOR → ROL → IMUL → XOR` e devolve o estado seguinte em `RAX`. A função implementa uma transformação determinística em espaço finito de 64 bits.

```text
RDI (estado de entrada)
  ↓
XOR → ROL → IMUL → XOR
  ↓
RAX (próximo estado)
```

### Compilar e executar

```sh
make
./ouroboros
./ouroboros 0xDEADBEEFCAFEBABE 8 1000000
```

Argumentos opcionais: `seed`, número de estados para imprimir e limite de iterações da detecção de ciclos de Floyd. O limite existe porque encontrar um ciclo num espaço de 64 bits pode demandar esforço impraticável.

## 2. SHA-256 independente

Implementação própria de SHA-256, sem OpenSSL:

```sh
./ouroboros --sha256 ouroboros 3
```

A sequência é definida por:

```text
H₀ = SHA256(mensagem)
Hₙ = SHA256(Hₙ₋₁), n ≥ 1
```

Hash iterado **não é criptografia reversível** nem oferece por si só sigilo, autenticação ou segurança adicional comprovada.

## 3. Autorreferência reduzida a 32 bits

```sh
./ouroboros --self-reference ouroboros 1000000
```

Com `x` codificado em big-endian:

```text
x' = first32(SHA256(mensagem || x))
```

Reduzir o estado a 32 bits permite investigar ciclos e pontos fixos computacionalmente. Isso não corresponde à procura de ponto fixo para a função SHA-256 completa de 256 bits.

## 4. Epochs e evolução de chaves

```sh
./ouroboros --epochs seed-mestre 2 4
```

```text
key(counter)    = SHA256(epoch_state || counter)
next_epoch      = SHA256(epoch_state || final_digest)
```

O programa mantém estado da epoch corrente e digest final, sem lista histórica de chaves em memória. A reprodução determinística exige sincronização de seed, epoch, contador e serialização dos campos. Eventos locais/telemetria não devem participar de derivações entre máquinas que precisam concordar.

**Atenção:** não armazenar uma lista de chaves não implica apagamento seguro das chaves passadas, forward secrecy, recuperação pós-comprometimento ou resistência a vazamento do seed original. Para um protocolo real, seria necessário especificar codificação inequívoca, separação de domínios, modelo de ameaças e análise independente.

## 5. Derivação experimental de senha

```sh
./ouroboros --password seed-mestre github.com 202609 0 20
```

Combina seed, serviço, epoch e contador; aplica uma etapa de `Ouroboros` e HKDF-SHA-256 para produzir uma senha formatada e reproduzível.

**Não passe segredos reais no terminal como parâmetros CLI**: histórico de shell e inspeção de processos podem revelá-los. O uso de HKDF é apropriado como derivação a partir de material de chave de alta entropia, mas **não substitui Argon2id para senhas humanas de baixa entropia**. Para uso pessoal, prefira gerenciadores de senha e mecanismos de derivação adequados.

## Experimento 004 — ciclos, Floyd e Brent

A análise independente de SHA-256 truncado agora possui um [experimento reproduzível em Python](./experiments/004-cycles/README.md), com implementação da busca de Floyd e Brent e enumeração completa de estados de 16 bits.

- Estado de 16 bits: 6 ciclos; comprimentos `155, 31, 18, 7, 4, 1`; 1 ponto fixo.
- Estado de 32 bits (mensagem `ouroboros`, seed `0x93DBF636`): pré-período de 115.659 passos e período de 19.959.
- Comparação de custo: 610.539 avaliações com Floyd, 402.307 com Brent.

As medições são sobre uma função de referência, **não** uma execução ou auditoria da implementação original C/Assembly.

---

## Experimento 005 — sensibilidade à seed

O [EXP-005](./experiments/005-initial-state-sensitivity/README.md) avalia a alteração de um único bit da seed na função de SHA-256 truncada estudada no EXP-004, distinguindo **ciclos compartilhados** de **colisões sincronizadas**.

- **16 bits:** 4 das 16 seeds modificadas alcançaram o ciclo original; as demais chegaram a outros ciclos.
- **32 bits:** 27 das 32 seeds modificadas alcançaram o ciclo original. As cinco restantes chegaram a um ciclo de 39.318 estados.
- **Nenhuma colisão sincronizada** foi observada nas 48 comparações com as trajetórias originais.
- Distância média de Hamming (transições 1 a 255): 8,06103 bits em 16 bits e 15,99473 bits em 32 bits.

O script e seus testes são reproduzíveis em Python. O estudo **não** executa nem valida a implementação Assembly original.

---

## Experimento 006 — bacias de atração

O [EXP-006](./experiments/006-attractor-basins/README.md) mapeia exaustivamente **65.536 estados** de cada uma de oito variantes da função `first16(SHA256(mensagem || estado_big_endian))`.

- A mensagem `ouroboros` tem 6 ciclos; sua maior bacia reúne 40.691 estados (62,09%).
- `wolfpack` apresenta 3 ciclos, sendo que 64.623 estados (98,61%) convergem para o mesmo ciclo.
- `ares` apresenta 8 ciclos, com maior bacia de 28.932 estados (44,15%).
- O percentual de pares de estados que chegam ao mesmo ciclo após alteração de um bit foi comparado ao esperado de dois estados independentes no mesmo grafo.

Código e testes de referência reproduzíveis em Python, sem dependências externas. **Não é uma avaliação de segurança da implementação C/Assembly.**

---

## Experimento 007 — Strict Avalanche Criterion (SAC)

O [EXP-007](./experiments/007-strict-avalanche/README.md) estabelece um protocolo reproduzível para estudar **probabilidades individuais de alteração dos bits de saída**, dependência pareada entre bits (phi/BIC), e comparação com funções intencionalmente fracas.

- Motores de referência: SHA-256 truncado em 16/32 bits, ARX reduzida de 8 bits e identidade.
- Piloto amostral (4.096 pares por bit de entrada): 7,99222 bits diferentes em 16 bits e 16,00418 em 32 bits, em média. Esses valores **não** demonstram segurança criptográfica.
- O programa exporta matriz SAC, resumos JSON/CSV e estatísticas exploratórias de correlação entre alterações dos bits.
- **Pendente:** executar o `ouroboros_step` real em C/Assembly após obter código-fonte e vetores de teste verificáveis.

Status: **protocolo criado, piloto executado; análise em andamento**.

---

## 6. Próximas perguntas de pesquisa

- Qual é o comportamento estatístico da transformação `ouroboros_step`?
- Qual é a distribuição do comprimento dos ciclos para seeds amostrados?
- Como as codificações de seed e counter evitam ambiguidade?
- Qual é a resistência a comprometimento do estado atual?
- É possível formalizar segurança sob um modelo de ameaça, sem tratar a transformação experimental como cifra segura?

## Referências do ecossistema

- [WolfPack Crypto Lab](https://wolfpack-crypto.pages.dev/#lowlevel)
- [ARES Protocol](https://ares-protocol.pages.dev)
- [Workshop Labs](https://workshop-labs.pages.dev)

**Build. Break. Understand. Rebuild.**


---

## Experimento 009 — análise diferencial e linear da função de rodada

O [EXP-009](./experiments/009-round-function-analysis/README.md) executa a DDT completa (256 × 256) e a LAT de Walsh completa (256 × 256) para a função de rodada do EXP-008, com enumeração exata e testes de invariância sob subchaves fixas.

- Máxima contagem diferencial para diferença de entrada não nula: 64/256 (25%), em 48 células.
- Máxima correlação linear absoluta não trivial: 0,5 (Walsh = 128), em 72 células.
- Os resultados são da camada de rodada, não um ataque demonstrado contra a rede Feistel de oito rodadas.
- O harness exporta DDT/LAT completas em CSV e verifica as invariâncias de subchave.

**Conclusão:** a camada de rodada possui relações diferenciais e lineares fortes. A investigação seguinte deve modelar trilhas e hulls através da composição Feistel.
