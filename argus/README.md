# ARGUS

ARGUS e um mecanismo defensivo local de threat hunting. Ele normaliza logs,
aplica regras deterministicas, correlaciona eventos por IP em janelas temporais,
calcula risco acumulado e persiste eventos/alertas em SQLite.

## Configurar e executar

Use o Python selecionado para o projeto e instale a unica dependencia:

```sh
python -m pip install -r argus/requirements.txt
python -m argus.main analyze argus/samples/ssh_bruteforce.jsonl
python -m argus.main timeline --src-ip 192.168.1.50
python -m argus.main serve
```

A API fica restrita a `127.0.0.1:8765` por padrao:

- `GET /health`
- `GET /alerts?limit=100`
- `GET /timeline?src_ip=192.168.1.50&limit=500`

O banco `argus.db` e criado no diretorio do projeto. Para logs locais, use
`--format jsonl`, `--format syslog` ou `--format network` (Zeek conn.log em JSONL).
O modo `auto` trata `.log`/`.syslog` como syslog e outros arquivos como JSONL.

## Deteccoes iniciais

- Uma falha de autenticacao isolada nao cria alerta.
- 15 falhas do mesmo IP em 30 segundos criam deteccao de brute force.
- Um login bem-sucedido apos esse limiar aumenta o risco acumulado.
- O mesmo IP observado em outra fonte adiciona uma deteccao de correlacao.
- Regras YAML podem identificar eventos especificos, como autenticacao bem-sucedida
  para `root`.

Os limites ficam em `config.yaml` e as regras em `rules/default.yaml`. A baseline Welford em `detection/anomaly.py` alimenta a camada estatistica
experimental v0.2 (`detection/anomaly_engine.py`), desligada por padrao. Quando
ativada, suas deteccoes entram no score de risco.

## Testes

```sh
python -m unittest discover -s argus/tests -v
```
## Comportamento e limites da API

O motor emite um alerta de brute force por sequencia ativa de falhas do mesmo
IP. Novos alertas desse tipo sao possiveis quando a janela anterior expira ou
apos a sequencia ser encerrada por um login bem-sucedido. Para evitar ruído,
falhas adicionais enquanto o limiar ja esta ativo nao geram alertas repetidos.

A API e somente leitura e vincula-se ao loopback por padrao. Os limites de
`/alerts` devem estar entre 1 e 500, e os de `/timeline` entre 1 e 2000;
valores invalidos retornam HTTP 400 em vez de serem truncados silenciosamente.
Respostas JSON usam `Cache-Control: no-store`. Como eventos podem conter
informacoes sensiveis, **nao exponha a porta da API na Internet** sem
autenticacao, controle de acesso e revisao de seguranca adicionais.

Os testes de regressao do ARGUS estao em
`.github/workflows/argus-tests.yml`, com verificacoes de API, deteccoes e
execucao basica pela CLI.

## v0.2 — Anomalias estatisticas (experimental)

O ARGUS agora pode observar metricas numericas de `network_connection`
(`orig_bytes`, `resp_bytes` e `duration`) e emitir uma deteccao quando
um valor supera o limiar de desvios padrao de sua baseline Welford.
A baseline e mantida por par **source + metrica** no processo atual.

O recurso fica **desativado por padrao**. Para experimentar, configure
`anomaly.enabled: true` em `argus/config.yaml`; os padroes sao 20
amostras de aquecimento e limiar `z_threshold: 4.0`. O score da deteccao e
25 e a severidade e `medium`. Cada metrica e avaliada antes de atualizar
a baseline. Numeros negativos, nao finitos e nao numericos sao ignorados.

Exemplo de entrada Zeek (`--format network`):
```json
{"ts": 1793400000, "id.orig_h": "192.0.2.10", "orig_bytes": 1048576}
```

**Limitacoes**: detecta desvios estatisticos, nao confirma ataque.
Dados artificiais, baseline contaminada, variacao legitima de trafego,
alteracao de fontes, drift e grandes volumes podem gerar falso positivo.
A baseline e reiniciada a cada invocacao, nao e persistida nem treinada
entre sessoes. Avalie resultados com supervisao humana.

## Laboratorio publico

A pagina [ARGUS / Workshop Labs](https://workshop-labs.pages.dev/argus/)
apresenta arquitetura, regras, um cenario sintetico de 17 eventos e 3 alertas,
exemplos de telemetria, comandos locais, limites de seguranca e roadmap. E uma
vitrine estatica sem coleta de logs ou API remota. O motor executa apenas no
ambiente Python escolhido pelo pesquisador.


## v0.3 — Ingestão contínua local (experimental)

O comando `watch` acompanha um arquivo de log **local e confiável**, sem
expor portas ou enviar dados. A cada ciclo, ele processa apenas linhas
terminadas por quebra de linha, com limite de bytes e tamanho do lote.
O cursor de leitura é armazenado em `stream_checkpoints`, no SQLite
**junto** aos eventos e alertas de cada linha, na mesma transação.

Use a partir da raiz do repositório:

```sh
# Arquivo de exemplo: processar uma rodada de até 100 linhas.
python -m argus.main watch argus/samples/ssh_bruteforce.jsonl \
  --format jsonl --db ./argus-watch.db --batch-size 100 --once

# Executar novamente: não reprocessa as linhas já confirmadas.
python -m argus.main watch argus/samples/ssh_bruteforce.jsonl \
  --format jsonl --db ./argus-watch.db --batch-size 100 --once

# Acompanhar um arquivo de teste crescente (Ctrl+C para encerrar).
python -m argus.main watch ./local-auth.log \
  --format syslog --db ./argus-watch.db --poll-interval 0.5
```

Suporta `--format jsonl`, `syslog`, `network` (Zeek JSON conn.log) e
`auto`; a detecção usa o mesmo motor de regras, correlação e score da
análise em lote. `--from-end` ignora o conteúdo preexistente **somente**
quando ainda não existe checkpoint para o arquivo. Ao retomar, usa o
cursor previamente confirmado.

### Limites e persistência

- **Limites padrão:** 65.536 bytes por linha, 200 linhas por polling,
  50.000 linhas completas por execução; o watcher termina ao atingir esse
  limite para conter o estado de correlação mantido em memória.
  Os limites podem ser ajustados com `--max-line-bytes`, `--batch-size`
  e `--max-lines`, dentro dos tetos de segurança.
- O modo `watch` exige banco SQLite persistente e obtém um lock local
  `.stream.lock` para impedir dois seguidores concorrendo pelo mesmo banco.
- Arquivos simbólicos, pipes e dispositivos são rejeitados. Arquivos
  ausentes são tolerados para permitir o aparecimento posterior do log.
  Linhas parciais aguardam conclusão e linhas acima do limite interrompem
  a leitura sem avançar o cursor. Registros inválidos completos são
  descartados e o descarte é confirmado, sem publicar seu conteúdo no stderr.
- Rotação por troca de inode e truncamento detectado fazem o cursor voltar
  para zero, com **geração** persistida para evitar colisão de IDs entre
  épocas. A detecção de truncamento depende de o tamanho observado ser
  menor que o offset confirmado; um arquivo truncado e preenchido
  inteiramente **entre dois polls** pode passar despercebido.
- Checkpoints e dados processados são transacionados; **não há garantia
  de exactly-once para o efeito da correlação em memória**, nem persistência
  de suas janelas, scores ou baselines. Reiniciar o processo limpa esses
  estados; eventos anteriores não são reprocessados para reconstruí-los.
- Arquivos fonte, diretórios, banco e lock devem ser controlados pelo
  operador local. A leitura é limitada por linha, mas o ARGUS ainda não
  possui políticas completas de retenção, controle de cardinalidade de
  fontes, proteção contra alterações simultâneas de conteúdo ou auditoria
  de permissões do caminho inteiro. **Não use como SIEM de produção.**
- Evite executar o watcher como root. Conceda apenas permissão de leitura
  no arquivo monitorado e escrita no diretório de dados protegido.

A página pública `/argus/` apresenta o recurso e exemplos, mas **não**
executa o watcher em Cloudflare. Próxima pesquisa proposta: subconjunto de
regras Sigma com mapeamento de campos e validação rigorosa.
