# CERBERUS_02 — Security design review

**Escopo:** laboratório didático executado localmente. O site público hospeda apenas documentação; não aceita requisições de criação de reservas e não expõe um banco de dados.

## Fronteiras de confiança
- Entrada externa CLI/objeto JSON -> validação de domínio -> portas -> armazenamento.
- Os adaptadores externos não devem transportar configurações sensíveis ao core.
- O projeto não usa `eval`, execução de comandos, serialização com pickle, downloads automáticos nem dependências runtime de terceiros.
- SQLite usa placeholders (?) em todos os parâmetros; a tabela é declarada estaticamente. A persistência usa arquivo local configurado pelo operador.
- `event_code`, `guest_name` e `seats` possuem regras de domínio; rejeita controle ASCII e atributos inesperados no controller JSON.
- `Reservation` é imutável. ID aleatório UUID4 na composição operacional; determinístico somente em teste.

## Limitações a não esconder
- **Sem login, controle de permissões, consentimento, criptografia de dados em repouso, retenção, LGPD, limitação de tráfego ou política de backups.** Nunca operar com pessoas reais.
- Não há garantia de integridade de estoque, capacidade por evento, concorrência ou idempotência distribuída.
- SQLite local é uma demonstração; permissões do sistema de arquivos, criptografia e limpeza do banco são responsabilidade do operador.
- Teste AST protege a fronteira dos imports diretos, não detecta carregamentos dinâmicos.
- Não abra `ReservationJsonController` na internet sem autenticação, autorização, rate limiting, logging seguro e uma modelagem própria de ameaças.

## Gates
1. Teste de domínio e contratos em memória e SQLite.
2. Teste AST de regra de dependências.
3. Inspeção de HEAD/GET, CSP, nosniff, frames, permissão de métodos e rotas do Worker.
4. Validar que o experiment 01 e os endpoints existentes não regressaram.
5. Preservar versão anterior do Worker para rollback.
