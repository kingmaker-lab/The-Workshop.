# EXP-002 · Process Lifecycle

**Pilar Alnilam / Build.** Demonstra criação e observação de um processo filho Ruby autorizado.

```sh
ruby bin/orion process list
ruby bin/orion process run 002 --timeout 5 --json
```

Experimente reduzir `--timeout` para `0.1` e aumentar o tempo do `sleep` no worker **somente em ambiente de laboratório**. Compare status, saída, duração e código de término. A ferramenta usa temporizadores monotônicos e encerra filhos que ultrapassam o tempo permitido. Não é um sandbox.
