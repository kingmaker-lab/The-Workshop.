# ARES — HTTP Parser v0.2

> Build. Break. Understand. Rebuild.

**Status:** experimento implementado e testado localmente. **Não é um servidor HTTP.**

Dá sequência ao [TCP Foundation v0.1](../tcp-foundation/README.md). O parser antigo de src/http_parser.c permanece preservado: este novo módulo é isolado e **não foi integrado ao servidor de rede**.

## Objetivo

TCP entrega um fluxo de bytes, não requisições prontas. A API ares_parser_feed() recebe fragmentos de comprimento arbitrário, armazena até 8192 bytes, detecta CRLF CRLF e valida a linha de requisição mais seus cabeçalhos.

    fragments → bounded buffer → CRLF CRLF → parse → ares_request

A alimentação é incremental, mas a análise sintática é feita quando os cabeçalhos estão completos. Um futuro módulo poderá processar linhas conforme chegam.

## Como compilar e testar

Na raiz do monorepo:

    cd ares/http-parser
    make
    make demo
    make test

Inspecione uma requisição offline:

    printf 'GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n' | ./build/ares-http-inspect

Saída esperada:

    PARSE: COMPLETE
    METHOD: GET
    TARGET: /health
    VERSION: HTTP/1.1
    HEADERS: 1
      Host: localhost

Teste de erro:

    printf 'GET / HTTP/1.1\r\n\r\n' | ./build/ares-http-inspect
    # REJECT: BAD_REQUEST (exit 2)

A ferramenta CLI usa apenas stdin e não abre sockets.

## API e limites

    ares_parser parser;
    ares_parser_init(&parser);
    size_t consumed = 0;
    ares_result r = ares_parser_feed(&parser, fragment, length, &consumed);

O chamador deve verificar consumed: os bytes não consumidos **não são processados**, e ignorá-los pode provocar falhas de framing. Após um estado terminal, reinicialize o parser para outra requisição.

| Recurso | Limite |
| --- | ---: |
| Total dos headers | 8192 bytes |
| Request line | 2048 bytes |
| Linha individual | 2048 bytes |
| Campos HTTP | 32 |
| Nome / valor | 64 / 1024 bytes |
| Método / target | 16 / 2048 bytes |

## Escopo e segurança

Aceita um subconjunto estrito de HTTP/1.0 e HTTP/1.1: target em origin-form (começando por /), métodos e nomes de campo token válidos, ASCII nos valores e terminadores CRLF. HTTP/1.1 exige Host presente, não vazio e não duplicado.

Recusa campos malformados, bytes de controle, whitespace antes do colon, obs-fold e limites excedidos. **Não suporta corpo HTTP, Transfer-Encoding, Expect nem Content-Length diferente de uma única ocorrência literal 0.** Também rejeita OPTIONS *, request targets com URI absoluta e valores não ASCII.

Não implementa gramática HTTP integral, validação rigorosa da autoridade Host, normalização de URI, TLS, deadline de rede, pipelining ou request smuggling completo. **Não é apropriado para tráfego público.**

## Testes locais realizados

- 2747 checks da suíte em C, com fragmentação e bytes aleatórios.
- 5 testes de CLI.
- Compilação com warnings elevados e tratamento de warnings como erros.
- Execuções adicionais com ASan/UBSan sem falhas detectadas.

    make clean
    make test CFLAGS='-std=c17 -O1 -g -Wall -Wextra -Wpedantic -Werror -fsanitize=address,undefined -fno-omit-frame-pointer' LDFLAGS='-fsanitize=address,undefined'

Isso não equivale a uma auditoria ou prova de ausência de bugs.

Leia [a autópsia dos bytes](docs/anatomy.md).

## Próximo marco

ARES v0.3 — Routing & Responses. A integração ao servidor preexistente requer revisão e testes adicionais.

[Workshop Labs — Project ARES](https://workshop-labs.pages.dev/projects/ares/)
