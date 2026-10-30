# The Workshop | Cronograma público de novembro a dezembro de 2026

**Versão:** 1.0
**Planejado em:** 30 de outubro de 2026
**Janela:** 02/11 a 27/12/2026 (oito semanas)
**Publicação:** https://workshop-news.pages.dev/#cronograma

> Este é um planejamento de trabalho, não um anúncio de disponibilidade de produtos. As datas são estimativas e o status de cada etapa só deve mudar depois de evidência registrada.

## Prioridades e janelas de entrega

| Semana | Período | Projeto prioritário | Critério de conclusão (Definition of Done) | Situação inicial |
|---|---|---|---|---|
| WK01 | 02–08 nov | Security Release Gate | CI aprovado, CSP/rotas verificadas, revisão PR #10 e riscos registrados | PLANEJADO |
| WK02 | 09–15 nov | Protocolo Ruby | Staging read-only e demo inofensiva verificados; sem upload ou execução de amostras | PLANEJADO |
| WK03 | 16–22 nov | ARGUS / HeartAI | Testes de runtime/memória/tokenizer reproduzíveis; documentar métricas e limites | PLANEJADO |
| WK04 | 23–29 nov | Cerberus 02 | Contratos para adaptadores SQLite/memória validados; trade-offs documentados | PLANEJADO |
| WK05 | 30 nov–06 dez | Ouroboros EXP-008 | Análise reprodutível de round function e key schedule além dos dados SAC iniciais | PLANEJADO |
| WK06 | 07–13 dez | WolfPack OS / Jogos | Protótipo testado de sequência didática para iniciantes em navegador | PLANEJADO |
| WK07 | 14–20 dez | Workshop News | Estabilidade das fontes, notícias editoriais revisadas, links e status auditáveis | PLANEJADO |
| WK08 | 21–27 dez | Integração e retrospectiva | Registros de decisões, pendências e prioridades para o primeiro ciclo de 2027 | PLANEJADO |

## Dependências e restrições

- **Segurança precede publicações**: mudanças em produção exigem verificação de testes, riscos e cabeçalhos, além de um caminho reversível.
- **Protocolo Ruby**: o código para Render é prova de staging. Não divulgar como ingestão real de malware; os endpoints atuais são exclusivamente GET e demonstrativos.
- **ARGUS / HeartAI**: memória e tokenizer não implicam a existência de um LLM autoral treinado; experimentos neurais exigem avaliação específica.
- **Cerberus 02**: demonstrador arquitetural com CLI/controlador JSON, não servidor HTTP do experimento.
- **Ouroboros EXP-008**: cifra didática Feistel com bloco de 16 bits. Nunca apresentar resultados de difusão como comprovação de segurança criptográfica.
- **WolfPack OS**: jogos educativos gratuitos para iniciantes; apps Android/iOS permanecem objetivos futuros, sem lançamento nesta janela.
- **Workshop News**: publicação Cloudflare Pages usa Direct Upload, e o PR #11 permanece em revisão. Um commit GitHub não publica automaticamente a alteração.

## Gate de publicação transversal

1. Evidência técnica: testes automatizados, documentação e escopo explícito.
2. Threat modeling e riscos residuais registrados conforme docs/SECURITY_RELEASE_GATE.md.
3. Verificação de preview e ambiente publicado: rotas, integrações, CSP, erros 404/405 e disponibilidade.
4. Identificar PLANEJADO, EM ANDAMENTO, VALIDADO ou ADIADO somente após revisão. Evitar declarar VALIDADO com base apenas em commits.
5. Referenciar commit, issue/PR, relatório ou experimento reproduzível.

## Ritual proposto

- **Sexta-feira**: checagem curta dos critérios e dos riscos. Atualizar status somente com evidências.
- **Fim de sprint**: nota de trabalho entregue ou justificativa do que precisou mudar.
- **Após WK08**: retrospectiva, priorização e nova versão do cronograma para 2027.

**Governança:** datas, prioridades e escopo podem ser replanejados. A equipe não tem proprietários de tarefas atribuídos neste documento e a publicação não configura compromisso contratual.

*Build. Break. Understand. Rebuild.*
