# LIMIAR · CERBERUS FASE II

Serviço local de controle de configuração operado por CLI. AEGIS valida e autentica mudanças, ATLAS registra e ativa cada revisão, e PHOENIX restaura uma configuração anterior como nova revisão. Os três componentes compartilham o mesmo fluxo e o mesmo banco SQLite.

Este primeiro incremento controla uma política com `maintenance` e `max_connections`. O comando `status` publica o estado efetivo em JSON. O comando `serve` aplica a política a sessões TCP reais em `127.0.0.1`.

## Executar no Debian

Requer Python 3 e seu módulo SQLite. Validado no Debian 13 com Python 3.13, sem dependências Python externas e sem serviços de rede. Execute da raiz do projeto.

```sh
python3 -m unittest discover -s tests -v
```

Para operar com dados descartáveis, execute em Bash:

```bash
(
  set -e
  umask 077
  state_dir=$(mktemp -d)
  trap 'rm -rf -- "$state_dir"' EXIT
  cerberus() {
    python3 -m cerberus --key "$state_dir/operator.key" --db "$state_dir/state.sqlite" "$@"
  }

  cerberus keygen
  cerberus init
  printf '%s\n' '{"maintenance":true,"max_connections":200}' > "$state_dir/policy.json"
  cerberus seal --expected 0 "$state_dir/policy.json" > "$state_dir/change.json"
  cerberus apply "$state_dir/change.json"
  cerberus restore --expected 1 0
  cerberus status
)
```

O estado final deve ter geração 2, ação `restore`, origem 0 e política `{"maintenance":false,"max_connections":100}`. Gere uma chave separada por instância e mantenha banco, chave e arquivos de operação em um diretório privado.

Para iniciar o consumidor, execute `python3 -m cerberus --key operator.key --db state.sqlite serve` depois de inicializar o banco. A porta padrão é 8765. Use `--port 0` para deixar o sistema escolher uma porta livre. O servidor anuncia o endereço em JSON. Um cliente recebe o resultado da admissão e, quando admitido, pode enviar `PING` seguido de quebra de linha para receber `PONG`.

- [Arquitetura e fronteira de confiança](docs/architecture.md)
- [ADR 001 · Uma transação por revisão](docs/adr/001-estado-transacional.md)
- [ADR 002 · Autenticação local e controle de geração](docs/adr/002-autenticacao-local.md)
- [Backlog e critérios de aceite](docs/backlog.md)
- [Histórico e integração GitHub](docs/history.md)
- [Evidência local](docs/verification.md)
- [Modelos executáveis em Assembly, Java e Pascal](models/README.md)
