# Science 0.1 | Baseline, riscos e próximos gates

**Snapshot:** 2026-11-13. Evidência observada: estrutura do GitHub e documentação. Testes pré-existentes **não** foram executados na auditoria inicial; consultar execuções independentes por SHA.

## Priorização

| Prioridade | Linha | Entrega incremental | Gate objetivo |
| --- | --- | --- | --- |
| P0 | Todas | Passar validação do catálogo, preservar CI, testar refs no PR, fixar baseline SHA. | G0 |
| P1 | ARGUS | Fixtures benignas e incidentes sintéticos, Sigma opt-in, matriz de falsos positivos. | G1/G2 |
| P1 | HeartAI | Corpus público fixo, seeds, regressões Byte-BPE e embeddings, análise de variação. | G1/G2 |
| P1 | Ouroboros | Vetores reais de C/ASM, comparadores de referência para ciclos e SAC; documentar cifra toy 16-bit. | G1/G2 |
| P1 | Active Sensing | Ambiente NumPy pinado, seeds e separação treino/teste, baselines VOI x custo. | G1 |
| P1 | Protocolo Ruby | Matriz main versus branch Render, fixtures de API e limites de arquivos; sem mudar produção. | G0/G1 |
| P2 | ARES & WOLF-VM | Corpus controlado, invariantes e sanitizers com testes reproduzíveis. | G1/G2 |
| P2 | RAVEN & Cerberus | Fixtures sintéticas compartilhadas, ADRs e medições de cenário. | G1/G2 |
| P2 | Crypto Lab | Preservar rotas atuais, testes E2E da camada de integração e evidência de deploy/rollback. | G1/G4 |
| P2 | NEXUS (The Arsenal) | Auditoria da branch em repositório próprio e comparação de métricas antes da integração. | G0/G1 |

## Formato mínimo de um resultado

Identificador da experiência, commit SHA, hipótese, dataset ou gerador, seed, parâmetros, ambiente (OS/runtime/deps), baselines, comando, resultados brutos, métrica/IC, limitações, decisão, autor/revisor e localização dos artefatos. **Não substituir** resultados antigos: produzir nova versão.

## Critérios de segurança e integridade

- Mudanças de ciência ficam em branch + PR; CI deve passar antes de qualquer merge.
- Trabalhos em produção requerem testes de regressão, smoke público e plano de rollback próprio do serviço.
- Manter APIs, páginas, routes e scripts existentes intactos nesta etapa; não publicar alterações do portal só porque o catálogo mudou.
- O catálogo é status documental. A confirmação de funcionamento real depende dos testes de cada módulo.
- Diferenciar demos (toy crypto, simulations, heuristics) de aplicações ou validações profissionais.

## Questões abertas

1. Quais branches de pesquisa foram revisadas e incorporadas à main de forma reproducível?
2. Quais números de experimento possuem notebooks/dados/testes mas não resultados reexecutáveis?
3. Como coletar métricas de desempenho sem dados pessoais ou telemetria sensível?
4. Como comparar variação por seeds e ambiente antes de afirmar melhorias?

**Próximo marco:** Science 0.2 pode iniciar benchmarks específicos, **após** baseline e portões G0/G1 verificados.
