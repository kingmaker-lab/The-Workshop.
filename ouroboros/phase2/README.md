# Ouroboros Fase II · O Limiar da Serpente

Laboratório offline para a rede de Feistel sintética do EXP-008. Uso exclusivo de pesquisa. Para dados reais, use uma biblioteca mantida com AEAD estabelecido. A implementação e o oráculo congelados conservam seus nomes e semântica históricos.

- [Inventário das fontes](INVENTARIO.md)
- [Decisões, critérios de refutação e agenda 2027](ARQUITETURA.md)
- [Resultados locais](RESULTADOS.md)

Na raiz do projeto, com Python 3.11+ e biblioteca padrão:

```sh
python3 -m unittest ouroboros.phase2.test_lab -v
python3 -m ouroboros.phase2.lab trace
python3 -m ouroboros.phase2.lab panel
python3 -m ouroboros.phase2.lab schedule
python3 -m ouroboros.phase2.lab benchmark
```

`trace` mostra os dois bytes do estado a cada rodada; `panel` compara Feistel, identidade e permutação aleatória usando a mesma amostra sintética. Use `panel --exact` para percorrer 65.536 entradas por diferença/máscara do recorte. O denominador converte contagens SAC e diferencial em probabilidades empíricas, e converte numeradores assinados de Walsh em correlações. A diferença de entrada e ambas as máscaras lineares têm peso um. A diferença de saída diferencial pode ter qualquer peso. O painel amostral é exploratório.

Para repetir a conformidade histórica, faça checkout de `34f98b19429070ab817c79bfc205d087cb62d3dd` do Workshop em uma cópia descartável e execute da raiz dela:

```sh
python3 research/cryptography/ouroboros-low-level/experiments/014-research-consolidation/conformance.py
```

O comando salva o relatório dentro dessa cópia.
