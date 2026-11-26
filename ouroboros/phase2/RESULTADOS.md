# Resultados locais em 26 de novembro de 2026

Os cinco testes da Fase II passaram, incluindo 25 vetores históricos com cifragem e inversão nas duas implementações, concordância das agendas das cinco chaves, verificação do traço de rodadas e os controles do painel. No EXP-004, as duas execuções documentadas repetiram os seis ciclos de 16 bits e o período de 19.959 na trajetória de 32 bits.

A reconstrução das equações de EXP-002 reproduziu `0x80000000 → 0x00001040` em 65.536 pares sintéticos. Em EXP-003, a linha `0x80 → 0x50` foi verificada para todas as 256 entradas e todas as 256 chaves de 8 bits.

As suítes históricas EXP-005–014 passaram em uma cópia descartável, com 62 testes no total. A execução separada de conformidade do EXP-014 repetiu 327.680 comparações, cobrindo o domínio completo de 16 bits para cinco chaves, com cinco verificações de permutação e 40 bytes de subchave comparados. O JSON gerado coincidiu byte a byte com o relatório versionado na fotografia local de `origin/main`.

## Painel exato

A chave sintética é `01234567`. Foram avaliadas 65.536 entradas para cada diferença ou par de máscaras do recorte. O máximo diferencial conta pares ordenados. O máximo linear é o maior numerador absoluto de Walsh. O denominador de ambas as medidas é 65.536.

| Permutação | Bits alterados em média | Máximo diferencial | Máximo linear |
|---|---:|---:|---:|
| Feistel de 8 rodadas | 7,99694 | 44 | 736 |
| Identidade | 1,00000 | 65.536 | 65.536 |
| Controle aleatório | 8,00116 | 14 | 796 |

No painel piloto de 4.096 entradas, os máximos diferenciais do Feistel e do controle aleatório foram 4 e 5 respectivamente. Essa diferença em relação à enumeração exata motiva a repetição com várias chaves e controles, sob um protocolo confirmatório. O comparativo atual usa uma chave e uma permutação aleatória.

## Agenda e custo

A agenda KS1 coincidiu com o oráculo e satisfez a identidade de XOR para as 256 chaves sintéticas. Conforme o bit de chave alterado, mudaram em média de 29,16 a 32,63 dos 64 bits de subchave.

No Debian 13 com Python 3.13.5, a mediana inicial foi de 24,47 µs para expansão da chave e 18,81 µs por bloco com agenda preparada, em cinco repetições de 4.096 chamadas. Os valores incluem a sobrecarga do laço Python e variam com a máquina e a carga.
