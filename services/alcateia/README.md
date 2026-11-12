# Alcateia — infraestrutura própria, fase 1

Runtime independente para Heart, Fake, Argus e Blade. Um processo mantém quatro
conexões Gateway e decide qual personagem responde. Não depende do camelBots.
**A migração de produção ainda não aconteceu.** Este diretório não altera o
Worker antigo de `web/workshop-discord` nem os bots hospedados no camelBots.

## Implementado

- Quatro identidades, personalidades e credenciais independentes. Somente o ID
  do criador configurado é tratado como pai; apelido não autentica ninguém.
- Nome, menção e resposta a bot; participação espontânea opcional com roteador
  conservador. Um destinatário por mensagem, deduplicação persistente e limite
  de 3 intervenções/15 min por canal, com 2 min entre intervenções da alcateia.
- Argus responde a dúvidas técnicas. O modelo não executa comandos nem navega.
- Presença real do Discord alternada a cada 15 minutos com frases revisadas.
- Preferências estruturadas por bot + servidor + pessoa; consulta efêmera via
  `/alcateia estilo`. Exclusão remove valores e mantém somente opt-out mínimo.
- TTL de 90 dias desde a última atualização. Sem histórico persistente de texto.
- Limite diário de chamadas à IA (100 por padrão, somado aos quatro), entrada de
  até 2.000 caracteres e saída limitada. O limite não é um orçamento monetário;
  configure também orçamento no provedor. Falhas consomem a reserva da chamada.
- Banco SQLite em WAL, lock de processo, encerramento por SIGTERM e logs de
  contadores/tipos de erro sem mensagens, respostas, tokens ou IDs de usuários.
- Standby por padrão: não conecta ao Discord e não chama IA.

## Limites deliberados da fase 1

Não há fine-tuning, treinamento neural contínuo, RAG, notícias ao vivo, execução
de código, chat por DM, memória autobiográfica ou conversa entre bots. O modelo
recebe somente a mensagem atual e preferências da própria pessoa. Isso evita
contexto cruzado, mas não oferece continuidade de diálogo nesta primeira etapa.
O roteador inicial é por padrões; textos ambíguos ficam sem intervenção.

**Os jogos do camelBots, comandos antigos e dados de produção não foram portados.**
Não desative a hospedagem antiga antes da migração de paridade e dos testes no
Discord. A Heart atual usa o app compartilhado do camelBots: será necessário
um aplicativo Discord próprio para ela (ou confirmar que você já criou um).

## Testar localmente sem segredos

Requer Python 3.12 ou 3.13. Dependências fixadas com hashes em `requirements*.txt`
e `uv.lock`. `uv sync --frozen` é alternativa à instalação abaixo.

```sh
python -m venv .venv
. .venv/bin/activate
pip install --require-hashes -r requirements-dev.txt
ruff check alcateia tests
pytest -q
python -m alcateia --check
python -m alcateia  # standby; Ctrl+C encerra
```

`.env.example` documenta os nomes, mas não é carregado automaticamente.
Configure as variáveis pelo ambiente ou pelo painel de hospedagem. Não coloque
credenciais em comandos de chat, commits, screenshots ou arquivos rastreados.

## Implantação no Render

Workspace confirmado: **The Workshop**. Blueprint separado em
`services/alcateia/render.yaml`, serviço novo `workshop-alcateia`, Oregon,
uma instância `0.5c-512mb`, disco de 1 GB em `/var/data`, auto-deploy desligado.
Não altera `protocolo-ruby-api` nem outros serviços. Ao criar o Blueprint,
selecione este caminho (o repositório não possui Blueprint na raiz).

Referência consultada em 04/11/2026: US$7/mês de compute + US$0,25/mês por 1 GB
de disco. Total base aproximado **US$7,25/mês**, excluindo IA, impostos, tráfego
adicional e eventuais custos do workspace. Confirme o total no painel antes de
aplicar: https://render.com/pricing . Nenhum recurso é criado por este arquivo.

1. Faça merge da PR, atualize `branch` no Blueprint para `main` e confira CI.
2. Crie um Blueprint no workspace escolhido, usando este arquivo. `sync: false`
   solicita segredos só na criação inicial; mudanças seguintes são pelo painel.
3. Cadastre os quatro tokens próprios e `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`
   no painel. O adapter usa HTTPS `POST {base}/chat/completions`, `messages` e
   `max_tokens`; escolha um provedor/modelo compatível e valide com uma pergunta.
   A assinatura do ChatGPT não fornece automaticamente uma chave de API.
4. Configure allowlists de servidor **e canal de teste**. Esses campos são
   obrigatórios em live. Ative Message Content Intent no Developer Portal dos
   quatro apps. Permissões: ver canal, enviar mensagens e ler histórico para
   resolver respostas. Não precisa de Administrador, membros ou presença alheia.
5. Use aplicativos de teste próprios ou desligue a instância antiga daquele app
   antes de reutilizar um token. Duas hospedagens do mesmo app geram duplicatas.
6. No canal de teste, mude `BOT_MODE=live`, mantendo espontâneo desligado.
   `SYNC_COMMANDS=true` registra `/alcateia` na inicialização; esta operação
   substitui os comandos de guild daquele app, portanto use apps de teste ou
   faça o corte aprovado primeiro. Depois da sincronização, volte a `false`.
7. Verifique quatro `discord_ready`, perguntas por nome/menção, preferências,
   respostas a outros usuários, status e falha simulada de IA. Só então habilite
   `ENABLE_SPONTANEOUS=true`. O serviço não inicia interações por timer.

`BOT_MODE` e controles operacionais têm valores no Blueprint: uma nova sync pode
restaurá-los. Mantenha o arquivo como fonte de verdade ao promover configurações.

## Operação, privacidade e rollback

O uso é no Discord, não uma ponte de chat para o portal infantil. Revele aos
membros que a mensagem respondida é processada pelo provedor de IA escolhido;
as políticas de retenção desse provedor precisam ser verificadas pelo operador.
O servidor não persiste mensagens. O cache do Discord é volátil (100 mensagens
por cliente). Preferências são apenas enums; opt-out permanece até reativação.
Logs contêm heartbeat e contadores agregados. Registros de dedupe/cooldown são
limpos após 24 horas. Snapshots/backup podem reter valores apagados até expirar.

Uma instância apenas. Não escale horizontalmente SQLite; migre para Postgres
com coordenação distribuída antes disso. Disco acoplado implica interrupção
curta nos deploys. Configure alertas de falha no Render e confira heartbeat a
cada cinco minutos; não há painel público nem porta HTTP neste worker.

Antes de um corte, faça backup consistente usando a API `sqlite3.Connection.backup`
para armazenamento restrito fora deste serviço. Teste restauração em standby.
Snapshots do disco não substituem um procedimento testado de backup do banco.
Uma restauração antiga também pode restaurar preferências excluídas: respeite
pedidos de exclusão e não recoloque dados antigos sem avaliação.

Rollback: coloque novo serviço em standby, pare suas conexões, restaure o release
anterior se necessário e só depois religue os apps antigos. Nunca deixe ambos
respondendo com o mesmo token. Nenhum dado do camelBots é importado implicitamente.

## Próximos marcos

1. Validar credenciais e o provedor no canal de teste.
2. Portar jogos/comandos dos fontes exportados e provar paridade.
3. Adicionar contexto temporário por pessoa/canal com TTL e limites.
4. Base de conhecimento revisada da Workshop e feedback de qualidade.
5. Migrar banco/coordenação quando volume justificar; treinamento separado só
   com dataset revisado, avaliação e consentimento apropriados.
