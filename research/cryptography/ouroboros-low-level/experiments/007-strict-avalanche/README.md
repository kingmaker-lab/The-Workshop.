# 🐍 Ouroboros | EXP-007 — Strict Avalanche Criterion

**The Workshop / WolfPack Crypto Lab**  
**Status:** protocolo implementado, piloto executado, ainda em pesquisa. **Não é certificação criptográfica.**

## Questão

No EXP-005, a média da distância de Hamming (t=1…255) ficou próxima de metade dos bits. Isso **não** mostra que cada bit de saída muda com probabilidade próxima de 50%, nem que as mudanças dos bits de saída são independentes. O EXP-007 investiga ambas as questões, separadamente.

```text
Δ_i(x) = F(x) XOR F(x XOR 2^i)
A[i,j] = P[bit_j(Δ_i(x)) = 1]
E[d_H] = Σ_j A[i,j]
```

A referência SAC idealizada é `A[i,j] ≈ 0.5` em **cada célula**, não apenas na média global.

## Motores comparados

- `sha16` e `sha32`: `first_k(SHA256(UTF8(mensagem) || big_endian_k(estado)))`, exatamente a família dos EXP-004–006.
- `identity16` e `identity32`: controles deliberadamente previsíveis.
- `toy_arx8`: função do EXP-003 com chave fixa 0x2A, controle deliberadamente fraco.
- **Ouroboros Assembly x86-64:** pendente de fonte original e vetores verificáveis. Não atribuir resultados de SHA-256 truncado ao motor C/ASM.

Para cada bit de entrada, o programa escolhe pares distintos `{x, x XOR 2^i}`, representados pelo elemento com bit `i=0`. Esse cuidado evita contar duas vezes a mesma diferença. Em 8/16 bits há opção de enumeração exaustiva; 32 bits usa amostras sem reposição.

## Métodos

1. Construir matriz SAC por bit de entrada/saída, salvando `sac_matrix.csv` e `sac.csv`.
2. Medir média da matriz, erro médio absoluto de 0,5, desvio máximo e distância de Hamming por par.
3. Estimar associação pareada entre indicadores de mudança por coeficiente **phi** (`bic.csv`). Marginais constantes produzem valor indefinido, não zero.
4. Conferir resultados contra controles fracos e vetores fixos.
5. Planejar correções para múltiplos testes *antes* de inferir significância estatística; não fazer alegações de segurança baseadas apenas nesses dados.

## Reproduzir (Python 3.9+, apenas biblioteca padrão)

```bash
python3 -m unittest -v
python3 sac_probe.py --engine sha16 --samples 4096 --bic-samples 256 --output results/sha16
python3 sac_probe.py --engine sha32 --samples 4096 --bic-samples 256 --output results/sha32
python3 sac_probe.py --engine toy_arx8 --exhaustive --output results/toy_arx8
python3 sac_probe.py --engine identity16 --samples 256 --output results/identity16
# 16 bits: 2^15 pares para cada bit de entrada
python3 sac_probe.py --engine sha16 --exhaustive --bic-samples 1024 --output results/sha16_exhaustive
```

## Piloto (amostras de 4096 pares por bit, BIC 256; controles conforme acima)

| Motor | Bits alterados em média | Média SAC | MAE de 0,5 | Maior desvio |
|---|---:|---:|---:|---:|
| sha16 | 7,99222/16 | 0,499514 | 0,005869 | 0,020996 |
| sha32 | 16,00418/32 | 0,500131 | 0,006079 | 0,026611 |
| toy_arx8 (exaustivo) | 2,88281/8 | 0,360352 | 0,426758 | 0,500000 |
| identity16 (256 pares) | 1/16 | 0,062500 | 0,500000 | 0,500000 |

**Resultados exploratórios**, de funções reduzidas, sem inferência de segurança. Um bom resultado SAC não prova resistência criptográfica. A associação BIC não testa todas as possíveis dependências de ordem superior.

## Próximas etapas

- Repetir amostras com mensagens e seeds de amostragem diferentes.
- Realizar análise exaustiva de SHA-256 truncado em 16 bits.
- Definir testes estatísticos pré-registrados e controle de múltiplas comparações.
- Receber, compilar e validar o `ouroboros_step` original em C/ASM com vetores independentes antes de estudá-lo.

Referências: Webster & Tavares (CRYPTO '85), *On the Design of S-boxes*; [NIST SP 800-22 Rev. 1a](https://csrc.nist.gov/pubs/sp/800/22/r1/upd1/final).

**Build. Break. Understand. Rebuild.**
