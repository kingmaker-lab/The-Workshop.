#define _POSIX_C_SOURCE 200809L

#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>

/* TCP Foundation: a small, intentionally single-client-at-a-time lab.
 * Protocol: one newline-terminated ASCII line per connection, up to 512 bytes.
 * This is NOT HTTP and is NOT intended to be internet-facing. */

enum { DEFAULT_PORT = 8081, BACKLOG = 16, MAX_LINE = 512, MAX_DRAIN = 2048, TIMEOUT_SEC = 3 };

static volatile sig_atomic_t running = 1;

static void stop_server(int signo)
{
    (void)signo;
    running = 0;
}

static int install_signals(void)
{
    struct sigaction action;
    memset(&action, 0, sizeof(action));
    action.sa_handler = stop_server;
    sigemptyset(&action.sa_mask);
    if (sigaction(SIGINT, &action, NULL) == -1 ||
        sigaction(SIGTERM, &action, NULL) == -1) {
        return -1;
    }
    /* A disconnected client must not terminate the server on send(). */
    struct sigaction ignored;
    memset(&ignored, 0, sizeof(ignored));
    ignored.sa_handler = SIG_IGN;
    sigemptyset(&ignored.sa_mask);
    return sigaction(SIGPIPE, &ignored, NULL);
}

static int send_all(int fd, const char *buf, size_t len)
{
    size_t sent = 0;
    while (sent < len) {
        ssize_t n = send(fd, buf + sent, len - sent, 0);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return -1;
        sent += (size_t)n;
    }
    return 0;
}

static int send_text(int fd, const char *message)
{
    return send_all(fd, message, strlen(message));
}

static void handle_client(int fd)
{
    char line[MAX_LINE];
    size_t used = 0;
    bool complete = false;
    bool invalid = false;
    bool too_long = false;
    size_t consumed = 0;
    struct timeval timeout = {.tv_sec = TIMEOUT_SEC, .tv_usec = 0};

    if (setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)) < 0 ||
        setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout)) < 0) {
        perror("setsockopt client timeout");
        return;
    }

    for (;;) {
        unsigned char ch;
        ssize_t n = recv(fd, &ch, 1, 0);
        if (n < 0 && errno == EINTR) continue;
        if (n < 0) {
            if (errno == EAGAIN || errno == EWOULDBLOCK)
                (void)send_text(fd, "ERR timeout waiting for newline\n");
            else
                perror("recv");
            return;
        }
        if (n == 0) {
            if (used != 0) (void)send_text(fd, "ERR expected newline\n");
            return;
        }
        if (ch == '\n') {
            complete = true;
            break;
        }
        /* Drain a bounded amount of bad input before responding. Otherwise,
         * closing a socket with unread data can cause TCP RST and hide ERR. */
        if (ch < 0x20 || ch > 0x7e) invalid = true;
        if (used < MAX_LINE) line[used++] = (char)ch;
        else too_long = true;
        if (++consumed >= MAX_DRAIN) {
            (void)send_text(fd, "ERR line too long\n");
            return;
        }
    }

    if (complete) {
        if (too_long) {
            (void)send_text(fd, "ERR line too long\n");
            return;
        }
        if (invalid) {
            (void)send_text(fd, "ERR printable ASCII only\n");
            return;
        }
        if (send_text(fd, "ARES/0.1 ECHO: ") < 0 ||
            send_all(fd, line, used) < 0 ||
            send_text(fd, "\n") < 0) {
            perror("send");
        }
    }
}

static int parse_port(int argc, char **argv, uint16_t *port)
{
    if (argc == 1) {
        *port = DEFAULT_PORT;
        return 0;
    }
    if (argc != 3 || strcmp(argv[1], "--port") != 0 || argv[2][0] == '\0' ||
        argv[2][0] == '-') return -1;
    char *end = NULL;
    errno = 0;
    unsigned long value = strtoul(argv[2], &end, 10);
    if (errno != 0 || *end != '\0' || value > UINT16_MAX) return -1;
    *port = (uint16_t)value; /* 0 requests an OS-assigned ephemeral port. */
    return 0;
}

int main(int argc, char **argv)
{
    uint16_t port;
    if (parse_port(argc, argv, &port) != 0) {
        fprintf(stderr, "usage: %s [--port 0..65535]\n", argv[0]);
        return EXIT_FAILURE;
    }
    if (install_signals() < 0) {
        perror("sigaction");
        return EXIT_FAILURE;
    }

    int listener = socket(AF_INET, SOCK_STREAM, 0);
    if (listener < 0) {
        perror("socket");
        return EXIT_FAILURE;
    }
    int reuse = 1;
    if (setsockopt(listener, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) < 0) {
        perror("setsockopt SO_REUSEADDR");
        close(listener);
        return EXIT_FAILURE;
    }
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);

    if (bind(listener, (struct sockaddr *)&addr, sizeof(addr)) < 0 ||
        listen(listener, BACKLOG) < 0) {
        perror("bind/listen");
        close(listener);
        return EXIT_FAILURE;
    }
    socklen_t addrlen = sizeof(addr);
    if (getsockname(listener, (struct sockaddr *)&addr, &addrlen) < 0) {
        perror("getsockname");
        close(listener);
        return EXIT_FAILURE;
    }
    printf("ARES TCP v0.1 listening on 127.0.0.1:%u\n", (unsigned)ntohs(addr.sin_port));
    fflush(stdout);

    while (running) {
        int client = accept(listener, NULL, NULL);
        if (client < 0) {
            if (errno == EINTR) continue;
            perror("accept");
            break;
        }
        handle_client(client);
        close(client);
    }
    close(listener);
    return EXIT_SUCCESS;
}
