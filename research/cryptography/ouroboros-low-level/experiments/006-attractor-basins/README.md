# OUROBOROS — EXPERIMENTO 006
**The Workshop / WolfPack Crypto Lab** • Bacias de atração • [Ouroboros Low Level](../../README.md)

## Hipótese e modelo
Mudar a mensagem modifica a topologia da função:
\[
f_m(x)=\operatorname{first}_{16}(\operatorname{SHA256}(\operatorname{UTF8}(m)\parallel\operatorname{BE}_{16}(x)))
\]
O estado é codificado como **dois bytes big-endian**. Uma bacia de atração inclui todos os estados que eventualmente chegam ao mesmo ciclo. O programa examina os **65.536 estados** para cada mensagem e usa poda por grau de entrada para identificar ciclos, suas bacias e distâncias até eles.

## Resultados medidos

| Mensagem | Ciclos | Maior ciclo | Maior bacia | Estados nos ciclos |
| --- | ---: | ---: | ---: | ---: |
| ouroboros | 6 | 155 | 40.691 (62,09%) | 216 |
| OUROBOROS | 12 | 460 | 50.809 (77,53%) | 541 |
| Ouroboros | 8 | 104 | 32.469 (49,54%) | 158 |
| wolfpack | 3 | 312 | 64.623 (98,61%) | 361 |
| ares | 8 | 177 | 28.932 (44,15%) | 403 |
| the workshop | 5 | 190 | 52.655 (80,35%) | 287 |
| ouroboros! | 9 | 204 | 38.541 (58,81%) | 348 |
| (vazia) | 6 | 419 | 62.934 (96,03%) | 496 |

Regressão do **EXP-004**, para m="ouroboros": ciclos `155,31,18,7,4,1`; bacias `40691,15629,8251,928,35,2`; ponto fixo `0x9A18`; seed padrão `0x93DB` alcança, após 55 passos, um ciclo de 31 estados, entrando em `0xE977`.

## Semelhança de bacias e alteração de um bit

`P_flip = (1 / (16 * 65536)) * sum(x,bit) [B(x)==B(x XOR (1<<bit))]`.

A linha de base para dois estados uniformes e independentes com reposição é:

\[
P_{indep}=\sum_i (|B_i|/65536)^2
\]

| Mensagem | Mesmo ciclo ao inverter um bit | Estados independentes |
| --- | ---: | ---: |
| ouroboros | 45,8487% | 45,8435% |
| wolfpack | 97,2565% | 97,2525% |
| ares | 33,3929% | 33,4191% |

A grande bacia de `wolfpack` explica por que tantos estados diferentes acabam no mesmo ciclo. **Isso não demonstra segurança criptográfica.**

## Reproduzir

Somente Python 3.9+; nenhuma dependência externa para os cálculos:

```sh
python3 basins.py --output out
python3 basins.py --message ouroboros --message 'nova mensagem' --output meus_resultados
python3 -m unittest -v
```

Saídas: `results.json` e `summary.csv`. O gráfico PNG e script opcional de visualização estão no pacote de pesquisa.

## Limitações

- Análise exaustiva de **funções reduzidas de 16 bits**, não do SHA-256 de 256 bits e nem da máquina de estados C/Assembly de 64 bits.
- Uma mensagem diferente define **outro grafo funcional**. Dentro do mesmo grafo, modificar a seed é um experimento diferente (EXP-005).
- Ciclos compartilhados não implicam colisão sincronizada.
- Oito mensagens escolhidas manualmente não formam uma amostra estatisticamente representativa.
- Boa difusão, ciclos longos e bacias grandes ou pequenas **não provam resistência criptográfica**.

**Próximo estudo:** EXP-007, Strict Avalanche Criterion, independência de bits e comparação com a implementação original de baixo nível.
