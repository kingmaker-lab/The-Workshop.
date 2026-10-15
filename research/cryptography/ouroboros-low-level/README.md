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
