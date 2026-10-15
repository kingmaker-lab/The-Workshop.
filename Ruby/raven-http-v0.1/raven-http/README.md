# RAVEN HTTP — Passive Security Posture Auditor

Ferramenta em **Ruby puro (biblioteca padrão)** para observar a postura de segurança de uma resposta HTTP/HTTPS e exportar evidências estruturadas. Integrante experimental do **The Workshop**; pode complementar o HTTP Auditor em Python sem substituir seu crawler.

## Requisitos

Ruby 3.1+; nenhuma gem externa necessária para o auditor. Internet só para consultar um alvo **sob sua autorização**.

## Execução

```bash
ruby raven.rb --help
ruby raven.rb https://exemplo-autorizado.com/ --json reports/audit.json
ruby raven.rb http://127.0.0.1:8000/ --allow-private --json reports/local.json
```

## Verificações

- Observa código HTTP, tipo de conteúdo, tamanho e SHA-256 do corpo (não grava o conteúdo).
- Analisa CSP, `frame-ancestors`/`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` e HSTS em HTTPS.
- Analisa metadados de `Set-Cookie` (`Secure`, `HttpOnly`, `SameSite`), **sem gravar o valor dos cookies**.
- Sinaliza políticas CORS observadas, sem alegar comprovação de falha de acesso.
- Registra informações públicas do certificado TLS e um alerta se estiver próximo do vencimento.
- Exporta `findings`, status, cabeçalhos relevantes e histórico de redirecionamentos para JSON.

## Controles de segurança

- Apenas método `GET`, nenhuma carga de ataque e sem exploração automática.
- **Origem fixa:** redirecionamentos fora da combinação esquema/host/porta são bloqueados.
- Resolve DNS, valida faixas e fixa o IP utilizado na conexão para reduzir risco de DNS rebinding.
- Bloqueia redes privadas, locais e algumas faixas reservadas por padrão. Use `--allow-private` apenas para ambientes locais autorizados.
- Limita tempo, respostas e redirecionamentos; o número máximo de requisições é `1 + --max-redirects`.
- Valida certificados TLS normalmente (`VERIFY_PEER`). Falhas TLS encerram a auditoria.
- Oculta **valores de query strings** no relatório; URLs no comando, logs de rede intermediária ou histórico de shell ainda podem conter dados sensíveis. Não coloque segredos na URL.

## Limitações

Uma verificação de resposta **não demonstra vulnerabilidades**; configurações podem ser intencionais. A ferramenta não executa crawler, não testa autenticação, não envia cabeçalho `Origin` e não valida explorabilidade de CORS. `--allow-private` habilita destinos em redes privadas, inclusive redirecionamentos na mesma origem. Revise políticas de rede e escopo antes de usar em infraestrutura real. O filtro de endereços é conservador, não uma lista exaustiva de todos os intervalos não roteáveis.

## Testes

```bash
ruby test/test_raven.rb
```

Os testes usam `minitest` e `webrick` (este último pode precisar de instalação separada em algumas distribuições de Ruby).

## Próximos passos

Integração com o schema de evidências do HTTP Auditor v0.2; entrada de lista de URLs dentro de escopo; classificação de prioridades; comparação temporal de relatórios; testes com fixtures TLS.
