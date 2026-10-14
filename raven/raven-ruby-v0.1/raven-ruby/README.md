# RAVEN — Ruby Security Drift Watch

**Versão:** v0.1.0 | **Linguagem:** Ruby 3 | **Dependências para executar:** somente bibliotecas padrão do Ruby.

Ferramenta de **auditoria passiva de postura HTTP** e **detecção de drift** entre duas capturas. Complementa o HTTP Auditor escrito em Python: o auditor mapeia recursos; o RAVEN registra e compara a configuração de segurança de uma URL escolhida.

## Características

- Uma requisição `HEAD` por snapshot, sem crawler, sem seguir redirecionamentos e sem ataques ativos.
- Verificação TLS pelo sistema de confiança do Ruby/OpenSSL (certificado inválido provoca erro).
- Registra status, headers selecionados, atributos de cookies (nunca seus valores), validade e emissor do certificado TLS.
- Compara snapshots JSON do **mesmo alvo**, ignorando data/hora da inspeção, o contador de dias até a expiração e nonces CSP rotativos.
- Detecta alterações em políticas HTTP, cookies, certificado e código de status.
- Apresenta **observações heurísticas**, que não equivalem a vulnerabilidades confirmadas.

## Requisitos

- Ruby >= 3.0
- `webrick` para testes locais (Ruby 3 pode exigir `gem install webrick`; o aplicativo não depende dele).

## Como usar

```bash
# A partir da pasta do projeto:
ruby bin/raven snapshot https://seu-dominio-autorizado.example/ \
  --output baseline.json

# Execute após uma mudança / deploy:
ruby bin/raven snapshot https://seu-dominio-autorizado.example/ \
  --output atual.json

# Compare os relatórios:
ruby bin/raven diff baseline.json atual.json --output drift.json
```

`--timeout 8` ajusta o tempo limite por operação de conexão/leitura/escrita. Use apenas alvos sob sua administração ou autorização.

## Códigos de saída

| Código | Significado |
| --- | --- |
| `0` | Execução bem-sucedida; no `diff`, nenhuma mudança. |
| `1` | Comando não reconhecido. |
| `2` | Entrada inválida, TLS/conexão falhou ou erro no arquivo. |
| `3` | O comando `diff` detectou mudança de postura. Útil em CI. |

## Exemplo de integração com pipeline

```bash
ruby bin/raven snapshot https://staging.exemplo-autorizado.com --output current.json
ruby bin/raven diff baseline.json current.json --output drift.json
# Código 3 = revisão de configuração necessária (não significa invasão ou vulnerabilidade).
```

## JSON de saída

O snapshot usa `schema_version: 1` e armazena `target`, `status`, `headers`, `cookies`, `tls`, `observations`, `observed_at`. O arquivo `drift.json` contém `changes_count` e `changes` (`path`, `before`, `after`).

## Testes

```bash
ruby test/test_raven.rb
```

Os testes sobem um servidor WEBrick somente em `127.0.0.1` e exercitam requisição única, não redirecionamento, anonimização de cookies, diff de cabeçalhos, estabilidade de nonces CSP, validação de alvo, URL inválida e persistência JSON.

## Restrições e futuras melhorias

1. Alguns serviços retornam **405/501 para `HEAD`** ou apresentam cabeçalhos diferentes de `GET`; a ferramenta **não faz GET automático**, e sinaliza `HEAD` não suportado. Nesta situação, o resultado de segurança não é conclusivo.
2. Atualmente não há crawler, importação direta do relatório do HTTP Auditor nem proteção completa contra **DNS rebinding** (além de não seguir redirecionamentos). O usuário define uma URL confiável/autorizada.
3. Políticas de segurança variam por rota e por contexto. Ausência de header não prova uma falha explorável.
4. Diferenças entre snapshots não são automaticamente regressões: mudança de certificado pode ser renovação legítima.
5. O diff de cookies compara os campos da lista; pode apresentar substituição da lista completa em uma alteração isolada. Refinamento por cookie é uma melhoria futura.
6. Não armazena credenciais nem parâmetros de query em URL: URLs contendo userinfo ou query são rejeitadas.

## Estrutura

```text
raven-ruby/
├── bin/raven             # CLI
├── lib/raven.rb          # inspeção, regras e comparação
├── test/test_raven.rb    # testes locais
└── README.md
```

**Objetivo:** transformar 'o que o alvo apresenta hoje?' em 'o que mudou em relação à última execução?'.
