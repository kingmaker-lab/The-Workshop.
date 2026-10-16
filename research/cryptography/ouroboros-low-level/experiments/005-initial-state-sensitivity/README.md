# 🐍 OUROBOROS | EXP 005 — Sensibilidade às condições iniciais

**WolfPack Crypto Lab** • [Ouroboros Low Level](../../README.md)  
Status: **EXPERIMENT / Não auditado**

## Hipótese
Alterar um único bit na seed inicial muda o percurso em uma função determinística de estado finito, mas não necessariamente o ciclo final. O objetivo é medir sensibilidade, convergência para ciclos e colisões sincronizadas.

Modelo idêntico ao EXP-004:

\[
f_m(x)=\operatorname{first}_k(\operatorname{SHA256}(\operatorname{UTF8}(m)\parallel\operatorname{BE}_k(x)))
\]

Para `k=16` ou `k=32`, o estado é codificado em big-endian com largura fixa. Mensagem: `ouroboros`. Seed original: `first_k(SHA256("ouroboros"))`. Para cada bit `j`, testamos `seed XOR (1 << j)`.

## Resultados reproduzidos

| Medida | 16 bits | 32 bits |
|---|---:|---:|
| Seed original | `0x93DB` | `0x93DBF636` |
| Modificações testadas (um bit) | 16 | 32 |
| Pré-período (μ) original | 55 | 115.659 |
| Comprimento do ciclo (λ) original | 31 | 19.959 |
| Modificações que chegam ao mesmo ciclo | **4/16** | **27/32** |
| Modificações que chegam a ciclo diferente | **12/16** | **5/32** |
| Colisões na mesma iteração | **0** | **0** |
| Distância de Hamming média entre t=1 e t=255 | **8,06103/16** | **15,99473/32** |

Em 32 bits, alterar os bits **0, 23, 26, 30 ou 31** envia a trajetória para outro ciclo (λ=39.318). As outras 27 trajetórias entram no ciclo original de λ=19.959, em **fases diferentes**; não colidem com a trajetória de base no mesmo instante.

Em 16 bits, as 16 trajetórias modificadas terminam em ciclos de λ=7 (8 trajetórias), λ=31 (4) e λ=155 (4).

Esses valores se referem aos vizinhos de **distância de Hamming 1 desta seed específica**, não a uma distribuição de seeds aleatórias.

## Por que mesma órbita não significa mesma trajetória?

Duas trajetórias podem eventualmente visitar o mesmo conjunto de estados do ciclo, mas em instantes diferentes. Se `x_t == y_t` em algum instante, por determinismo serão iguais para todos os instantes posteriores. Por outro lado, se compartilham o mesmo ciclo mas têm fases distintas quando ambas chegaram ao ciclo, nunca terão colisão **sincronizada**.

A distância de Hamming foi medida como:

\[
d_H(x_t,y_t)=\operatorname{popcount}(x_t\oplus y_t)
\]

A média próxima de metade do total de bits é um **dado descritivo**, não demonstra segurança criptográfica, independência estatística ou resistência a ataques.

## Executar localmente

Requer somente **Python 3.9+**, sem pacotes adicionais:

```sh
python3 ouroboros_sensitivity.py --bits 16 --output results_16bit.json
python3 ouroboros_sensitivity.py --bits 32 --output results_32bit.json
python3 -m unittest -v
```

Para mais amostras temporais:

```sh
python3 ouroboros_sensitivity.py --bits 32 --samples 512 --max-states 2000000
```

O programa imprime o resumo e, com `--output`, salva os dados completos por bit e a curva média de Hamming.

## Limitações
- **Não executamos o Assembly original `ouroboros_step`**. É uma referência Python/hashlib da função reduzida de SHA-256 do EXP-004. Comparar requer ler e testar o código C/ASM.
- Alterar a seed não altera o próprio grafo da função.
- Nossas 16/32 alterações são correlacionadas, sobre **uma única mensagem**. Novas mensagens e seeds devem ser investigadas.
- Ciclos longos, aparente difusão e algumas métricas próximas de 50% **não provam segurança**, sigilo ou aleatoriedade criptográfica.

**Próximo passo:** caracterizar bacias de atração em 16 bits com múltiplas mensagens e comparar implementações com vetores determinísticos.

*The Workshop — Build. Break. Understand. Rebuild.*
