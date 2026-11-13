# 🔬 Protocolo Science 0.1 | The Workshop

> Baseline inventariada em **2026-11-13** a partir do GitHub. Atualização **aditiva**, sem modificar algoritmos, dados, APIs, rotas, Workers, CI existente ou deploys.

O Protocolo Science é uma disciplina de pesquisa, **não** um mecanismo para declarar automaticamente software seguro, pronto ou cientificamente validado. O catálogo abaixo representa caminhos e documentação examinados, não uma auditoria de resultados.

## Diretório

- `catalog.json`: inventário legível por máquinas. Origem do relatório de status.
- `validate.py`: valida esquema básico, IDs, caminhos do próprio repo e documentação; não executa os projetos.
- `tests/test_validate.py`: regressões do verificador.
- `ROADMAP.md`: decisões, lacunas e prioridades de pesquisa.
- `templates/EXPERIMENT.md`: modelo para novos experimentos.

## Como usar

Na raiz do repositório:

```sh
python3 science/validate.py
python3 -m unittest discover -s science/tests -v
python3 science/validate.py --format markdown
python3 science/validate.py --format json
```

Esses comandos não alteram as pesquisas nem criam serviços. As suítes específicas de cada laboratório continuam nos locais e workflows originais e **não são substituídas** por esta validação.

## Portões de maturidade científica

| Gate | Requisito para avançar |
| --- | --- |
| G0: Inventário | Dono técnico, código/branch, limites e próxima hipótese conhecidos. |
| G1: Reproduzível | Parâmetros, entradas sintéticas/públicas, seed, ambiente, comando, testes e artefatos identificados. |
| G2: Mensurável | Baseline, métricas, distribuição de resultados, margem de incerteza e custo publicados. |
| G3: Comparável | Réplicas independentes, controles negativos, possíveis vieses e análise de erros. |
| G4: Publicável | Revisão, segurança, privacidade, controle de versão, rollback e licença aplicável. |

**A presença de um teste não significa G1 concluído.** Resultados só devem ser declarados após reprodução documentada e verificável.

## Regras de compatibilidade

1. Acrescentar, não sobrescrever: cada experimento possui pasta/identificador próprio e registros versionados.
2. Não apagar snapshots, pesos, corpora sintéticos, resultados ou rotas preexistentes; se for inevitável migrar, documentar backup e rollback.
3. Seeds e dados devem ser estáveis/registrados; para benchmarks, declarar versões do compilador/runtime e ambiente.
4. Hipóteses, métricas observadas e conclusões são campos distintos; não extrapolar segurança a partir de cifras reduzidas, PoCs ou simulações.
5. Nenhum token, segredo, log pessoal ou dado infantil entra nos experimentos públicos. Para segurança, usar somente amostras autorizadas/sintéticas.
6. Atualização científica não publica automaticamente na Cloudflare, Render, Vercel ou dispositivos móveis.

## Escopo atual

O catálogo acompanha 11 trilhas versionadas na branch principal e aponta o NEXUS como trilha externa do The Arsenal. O Protocolo Ruby tem fontes históricas na main e backend em outra branch; isso é uma divergência a investigar, não um merge já realizado.

Para a matriz de lacunas e os critérios de aceite, consulte [ROADMAP.md](ROADMAP.md).

**Build. Break. Understand. Rebuild.**
