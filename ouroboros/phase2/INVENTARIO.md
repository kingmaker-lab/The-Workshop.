# Inventário em 26 de novembro de 2026

O [The-Workshop.](https://github.com/kingmaker-lab/The-Workshop.) é o repositório confirmado pelo GitHub. A variante sem ponto devolveu 404 ao conector. A busca de repositórios por Ouroboros no proprietário não retornou resultados. A cópia local `The Workshop/workshop-source` contém as referências remotas e o histórico. A fotografia local de `origin/main` é `7bf3c226fc8e21de5d741cc25f1620d86f43a41b`. Ela contém EXP-004–007 e o relatório JSON de EXP-014. O [ramo de consolidação](https://github.com/kingmaker-lab/The-Workshop./tree/34f98b19429070ab817c79bfc205d087cb62d3dd/research/cryptography/ouroboros-low-level) contém as fontes EXP-004–014. O GitHub devolveu o blob `4e28e7cf658a7ef7f5bda756505194768359fd51` para o Feistel nessa revisão.

| Registro | Evidência localizada |
|---|---|
| EXP-001 | Registro conceitual no portal. Demonstração algébrica da reversibilidade Feistel para bloco de 64 bits. Código original autônomo pendente. |
| EXP-002 | Registro teórico no portal. Diferencial de probabilidade 1 para uma função ARX de 32 bits. Código original autônomo pendente. |
| EXP-003 | Registro metodológico e equações da DDT ARX de 8 bits no portal. O EXP-007 reutiliza a função em seu controle. Artefato autônomo da campanha original pendente. |
| EXP-004 | Código e relatório de ciclos em SHA-256 truncado. |
| EXP-005 | Código, testes e relatório de sensibilidade ao estado inicial. |
| EXP-006 | Código, testes e relatório de bacias de atração. |
| EXP-007 | Código, testes e piloto SAC/BIC, com controles. |
| EXP-008 | Especificação, Feistel Python, testes e três relatórios por chave. |
| EXP-009 | Testes e tabelas diferenciais e lineares completas da função de rodada. |
| EXP-010 | Código, testes e resultados para até oito rodadas em recortes de peso um. |
| EXP-011 | Código e testes de trilhas e hulls, com validação exata selecionada. |
| EXP-012 | Código e testes da transição e das estatísticas amostrais da agenda KS1. |
| EXP-013 | Código, testes e resultados de dependência de chaves. O registro histórico condiciona a recuperação de preimagem ao conhecimento da agenda interna de oito bytes. |
| EXP-014 | Oráculo, 25 vetores, regressões e [registro de evidências e CI](https://github.com/kingmaker-lab/The-Workshop./blob/34f98b19429070ab817c79bfc205d087cb62d3dd/research/cryptography/ouroboros-low-level/experiments/014-research-consolidation/results/research_evidence_register.json). O histórico documenta 327.680 comparações. |

O [arquivo histórico do WolfPack Crypto Lab](https://github.com/kingmaker-lab/The-Workshop./blob/08db9bb7b0b14df4a5ba10066e71355c7e80a6f2/sites/wolfpack-crypto/worker.mjs) preserva as rotas `/experimentos/001/`, `/experimentos/002/` e `/experimentos/003/`. Elas descrevem um modelo Feistel e funções ARX anteriores ao Feistel reduzido do EXP-008. Os EXP-001–003 de blockchain em `web/crypto-lab` pertencem a outra série. O histórico também contém um gitlink chamado `The Ouroboros Project ` (espaço final) para `f9c7e3d212238f26d3650603090b7a3a01baf546`. A listagem do backup tar local não trouxe arquivos com nomes Ouroboros/Feistel. O conteúdo do gitlink segue como lacuna. O bundle local do Workshop foi identificado como cópia de preservação, sem restauração sobre a árvore atual. O registro histórico de CI foi lido como evidência declarada no repositório.

A pasta `baseline/` contém cópias exatas da fonte EXP-008 e do oráculo e vetores EXP-014 da revisão acima. Os arquivos originais e seus commits ficam no Workshop.
