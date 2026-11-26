# Arquitetura integrada

| Componente | Responsabilidade | Entrada e saída |
| --- | --- | --- |
| AEGIS | Validar formato, política e autenticidade | JSON limitado a 64 KiB → mudança autenticada com geração esperada |
| ATLAS | Serializar alterações, verificar a revisão ativa e registrar a próxima | Revisão ativa + mudança → nova revisão persistida |
| PHOENIX | Verificar uma revisão anterior e reaplicar seu conteúdo | Geração ativa esperada + geração de origem → nova revisão com referência à origem |

`apply` autentica o envelope antes de abrir a transação. Na transação, ATLAS carrega e verifica a revisão ativa, compara a geração esperada e insere a próxima revisão. Cada inserção comitada vira a revisão ativa por ordem de geração. `restore` segue o mesmo controle de concorrência, verifica a autenticidade da revisão de origem e registra os valores recuperados em uma geração nova. `status` só entrega a revisão ativa após a verificação de autenticidade.

## Fronteira de confiança

O operador local e a chave de 32 bytes formam a fronteira de confiança. Quem tem a chave pode produzir mudanças e revisões autenticadas. O HMAC de cada revisão cobre geração, política, ação e origem. A geração esperada bloqueia reenvio após uma alteração e impede que duas operações baseadas na mesma revisão sejam aceitas. A chave deve ser exclusiva da instância para manter esse controle dentro da instância correta.

A proteção do banco e dos caminhos depende das permissões do sistema operacional. A autenticação de uma revisão individual detecta adulteração de seu conteúdo. Um invasor com escrita no banco pode apagar revisões ou substituir o arquivo por uma cópia antiga válida. A detecção de truncamento e a recuperação após perda do banco exigem uma âncora externa e backup verificado.

## Falhas operacionais

- **Interrupção durante a gravação.** O journal do SQLite descarta a transação incompleta na próxima abertura.
- **Concorrência.** Um escritor por vez. A operação espera até dois segundos pelo bloqueio. Após erro ou saída incerta, consulte `status` para distinguir conflito de geração de transação recuperada.
- **Falha de autenticidade.** Uma revisão ativa inválida impede leitura e mutação. Uma origem inválida impede a restauração daquele conteúdo.

## Serviço consumidor

O serviço TCP vincula-se a `127.0.0.1` e consulta a revisão autenticada a cada admissão. Modo de manutenção recusa novas sessões. O limite se aplica às sessões simultâneas ativas daquele processo. Alterações e recuperação afetam as próximas admissões. Sessões já aceitas podem concluir sua troca `PING`/`PONG`, com prazo de dois segundos para leitura. Estado indisponível produz recusa de novas sessões. O serviço usa códigos numéricos 200, 429 e 503 em mensagens JSON delimitadas por linha sobre TCP.
