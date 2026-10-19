#define _POSIX_C_SOURCE 200809L
#include "ares_response.h"

#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

static const char *reason(int status)
{
    switch (status) {
        case 200: return "OK";
        case 400: return "Bad Request";
        case 403: return "Forbidden";
        case 404: return "Not Found";
        case 405: return "Method Not Allowed";
        case 408: return "Request Timeout";
        case 431: return "Request Header Fields Too Large";
        case 501: return "Not Implemented";
        default: return "Internal Server Error";
    }
}

void ares_response_init(ares_response *response)
{
    memset(response, 0, sizeof(*response));
    response->file_fd = -1;
}

void ares_response_destroy(ares_response *response)
{
    if (response->file_fd >= 0) close(response->file_fd);
    response->file_fd = -1;
}

void ares_error(int status, ares_response *response)
{
    const char *body;
    switch (status) {
        case 400: body = "400 Bad Request\n"; break;
        case 403: body = "403 Forbidden\n"; break;
        case 404: body = "404 Not Found\n"; break;
        case 405: body = "405 Method Not Allowed\n"; break;
        case 408: body = "408 Request Timeout\n"; break;
        case 431: body = "431 Request Header Fields Too Large\n"; break;
        case 501: body = "501 Unsupported HTTP Framing\n"; break;
        default: status = 500; body = "500 Internal Server Error\n";
    }
    response->status = status;
    response->content_type = "text/plain; charset=utf-8";
    response->body = body;
    response->body_length = strlen(body);
    response->allow = status == 405 ? "GET, HEAD" : NULL;
}

static int write_all(int fd, const char *data, size_t length)
{
    size_t sent = 0;
    while (sent < length) {
        ssize_t count = send(fd, data + sent, length - sent, 0);
        if (count < 0 && errno == EINTR) continue;
        if (count <= 0) return -1;
        sent += (size_t)count;
    }
    return 0;
}

static int stream_file(int client, int file_fd, size_t length)
{
    char buffer[16384];
    size_t remaining = length;
    while (remaining > 0) {
        size_t batch = remaining < sizeof(buffer) ? remaining : sizeof(buffer);
        ssize_t n = read(file_fd, buffer, batch);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return -1;
        if (write_all(client, buffer, (size_t)n) < 0) return -1;
        remaining -= (size_t)n;
    }
    return 0;
}

int ares_write_response(int fd, const ares_response *response, int head_only)
{
    if (!response || !response->content_type ||
        (response->file_fd < 0 && !response->body)) return -1;
    char headers[1024];
    char date[64];
    time_t now = time(NULL);
    struct tm utc;
    if (now == (time_t)-1 || gmtime_r(&now, &utc) == NULL ||
        strftime(date, sizeof(date), "%a, %d %b %Y %H:%M:%S GMT", &utc) == 0)
        return -1;
    int len = snprintf(headers, sizeof(headers),
        "HTTP/1.1 %d %s\r\n"
        "Date: %s\r\n"
        "Server: ARES/0.4\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %zu\r\n"
        "Connection: close\r\n"
        "Cache-Control: no-store\r\n"
        "X-Content-Type-Options: nosniff\r\n"
        "X-Frame-Options: DENY\r\n"
        "Referrer-Policy: no-referrer\r\n"
        "%s"
        "\r\n",
        response->status, reason(response->status), date,
        response->content_type, response->body_length,
        response->allow ? "Allow: GET, HEAD\r\n" : "");
    if (len < 0 || (size_t)len >= sizeof(headers)) return -1;
    if (write_all(fd, headers, (size_t)len) < 0) return -1;
    if (head_only || response->body_length == 0) return 0;
    if (response->file_fd >= 0)
        return stream_file(fd, response->file_fd, response->body_length);
    return write_all(fd, response->body, response->body_length);
}
