# Ouroboros — Roadmap de encerramento da pesquisa (EXP-011 a EXP-015)

**The Workshop / WolfPack Crypto Lab**  
**Estado:** planejamento de pesquisa e transição de fase.

A decisão de projeto é encerrar a série de experimentos exploratórios no EXP-014. O EXP-015 não deverá introduzir uma nova hipótese criptográfica ou uma nova variante da cifra: ele marca o congelamento da pesquisa e o início da campanha de provas de funcionalidade.

## Linha de chegada

| Experimento | Tema | Estado |
|---|---|---|
| EXP-011 | Trilhas diferenciais, estimativas Markov, observações de chave fixa, linear trails e hulls | Em execução nesta branch |
| EXP-012 | Caracterização de KS1: difusão entre subchaves, chaves equivalentes/fracas e relações entre chaves | Em execução nesta branch |
| EXP-013 | Dependências entre subchaves de rodadas, difusão related-key e varredura densa de deltas de byte | Implementado; testes e campanha do job CI aprovados |
| EXP-014 | Consolidação de resultados, reprodutibilidade, vetores de referência e confronto das implementações disponíveis | Planejado |
| EXP-015 | Congelamento da fase exploratória e início das provas de funcionalidade | Marco de transição |

## EXP-012 — Key schedule sob análise

Questões previstas:
- distância de Hamming entre sequências de subchaves geradas por chaves mestras próximas;
- colisões e sequências equivalentes no espaço de chaves de 32 bits;
- comportamento de chaves fracas e padrões degenerados;
- impacto de diferenças controladas da chave mestra em cada subchave;
- comparação entre propriedades locais do KS1 e as diferenças/correlações observadas pela cifra.

Qualquer conclusão deverá separar evidência exaustiva no espaço reduzido, amostras determinísticas e hipóteses sobre segurança.

## EXP-013 — Busca ampliada de diferenças e máscaras

Questões previstas:
- diferenças de entrada com peso maior que um;
- máscaras lineares de peso maior que um;
- comparação de máximos, médias, distribuição e concentração de trilhas;
- busca de efeitos de reforço e cancelamento em hulls;
- controle do custo computacional e registro do espaço efetivamente explorado.

Uma DDT/LAT completa de 16 bits tem dimensão 65.536 × 65.536. Não será declarada completa sem enumeração integral verificável; o trabalho poderá usar subespaços explicitamente delimitados e nomeados como tais.

## EXP-014 — Consolidação e confronto de implementações

Questões previstas:
- fixar vetores de teste independentes para a cifra reduzida;
- verificar que código de referência, ferramentas de análise e implementações alternativas concordam;
- consolidar resultados negativos, limitações e falsificações de hipóteses;
- garantir que cada tabela publicada pode ser regenerada a partir de código versionado;
- registrar a versão congelada do desenho experimental e os hashes dos artefatos.

Não modificar S-box, permutação, KS1 ou número de rodadas apenas para melhorar métricas durante esta etapa. Variantes, se necessárias, devem receber identidade experimental independente.

## EXP-015 — Congelamento e provas de funcionalidade

Ao chegar ao EXP-015, encerrar a série de experimentos de criptoanálise exploratória. A fase seguinte será dedicada à validação funcional, sem confundir funcionamento correto com segurança criptográfica.

Campanha funcional proposta:
1. **Especificação congelada:** parâmetros, representação de bits/bytes, key schedule, ordem de rodadas e vetores conhecidos.
2. **Correção funcional:** cifra/decifra, ida e volta exaustiva, domínio/permutação, validação de entradas e comportamento de erro.
3. **Conformidade entre implementações:** comparar Python e C/Assembly, quando ambas existirem, com vetores determinísticos e testes diferenciais.
4. **Regressão e fuzzing:** propriedades invariantes, valores de borda, chaves degeneradas, blocos de borda e fuzzing determinístico.
5. **Build e portabilidade:** compilação reproduzível, warnings, sanitizers quando aplicáveis, arquitetura e ABI documentadas.
6. **Segurança de implementação:** memória, temporização, side channels, tratamento de chaves e limites documentados.
7. **Release gate:** nenhum resultado de funcionalidade será apresentado como prova de segurança criptográfica; uso real continua bloqueado sem revisão criptográfica independente.

## Regra de transição

- EXP-011 a EXP-014: investigar, medir, tentar refutar e documentar.
- EXP-015 em diante: congelar a pesquisa e provar que a implementação faz exatamente o que a especificação define.
- Não promover para uso real por ter passado testes funcionais. Correção funcional e segurança criptográfica são gates separados.

**Build. Break. Understand. Rebuild.**
