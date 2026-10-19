# ARES / TCP Foundation — v0.1

> Build. Break. Understand. Rebuild.

**Status:** primeiro experimento TCP local e reproduzível. **Não implementa HTTP e não é adequado para exposição pública.**

Este laboratório isola o ciclo de vida de um servidor TCP em C17/POSIX, preservando o protótipo HTTP já existente em `src/` na raiz do repositório.

## Compilar e executar

Requer Linux/POSIX, `cc`, `make`, `python3` e opcionalmente `nc`:

```bash
cd ares/tcp-foundation
make
make run
```

Em outro terminal:

```bash
printf 'Hello ARES!\n' | nc 127.0.0.1 8081
# ARES/0.1 ECHO: Hello ARES!
```

Caso não tenha netcat:

```bash
python3 -c 'import socket; s=socket.create_connection(("127.0.0.1",8081)); s.sendall(b"ping\n"); print(s.recv(1024).decode(),end=""); s.close()'
```

Você também pode usar `./build/ares-tcp --port 9091`. A opção `--port 0` seleciona uma porta efêmera para os testes. A escuta fica **restrita a 127.0.0.1**, mesmo com porta personalizada.

## Testes

```bash
make test
make clean
```

Os oito testes de integração verificam: echo básico, fragmentação de entrada TCP, linha vazia, limite de 512 bytes, rejeição de entradas maiores, caracteres não imprimíveis, término prematuro da entrada e múltiplos clientes sequenciais.

**Resultado observado durante a preparação do laboratório:** 8 testes passaram na compilação comum e 8 passaram com AddressSanitizer + UndefinedBehaviorSanitizer.

## Anatomia da comunicação

```text
socket(AF_INET, SOCK_STREAM, 0)
      ↓
setsockopt(SO_REUSEADDR)
      ↓
bind(127.0.0.1:PORT)
      ↓
listen(BACKLOG)
      ↓
accept()  ← cliente conectado
      ↓
recv()    ← fluxo de bytes, NÃO mensagens prontas
      ↓
send()    → resposta e possíveis envios parciais
      ↓
close(client) → accept() novamente
```

### Protocolo didático

Cada cliente envia **uma única linha ASCII imprimível terminada por LF (`\n`)**, contendo até **512 caracteres**. O servidor responde `ARES/0.1 ECHO: <linha>\n` e encerra a conexão. Não há suporte a HTTP ou TLS.

Entradas inválidas recebem mensagens `ERR ...`. Cada operação de recebimento tem timeout de 3 segundos. O código lê deliberadamente **um byte por recv()**, para deixar visível o enquadramento do protocolo; isso é ineficiente e não é técnica de produção. A rotina `send_all()` demonstra como tratar possíveis envios parciais.

### Descoberta do experimento

No primeiro teste, fechar uma conexão quando ainda havia dados pendentes na entrada causou **TCP RST**, e a mensagem de erro podia não chegar ao cliente. O laboratório passou a drenar uma quantidade limitada de dados de entrada (até 2048 bytes ao todo), antes de responder a solicitações inválidas. Isso evita o problema nos casos comuns do experimento, mas não é solução universal para clientes arbitrariamente hostis.

## Limitações

- Um cliente por vez; sem concorrência, filas de trabalho, `epoll` ou threads.
- Protocolo ASCII de uma linha, não HTTP.
- Um timeout por chamada de socket não representa um deadline total; cliente lento pode prolongar o atendimento.
- O limite adicional de descarte não evita RST em todos os cenários, por exemplo diante de payloads enormes.
- Não há autenticação, criptografia nem endurecimento suficiente para a internet pública.
- Nenhuma integração com Cloudflare Pages executa o binário: o site é apenas a vitrine/documentação.

## Próxima bancada

**v0.2 — HTTP Parsing:** request line, headers, estados de parser, limites explícitos, erros e testes de requisições malformadas.

Site: [ARES — The Workshop Labs](https://workshop-labs.pages.dev/projects/ares/).
