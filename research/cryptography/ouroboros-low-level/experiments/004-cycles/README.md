# OUROBOROS | EXP 004 — Ciclos, Floyd e Brent

**WolfPack Crypto Lab** • [Site](https://wolfpack-crypto.pages.dev) • [Ouroboros Low Level](../../README.md)

## Hipótese
Para \( f_m(x)=\operatorname{first}_k(\operatorname{SHA256}(m\parallel \operatorname{BE}_k(x))) \), toda trajetória num espaço finito eventualmente entra em ciclo. Queremos medir o pré-período \(\mu\), o comprimento \(\lambda\) e o custo de detecção.

**Escopo:** implementação independente de referência em Python/hashlib, para \(k=16\) e \(k=32\), com \(m=\)"ouroboros". Não é auditoria da implementação C/Assembly de `ouroboros_step`.

## Como repetir
```sh
python3 cycle_probe.py --bits 16 --message ouroboros --full-graph
python3 cycle_probe.py --bits 32 --message ouroboros
```
Condição inicial padrão: `first_k(SHA256(mensagem))`. Na transição, o estado é codificado com largura fixa, **big-endian**. O binário C original pode usar inicialização diferente.

## Resultados observados

| Medida | 16 bits | 32 bits |
|---|---:|---:|
| Seed | 0x93DB | 0x93DBF636 |
| Pré-período (μ) | 55 | 115.659 |
| Ciclo (λ) | 31 | 19.959 |
| Estados distintos até primeira repetição | 86 | 135.618 |
| Entrada do ciclo | 0xE977 | 0xA8A73F96 |
| Avaliações Floyd | 327 | 610.539 |
| Avaliações Brent | 235 | 402.307 |

Análise **exaustiva** de 16 bits: 65.536 estados; **6 ciclos** de comprimentos 155, 31, 18, 7, 4 e 1. O ponto fixo é `0x9A18`. Existem **216** estados diretamente em ciclos e **65.320** fora deles. Maior bacia de atração: 40.691 estados.

No caso de 32 bits, Brent usou cerca de **34,1% menos avaliações** que Floyd para localizar o mesmo ciclo.

## Limitações

- Esses resultados pertencem à função **truncada**, não ao SHA-256 completo de 256 bits.
- Não há evidência de que ciclos longos ou estatísticas favoráveis impliquem segurança criptográfica.
- Não confundir derivação determinística de estados com sigilo ou recuperação pós-comprometimento.
- Para comparação com `./ouroboros --self-reference`, verificar **serialização**, **estado inicial** e lógica efetiva do código-fonte C.
- A aproximação para a primeira repetição de uma *função aleatória ideal* é \(\sqrt{\pi 2^k/2}\), não um limite garantido.

**The Workshop:** Build. Break. Understand. Rebuild.
