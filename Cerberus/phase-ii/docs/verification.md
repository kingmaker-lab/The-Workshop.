# Evidência local · 26/11/2026

Debian 13.6, Python 3.13.5 e SQLite 3.46.1. Suíte executada sem dependências Python externas.

```text
$ python3 -m unittest discover -s tests -v
Ran 10 tests in 8.695s
OK
```

| Cenário | Resultado observado |
| --- | --- |
| Sessões TCP reais em loopback | Capacidade produziu 429, manutenção produziu 503, restauração reabriu admissões e adulteração da revisão fechou o serviço para novas sessões. |
| Aplicar e restaurar pelo CLI | A geração 1 recebeu a política nova e a geração 2 recuperou os valores da geração 0 com referência à origem. O envelope original foi recusado após a recuperação. |
| Dois processos aplicando a mesma geração | Uma aplicação foi confirmada e a outra recebeu erro de geração. |
| SIGKILL entre INSERT e COMMIT | O processo recebeu SIGKILL durante a operação real. A geração 0 permaneceu ativa, e a nova tentativa confirmou a geração 1. |
| Bloqueio de escrita | O CLI retornou erro ao expirar a espera. Após liberar o bloqueio, a alteração foi confirmada. |
| Envelope adulterado | A alteração foi recusada e a revisão ativa foi preservada. |
| Revisão ativa adulterada | A consulta e a aplicação foram recusadas, e o banco manteve uma única revisão. |
| Origem de recuperação adulterada | A recuperação foi recusada e a revisão ativa foi preservada. |
| JSON inválido ou acima do limite | O CLI recusou chaves duplicadas, UTF-8 inválido, JSON truncado, tipo incorreto e entrada acima do limite. |
| Permissões da chave | A geração de chave preservou o arquivo existente, e a leitura recusou uma chave com acesso de grupo ou terceiros. |

O exemplo do README também foi executado em um diretório temporário. O comando final retornou:

```json
{"action": "restore", "generation": 2, "policy": {"maintenance": false, "max_connections": 100}, "source": 0}
```
