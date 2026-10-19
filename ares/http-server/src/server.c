#define _POSIX_C_SOURCE 200809L
#include "ares_response.h"
#include "ares_http_parser.h"
#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>
#define BACKLOG 16
#define RECV_DEADLINE_SEC 5
static volatile sig_atomic_t active = 1;
static void stop(int signo)
{
    (void)signo;
    active = 0;
}
static int signals_init(void)
{
    struct sigaction action;
    memset(&action, 0, sizeof(action));
    sigemptyset(&action.sa_mask);
    action.sa_handler = stop;
    if (sigaction(SIGTERM, &action, NULL) < 0 ||
        sigaction(SIGINT, &action, NULL) < 0) return -1;
    action.sa_handler = SIG_IGN;
    return sigaction(SIGPIPE, &action, NULL);
}
static int set_timeouts(int fd)
{
    struct timeval receive = {.tv_sec = 1, .tv_usec = 0};
    struct timeval send = {.tv_sec = 2, .tv_usec = 0};
    return setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &receive, sizeof(receive)) == 0 &&
           setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &send, sizeof(send)) == 0;
}
static int deadline_expired(const struct timespec *start)
{
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) return 1;
    return (now.tv_sec - start->tv_sec) >= RECV_DEADLINE_SEC;
}
static void send_error(int fd, int status)
{
    ares_response response;
    ares_error(status, &response);
    (void)ares_write_response(fd, &response, 0);
}
static void handle_client(int fd)
{
    if (!set_timeouts(fd)) return;
    struct timespec started;
    if (clock_gettime(CLOCK_MONOTONIC, &started) != 0) return;
    ares_parser parser;
    ares_parser_init(&parser);
    unsigned char buffer[1024];
    for (;;) {
        if (deadline_expired(&started)) {
            send_error(fd, 408);
            return;
        }
        ssize_t n = recv(fd, buffer, sizeof(buffer), 0);
        if (n == 0) {
            if (parser.used > 0) send_error(fd, 400);
            return;
        }
        if (n < 0) {
            if (errno == EINTR) continue;
            if (errno == EAGAIN || errno == EWOULDBLOCK) continue;
            return;
        }
        size_t consumed = 0;
        ares_result result = ares_parser_feed(&parser, buffer, (size_t)n, &consumed);
        if (result == ARES_NEED_MORE) continue;
        if (result == ARES_COMPLETE) {
            /* Extra bytes in this recv could be body or a second request.
               This lab cannot frame either, so reject them. */
            if (consumed != (size_t)n) {
                send_error(fd, 400);
                return;
            }
            ares_response response;
            ares_route(&parser.request, &response);
            (void)ares_write_response(fd, &response,
                    strcmp(parser.request.method, "HEAD") == 0);
            return;
        }
        if (result == ARES_TOO_LARGE || result == ARES_TOO_MANY_HEADERS)
            send_error(fd, 431);
        else if (result == ARES_UNSUPPORTED_BODY)
            send_error(fd, 501);
        else
            send_error(fd, 400);
        return;
    }
}
int ares_serve(uint16_t port)
{
    if (signals_init() < 0) { perror("sigaction"); return 1; }
    int listener = socket(AF_INET, SOCK_STREAM, 0);
    if (listener < 0) { perror("socket"); return 1; }
    int reuse = 1;
    if (setsockopt(listener, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) != 0) {
        perror("SO_REUSEADDR");
        close(listener);
        return 1;
    }
    struct sockaddr_in local;
    memset(&local, 0, sizeof(local));
    local.sin_family = AF_INET;
    local.sin_port = htons(port);
    local.sin_addr.s_addr = htonl(INADDR_LOOPBACK); /* Never bind 0.0.0.0. */
    if (bind(listener, (struct sockaddr *)&local, sizeof(local)) != 0 ||
        listen(listener, BACKLOG) != 0) {
        perror("bind/listen");
        close(listener);
        return 1;
    }
    socklen_t length = sizeof(local);
    if (getsockname(listener, (struct sockaddr *)&local, &length) != 0) {
        perror("getsockname");
        close(listener);
        return 1;
    }
    printf("ARES v0.3 listening on http://127.0.0.1:%u\n", (unsigned)ntohs(local.sin_port));
    fflush(stdout);
    while (active) {
        int client = accept(listener, NULL, NULL);
        if (client < 0) {
            if (errno == EINTR) continue;
            perror("accept");
            close(listener);
            return 1;
        }
        handle_client(client);
        close(client);
    }
    close(listener);
    return 0;
}
