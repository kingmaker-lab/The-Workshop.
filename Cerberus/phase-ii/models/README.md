# CERBERUS FASE II · Dois modelos executáveis

Java e Pascal são adaptadores intercambiáveis. Cada um codifica a mesma decisão de domínio em um quadro binário e o entrega por stdin a um processo Linux x86-64 escrito em GNU Assembly. A fronteira entre processos é a mesma para os dois modelos. Os exemplos executam offline e exercitam regras do CERBERUS com entradas explícitas, sem conectar ao banco ou ao serviço TCP.

## Modelo 1 · Admissão de uma sessão

O adaptador recebe o indicador de manutenção, o número de sessões ativas e o limite. O processo Assembly valida os campos e aplica a precedência do serviço CERBERUS. Manutenção recusa novas sessões mesmo quando há capacidade. Fora da manutenção, a admissão exige `ativas < limite`.

O chamador é responsável por ler a política autenticada e reservar a vaga sob o mesmo bloqueio usado para contar sessões. Executar apenas o veredito em paralelo não reserva vagas. No CERBERUS, essa responsabilidade fica com o consumidor TCP.

```bash
cd models
make
set -o pipefail
java -cp build Frame admission 0 2 3 | build/gate
printf 'admissão com vaga = %s\n' "$?"
build/frame-pascal admission 0 3 3 | build/gate
printf 'capacidade atingida = %s\n' "$?"
```

Resultado esperado: `0` e `2`.

## Modelo 2 · Veredito para recuperação de revisão

O adaptador recebe a geração ativa, a geração esperada pelo operador e a origem desejada. O Assembly verifica a geração esperada e exige que a origem seja anterior à ativa. Também recusa o incremento de uma geração que já atingiu o maior valor representável no formato.

O veredito autoriza apenas a transição numérica. O chamador precisa verificar a existência e o HMAC da revisão de origem e, na mesma transação, registrar a revisão nova. O armazenamento do CERBERUS usa gerações de 63 bits não negativos. O contrato didático usa 32 bits sem sinal, com limite explícito e sem truncamento pelos adaptadores.

```bash
cd models
make
set -o pipefail
build/frame-pascal recovery 3 3 0 | build/gate
printf 'recuperação permitida = %s\n' "$?"
java -cp build Frame recovery 3 2 0 | build/gate
printf 'geração obsoleta = %s\n' "$?"
```

Resultado esperado: `0` e `1`.

## Contrato entre processos

Um quadro possui exatamente 16 bytes, quatro palavras `uint32` little-endian, seguidas de EOF. As duas CLIs aceitam palavras em decimal ASCII de 1 a 10 dígitos, sem sinal. O executável Assembly usa as chamadas Linux `read` e `exit`. Lê até completar o quadro, repete a leitura interrompida por sinal e rejeita bytes extras. Cada invocação toma uma decisão e comunica somente o código de saída.

| Palavra | Admissão | Recuperação |
| --- | --- | --- |
| 0 | 1 | 2 |
| 1 | Manutenção (0 ou 1) | Geração ativa |
| 2 | Sessões ativas | Geração esperada |
| 3 | Limite (1–10000) | Geração de origem |

| Saída | Admissão | Recuperação |
| --- | --- | --- |
| 0 | Admitida | Transição numérica válida |
| 1 | Em manutenção | Geração esperada obsoleta |
| 2 | Sem capacidade | Origem igual ou posterior à ativa |
| 3 | — | Geração esgotada |
| 64 | Quadro inválido ou erro de leitura | Quadro inválido ou erro de leitura |

## Reproduzir

Em Debian x86-64, instale `binutils`, `make`, `default-jdk-headless`, `fp-compiler` e `python3`. Na raiz da FASE II, execute `make -C models test`.

A execução local em Debian 13.6 com GNU Binutils 2.44, OpenJDK 21.0.13 e Free Pascal 3.2.2 passou nas quatro suítes. Elas incluem 16 vetores de domínio executados pelas duas cadeias, 14 entradas inválidas nos adaptadores e cinco quadros rejeitados pelo Assembly. Os testes usam processos reais e comparam bytes contra uma referência independente em Python.
