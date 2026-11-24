# Ruby Orion v0.2 · Alnilam

## Contrato público

- `orion process list [--json]`: apresenta tarefas cadastradas do tipo `process`.
- `orion process run 002 [--timeout N] [--json]`: executa somente o worker local EXP-002.
- `orion ipc demo [--timeout N] [--json]`: envia mensagem JSON `orion-ipc/1` ao worker local EXP-003.
- Retornos: `0` sucesso, `1` falha do worker ou verificação negativa, `2` erro de entrada/uso, `124` timeout.
- O timeout é de 5 s por padrão, entre 0,1 s e 30 s.

## Versões suportadas

O piso de distribuição passa a Ruby **3.3+**. Para execução em sistemas reais, utilizar patch de segurança atual de uma série oficialmente mantida. O suporte a Windows precisa ser validado no CI; no Windows o supervisor encerra apenas o filho direto, não um grupo de processos.

## Modelo de execução

Processos filhos são invocados por caminho Ruby absoluto e arquivo de tarefa **cadastrado em código**, sem shell. O processo recebe ambiente reduzido, diretório de trabalho do Orion e descritores explícitos. No POSIX é criado um grupo de processos dedicado para encerramento em timeout; no Windows o encerramento está restrito ao processo direto. Limites: 8 KiB de entrada, 32 KiB por fluxo de saída, 4 KiB por frame IPC. Saída excedente é drenada e descartada para evitar deadlock por buffer cheio. O código usa relógio monotônico e recolhe o estado do processo filho.

**A ferramenta não é uma sandbox.** Não há limites rígidos de CPU, RAM, disco, syscalls ou criação de processos. Não usar com código não confiável nem anexar a endpoints remotos. Somente os scripts dos laboratórios mantidos no repositório devem ser executados pela CLI.

## Protocolo IPC v1

```json
{"protocol":"orion-ipc","version":1,"type":"request","payload":{"values":[8,13,21]}}
```

Todo frame é um objeto JSON seguido por `\n`, com chaves exatas `protocol`, `version`, `type`, `payload`, UTF-8 válido, até 4096 bytes e profundidade máxima de 16 níveis. Tipos: `request`, `response`, `error`. Payload deve ser um objeto.

## Testes de estabilidade

- Comandos e testes legados da v0.1.
- Sucesso, erro não zero, timeout, truncamento de saída, argumento inválido, e limite de stdin.
- Mensagens JSON inválidas, versão incorreta, frame excessivo, ausência de newline e payload fora do contrato.
- Teste de integração com subprocessos locais reais e coleta de estado.

## Limitações

A limpeza de descendentes no POSIX depende de grupos de processos; processos que criem sessões independentes podem escapar, logo **não executar árvores arbitrárias de processos**. A versão inicial evita persistência, serviços de rede e execução de comandos fornecidos pelo usuário. Os limites de tempo não substituem cgroups, quotas e isolamento de sistema operacional.
