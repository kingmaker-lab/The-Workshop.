# The Workshop Mobile Division

**Status:** [IDEA] → planejamento inicial  
**Data:** 2026-10-30  
**Escopo:** Android e iOS, com distribuição web/PWA quando fizer sentido.  
**Princípio:** *Build. Break. Understand. Rebuild.*

> Este documento propõe futuros aplicativos; não indica builds ou lançamentos já concluídos.

## Objetivos

1. Disponibilizar experiências educativas de programação, tecnologia e segurança, gratuitamente, começando por iniciantes.
2. Reutilizar de modo consciente o conteúdo, os jogos e os laboratórios existentes na plataforma web The Workshop.
3. Permitir aprendizagem por experimentação: explicações dos erros, hipóteses, testes e comparação de soluções.
4. Preservar privacidade, segurança, transparência técnica e custos operacionais baixos.

## Inventário e prioridades

| ID | Produto provisório | Missão | Prioridade | Escopo inicial |
|---|---|---|---|---|
| MOB-001 | Wolfpack Academy | Jogos e desafios de programação | P0 | MVP Android + versão web já existente como referência |
| MOB-002 | Workshop Pocket | Biblioteca de estudos e exercícios offline | P1 | Protótipo |
| MOB-003 | Workshop News | Curadoria, notícias e novidades da The Workshop | P1 | Integração com portal web, leitura offline e favoritos |
| MOB-004 | Workshop Labs Mobile | Experimentos e laboratórios didáticos seguros | P2 | Prova de conceito |
| MOB-005 | Workshop Security | Treinamento de segurança defensiva e conscientização | P2 | Pesquisa |
| MOB-006 | Workshop Business | Futuras ferramentas de trabalho para empresas | P3 | Descoberta de requisitos e conformidade |

**Estratégia de publicação:** começar com **um app principal**, Wolfpack Academy. Considerar conteúdo de Pocket, News e Labs como módulos do app principal antes de fragmentar em vários binários. Criar apps separados somente quando houver proposta de valor e público suficientemente distintos; isso reduz manutenção e riscos de rejeição por apps muito semelhantes.

## MOB-001: Wolfpack Academy

**Referência existente:** https://wolfpack.wolfpackworkshop.workers.dev/  
A plataforma web é um ponto de partida, mas o estado, a arquitetura e a reutilização de seu código precisam de auditoria antes de integrar.

### Público e experiência

- Público: iniciantes em tecnologia, especialmente brasileiros.
- PT-BR no primeiro lançamento; preparar localização futura.
- Acesso gratuito; sem paywall nos conteúdos educativos planejados.
- Experiência mobile acessível: navegação por toque, fonte ajustável, contraste, navegação por leitor de tela e suporte a telas pequenas.

### MVP: somente o essencial

- Catálogo de trilhas: lógica, Python, JavaScript e fundamentos de C (priorizar lógica + Python na primeira versão).
- Missões com pergunta, exemplos, feedback contextual, explicação do erro e caminho alternativo.
- Exercícios de interpretação de código, ordenação de algoritmos, debugging guiado e quizzes com justificativa.
- Progresso local persistido e estatísticas simples; conta opcional em etapa posterior.
- Seleção de módulos para uso offline (conteúdos sem executor remoto).
- Tela sobre o projeto, licenças e mecanismo de feedback.

### Excluído do primeiro MVP

- Editor/execução irrestrita de código arbitrário.
- Ranking global, chat, pagamentos, marketplace ou perfil público.
- Login obrigatório, coleta de dados excessiva e notificações invasivas.
- Chatbot de IA como dependência para completar atividades.

### Métricas de qualidade (propostas)

- 0 falhas críticas abertas no release.
- 100% dos desafios do MVP revisados tecnicamente.
- Pelo menos 20 desafios testados e distribuídos em níveis, antes do beta.
- Fluxos principais testados offline; sem bloqueio total se o backend estiver fora do ar.
- Medir taxa de conclusão de missão via dados agregados ou opt-in, evitando rastreamento invasivo.

## Arquitetura candidata

```
Android / iOS
  └─ Flutter (Dart), UI adaptativa
       ├─ módulos de ensino e jogos
       ├─ banco local (SQLite) e cache offline
       ├─ serviço de sincronização opcional
       └─ cliente HTTP tipado
               |
               v
     Cloudflare API / Workers (a validar)
       ├─ catálogo versionado de conteúdo
       ├─ versionamento e atualização de desafios
       ├─ autenticação opcional, futuramente
       └─ pontuação somente se existir mecanismo server-side confiável
```

**Justificativa:** Flutter compartilha código de UI e lógica entre Android e iOS, permitindo desenvolvimento inicial no Linux para Android. Build e envio para iOS exigem ambiente macOS/Xcode. Alternativa a avaliar durante descoberta: PWA/Capacitor se o código web atual oferecer grande reaproveitamento, mantendo experiência genuína de app.

**Separação de responsabilidades:**
- Conteúdo didático versionado em JSON/Markdown com schema validado.
- Motor de missões testável independentemente da interface.
- Interface mobile sem confiança em respostas do cliente para ranking competitivo.
- Backend opcional para MVP; manter modo offline como primeira classe.

### Segurança e privacidade

- TLS e verificação de certificados por padrão; nada de desabilitar validações.
- Dados mínimos, retenção explícita e mecanismo de exclusão caso contas sejam adicionadas.
- Nenhum segredo/chave privada no binário mobile.
- Rate limits e validação server-side em APIs; autenticação com tokens de curta duração quando aplicável.
- Não executar código não confiável no host ou backend sem isolamento robusto e limites de CPU, memória, tempo, rede e filesystem. Preferir desafios estáticos/interpretativos no MVP.
- Proteção contra manipulação de progresso só se necessário; não prometer inviolabilidade do dispositivo cliente.
- Revisar dependências, SBOM, CI, análise estática, testes e gates de release.
- Termos, política de privacidade, licenças de conteúdo e conformidade LGPD antes da publicação.

## Fases de trabalho (estimativa por sprint, sem datas de lançamento prometidas)

### Fase 0: descoberta e inventário

- [ ] Auditar estrutura e conteúdo da plataforma Wolfpack existente.
- [ ] Definir público-alvo inicial e 2 ou 3 jornadas prioritárias.
- [ ] Inventariar conteúdos reaproveitáveis, contratos de API e direitos de uso.
- [ ] Decidir Flutter versus PWA/Capacitor após prova curta.
- [ ] Criar design system e wireframes navegáveis.

**Critério de saída:** backlog validado, arquitetura decidida e 1 fluxo de aprendizado desenhado.

### Fase 1: protótipo funcional

- [ ] Criar projeto mobile Android em branch/projeto próprio.
- [ ] Implementar catálogo, tela de missão, feedback e persistência local.
- [ ] Construir 5 desafios representativos e teste de acessibilidade inicial.
- [ ] Adicionar lint, unit tests, análise de dependências e CI.

**Critério de saída:** protótipo instalável e demonstrável.

### Fase 2: MVP e beta

- [ ] Expandir para no mínimo 20 desafios revisados.
- [ ] Testar backup, atualização/migração do banco local e recuperação de erros.
- [ ] Testar em dispositivos fracos, tamanhos de tela distintos e conexões instáveis.
- [ ] Produzir política de privacidade, imagens da loja, texto de descrição e instruções para testadores.
- [ ] Organizar teste interno e fechado na Google Play, conforme requisitos de conta.

**Critério de saída:** beta com feedback documentado e release gate aprovado.

### Fase 3: iOS e expansão

- [ ] Preparar ambiente macOS/Xcode ou CI macOS confiável.
- [ ] Corrigir detalhes de interface, notificações/permissões e acessibilidade no iOS.
- [ ] Publicar via TestFlight, revisar diretrizes Apple e submeter app nativo com funcionalidade real.
- [ ] Avaliar módulos Pocket/News/Labs antes de criar novos apps.

**Critério de saída:** candidato de release iOS validado; sem compromisso de data até haver infraestrutura, conta e testes.

## Organização sugerida do projeto

```
mobile/
├── README.md
├── apps/
│   └── wolfpack_academy/
├── packages/
│   ├── learning_core/
│   ├── mission_schema/
│   └── workshop_design/
├── content/
│   └── missions/
├── docs/
│   ├── architecture/
│   ├── privacy/
│   └── release/
└── .github/workflows/
```

**Observação:** estrutura-alvo ainda não criada. Avaliar monorepo versus repositório dedicado quando o protótipo existir.

## Restrições operacionais e lojas

- **Google Play Console:** inscrição única de US$ 25 (verificar valor regional no cadastro); contas pessoais novas podem exigir teste fechado com pelo menos 12 testadores por 14 dias consecutivos antes de acesso à produção.
- **Apple Developer Program:** assinatura anual de US$ 99 (ou equivalente local); publicação iOS requer Xcode/macOS e conformidade com App Review.
- **Apple 4.2:** não publicar uma simples WebView ou agregador de links; entregar experiência própria de app e valor duradouro.
- **Apple 4.3:** evitar muitas aplicações praticamente idênticas; combinar módulos quando adequado.

Fontes de referência:
- https://docs.flutter.dev/install
- https://docs.flutter.dev/deployment/ios
- https://support.google.com/googleplay/android-developer/answer/6112435?hl=pt-BR
- https://support.google.com/googleplay/android-developer/answer/14151465?hl=pt-BR
- https://developer.apple.com/br/help/account/membership/program-enrollment/
- https://developer.apple.com/app-store/review/guidelines/br/

## Próximas decisões

1. Auditar o Wolfpack web para medir reaproveitamento e dependências atuais.
2. Aprovar P0 como produto inicial e escolher escopo real de trilhas para versão 0.1.
3. Definir conta de publicação (pessoa física ou organização) e estratégia de distribuição.
4. Criar backlog por épicos, issues e um protótipo Android.
