# Arquitetura do CERBERUS — v0.4

## Contexto

O Cerberus é um laboratório educacional para explorar arquitetura de software, dentro do The Workshop. Nesta etapa não há contas de usuários nem operações mutáveis. Conteúdo acessível publicamente de modo isolado dos demais sistemas.

## Contexto de execução

```text
Visitor (HTTPS)
    |
    v
Cloudflare Workers / cerberus
    |-- GET /             => landing page estática
    |-- GET /labs/01      => experimento 001 (documentação)
    |-- GET /labs/02      => experimento 002 (camadas, Clean e Hexagonal)
    |-- GET /labs/03      => experimento 003 (fluxo visual de falhas)
    |-- GET /api/modules  => dados estáticos JSON
    |-- GET /api/status   => status declarativo do portal
    '-- GET /api/projects => compatibilidade com versão anterior
               |
               v
           URLs HTTPS externas (links diretos, sem proxy)
```

## Decisões arquiteturais

- **Evoluir em passos reversíveis:** Worker de leitura, sem dados sensíveis ou dependências externas no caminho crítico.
- **Contratos pequenos:** GET/HEAD permitidos; caminhos não definidos retornam 404; outros métodos 405.
- **Isolamento:** links de navegação não criam confiança entre origens; nenhum token ou sessão atravessa limites.
- **Testabilidade:** testes de contrato em Node 20+, mesmo código-fonte do deploy.
- **Conteúdo pedagógico:** hipótese e conclusão provisória são distintas de benchmark executado e validado.
- **Evolução posterior:** exemplos em C, Python e Ruby podem acompanhar estudos no próprio repositório; não é necessário introduzir banco ou frontend framework agora.

## Qualidades prioritárias

- Segurança: CSP, X-Frame-Options, nosniff, política de referência, sem scripts/cookies.
- Performance: somente conteúdo estático e JSON em memória; zero fontes remotas.
- Acessibilidade: semântica HTML, foco visível, contraste e mídia responsiva.
- Reprodutibilidade: fonte + teste + ADR versionados.

## Não objetivos

API de orquestração de outros serviços; gateway de identidade; sistema universal de monitoramento; scanner de vulnerabilidades; redirecionador aberto; integrações entre domínios via scripts.

## Bancada 03 (somente ambiente local de teste)

Dois arquivos SQLite: `producer.sqlite` registra reservas e outbox de modo transacional; `consumer.sqlite` guarda notificações com chave única. Testes Python instanciam um servidor HTTP bound a 127.0.0.1 com porta efêmera e injetam falhas antes do envio e depois do commit remoto. O Worker de produção **não** possui conexão, binding, proxy ou chamadas a esses bancos; fornece apenas documentação estática de leitura. Não existe isolamento em processos diferentes nem garantia universal exactly-once.
