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


## v0.4 — Sigma subset / Detection Engineering (opt-in)

O ARGUS passa a executar **um subconjunto rigorosamente limitado do formato
Sigma**, sobre eventos já normalizados pelo motor. **Não** é o pySigma nem
um conversor geral de regras Sigma; regras de outras plataformas não podem
ser importadas sem revisão e mapeamento explícito. A especificação original:
https://github.com/SigmaHQ/sigma-specification/blob/main/specification/sigma-rules-specification.md

A integração é **desativada por padrão** em `argus/config.yaml`. O motor
anterior de regras YAML, correlação, Welford, `watch`, alertas e a API local
continuam funcionando. Quando ativada, uma detecção Sigma é adicionada
às demais detecções do evento e contribui para o score de risco.

### Experimento reproduzível

```sh
# Validação estática do conjunto de regras, sem criar banco:
python -m argus.main sigma-validate --rules-dir argus/sigma/rules

# Ative SOMENTE via arquivo de configuração de demonstração:
python -m argus.main --config argus/config-sigma-demo.yaml analyze \
  argus/samples/ssh_bruteforce.jsonl --db /tmp/argus-sigma-demo.db

# O fluxo contínuo aceita a mesma configuração:
python -m argus.main --config argus/config-sigma-demo.yaml watch \
  argus/samples/ssh_bruteforce.jsonl --db /tmp/argus-sigma-watch.db --once
```

### Subconjunto suportado

- Um YAML de regra por arquivo `.yml` ou `.yaml`, até **32 arquivos**,
  até **32 KiB por arquivo**, apenas diretório local sem subpastas.
  A leitura rejeita symlinks de regra, aliases/anchors YAML, chaves
  duplicadas, arquivos excessivos e identificadores duplicados.
- `title`, `id` opcional, `level` (`low/medium/high/critical`),
  `logsource` e `detection`. O `logsource` aceito deve ter **exatamente**
  `product: argus` e `category: authentication` ou
  `category: network_connection`. É um mapeamento **específico** da
  taxonomia normalizada ARGUS; não equivale a qualquer fonte Linux/Zeek
  arbitrária.
- Seletores como mappings (campos ligados por AND), listas de mappings
  (OR), valores escalares e listas de alternativas (OR).
  Os campos reconhecidos são `User`, `Result`, `SourceIp`,
  `Source`, `Message`, `Service`, `Protocol`,
  `DestinationIp`, `DestinationPort`, `OrigBytes`,
  `RespBytes` e `Duration`; qualquer campo não mapeado gera erro.
- Condições booleanas `and`, `or`, `not` e parênteses; referências
  a seletores existentes e `1 of them`, `all of them`,
  `1 of selection_*` ou `all of selection_*`. Um seletor
  positivo é obrigatório para evitar filtros isolados muito amplos.
- Comparação exata com strings case-insensitive; modificadores
  `|contains`, `|startswith`, `|endswith` em strings.
  Tipos numéricos são comparados sem coerção. Limites de valores,
  seletores e tamanho de expressão protegem o avaliador.

**Não suportado, com rejeição explícita:** curingas em valores (`*`, `?`),
regex, transformações base64, `|all`, `|exists`, `|cidr`,
thresholds/count/aggregation, correlações Sigma, timeframes, condições
referenciando nomes ausentes e outros modificadores. Também não há
ingestão pública de regras. A carga e a execução são locais.

A regra de exemplo em
`argus/sigma/rules/lnx_argus_privileged_auth.yml` observa uma
autenticação privilegiada de demonstração e exclui o loopback. É uma
regra educacional e **não** prova exploração ou comprometimento.

### Limites conhecidos

- A classificação de origem usa a categoria normalizada do evento.
  O subset não confirma que o evento corresponde a uma fonte Linux/Zeek
  real, nem que uma regra comunitária Sigma traduz corretamente.
- A validação ocorre na inicialização. Modificar arquivos enquanto o
  programa está rodando **não** atualiza as regras automaticamente.
- A pontuação se soma às regras existentes, podendo produzir mais
  alertas e falsos positivos. Requer revisão humana das regras e testes
  com amostras benignas e suspeitas, antes de qualquer uso operacional.
- Dependências continuam limitadas à biblioteca Python e PyYAML já
  utilizada pelo ARGUS; não há download de regras durante a execução.
- Nenhuma mudança autoriza tornar a API não autenticada pública.
