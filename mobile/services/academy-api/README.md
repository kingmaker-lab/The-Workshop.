# Wolfpack Academy API (MVP v0.1)

Primeiro backend educacional da The Workshop Mobile Division. Serviço sem estado: somente catálogo e correção de exercícios de múltipla escolha. Não executa código submetido pelos usuários e não armazena dados pessoais.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | /health | Health check |
| GET | /api/v1/games | Catálogo de jogos |
| GET | /api/v1/challenges | Desafios públicos, sem gabarito |
| GET | /api/v1/challenges?game_id=debug | Filtro por jogo |
| GET | /api/v1/challenges/{id} | Detalhes |
| POST | /api/v1/challenges/{id}/check | Enviar JSON {"choice_id":"a"} e receber explicação |

O endpoint educativo de correção devolve o gabarito depois da tentativa; **não** serve para leaderboard competitivo, certificados ou prêmios. Antes de grande exposição pública, configurar limite de requisições na borda. CORS restrito por ALLOWED_ORIGINS.

## Desenvolvimento local

No diretório mobile/services/academy-api:

1. Criar e ativar um venv com Python 3.12.
2. Executar pip install -r requirements.txt pytest httpx.
3. Executar uvicorn app:app --reload --port 8000.
4. Executar PYTHONPATH=. pytest -q.

Documentação automática: http://localhost:8000/docs.

## Deploy Render (Docker)

- Repositório: https://github.com/kingmaker-lab/The-Workshop.
- Branch: feat/wolfpack-academy-api-mvp (beta), main após revisão.
- Runtime: Docker.
- Docker context: mobile/services/academy-api.
- Dockerfile path: mobile/services/academy-api/Dockerfile.
- Plano free apenas para desenvolvimento, não produção.
- Variável ALLOWED_ORIGINS=https://wolfpack.wolfpackworkshop.workers.dev.
- Health check: /health.
- Escuta 0.0.0.0 no PORT configurado pelo Render.

## Próximas etapas

- Auditar a plataforma Wolfpack existente e migrar desafios reais.
- Acrescentar CI, varredura de dependências e observabilidade.
- Sincronização de progresso com persistência durável somente após definir autenticação e LGPD.
- Implementar rate limiting na API/borda antes do lançamento público.
- Testar contratos entre aplicativo Flutter e backend.
