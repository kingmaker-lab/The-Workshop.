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

Os limites ficam em `config.yaml` e as regras em `rules/default.yaml`. A baseline
Welford em `detection/anomaly.py` e uma base pequena para a futura camada de
anomalias; ainda nao participa do score padrao.

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
