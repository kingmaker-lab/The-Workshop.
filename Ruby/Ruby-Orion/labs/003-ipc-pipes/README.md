# EXP-003 · IPC Pipes

**Pilar Alnilam / Build.** Um processo Ruby pai envia uma mensagem JSON delimitada por newline, e um processo filho responde usando pipes STDIN/STDOUT.

```sh
ruby bin/orion ipc demo --json
```

O contrato `orion-ipc/1` limita frames a **4 KiB**, valida nome, versão, tipo e payload. O demo soma valores definidos no programa, sem aceitar código arbitrário do visitante. Modifique localmente a lista de inteiros para testar limites. Não há sockets ou escuta de rede.
