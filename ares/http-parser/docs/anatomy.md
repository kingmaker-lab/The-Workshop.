# Anatomia de uma requisição HTTP — ARES v0.2

## 1. Os bytes

    GET /health HTTP/1.1\r\n
    Host: localhost\r\n
    User-Agent: ARES-Lab\r\n
    \r\n

Os primeiros bytes podem ser expressos em hexadecimal:

    47 45 54 20 2f 68 65 61 6c 74 68 20 48 54 54 50 ...
     G  E  T     /  h  e  a  l  t  h     H  T  T  P

CRLF é 0d 0a. Quatro bytes finais 0d 0a 0d 0a marcam o fim dos cabeçalhos.

## 2. Por que incremental?

O TCP é um fluxo. Uma única mensagem pode chegar fragmentada em várias chamadas de leitura. O parser adiciona bytes a um buffer com limite, rastreia quantos foram consumidos e só passa para validação quando identifica CRLF CRLF.

Separadores da request line são espaços simples exatos; a versão aceita é HTTP/1.0 ou HTTP/1.1. Método e nomes de campos usam caracteres válidos de token. O target precisa começar com /, pois a bancada só estuda origin-form.

## 3. Cabeçalhos e erros

Um cabeçalho é nome seguido de : e valor. Em HTTP/1.1, Host deve aparecer exatamente uma vez e não pode ser vazio. Valores e nomes malformados, bytes de controle, obs-fold e whitespace antes de : são rejeitados.

Resultados de API: NEED_MORE, COMPLETE, BAD_REQUEST, TOO_LARGE, TOO_MANY_HEADERS, UNSUPPORTED_BODY e INVALID_STATE.

A API informa o número de bytes consumidos. A CLI rejeita bytes excedentes; a biblioteca devolve controle ao chamador. **Um chamador que ignora o leftover é inseguro.**

## 4. Framing e ameaça

Divergência de interpretação entre proxies e origens pode produzir HTTP request smuggling. Como este laboratório ainda não processa corpos, recusa Transfer-Encoding, Expect e Content-Length diferente de uma única ocorrência literal 0. Essa política é uma limitação consciente, não proteção completa.

Não há validação completa de Host, normalização de caminho, timeouts de rede ou HTTP conforme para internet pública.

## 5. Experimentos

- Fragmente os mesmos headers em 1, 2, 3 e 7 bytes.
- Troque CRLF por LF sozinho.
- Remova Host em HTTP/1.1 e compare com HTTP/1.0.
- Envie Content-Length duplicado e observe a rejeição.
- Exceda 32 cabeçalhos ou 8192 bytes.
- Execute a suíte com sanitizers e compare.

O próximo passo é entender respostas HTTP e roteamento, antes de qualquer integração a uma instância de servidor real.
