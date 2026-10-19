#define _POSIX_C_SOURCE 200809L
#include "ares_response.h"

#include <errno.h>
#include <fcntl.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

/* The static directory is trusted and not writable by network clients.
   Resolve relative paths descriptor-by-descriptor; never follow symlinks. */
#define ARES_MAX_STATIC_BYTES (256u * 1024u)
#define ARES_MAX_STATIC_PATH 1024u

static const char *mime_type(const char *name)
{
    const char *dot = strrchr(name, '.');
    if (!dot) return NULL;
    if (strcmp(dot, ".html") == 0) return "text/html; charset=utf-8";
    if (strcmp(dot, ".css") == 0) return "text/css; charset=utf-8";
    if (strcmp(dot, ".js") == 0) return "text/javascript; charset=utf-8";
    if (strcmp(dot, ".json") == 0) return "application/json; charset=utf-8";
    if (strcmp(dot, ".txt") == 0) return "text/plain; charset=utf-8";
    if (strcmp(dot, ".svg") == 0) return "image/svg+xml";
    if (strcmp(dot, ".png") == 0) return "image/png";
    if (strcmp(dot, ".jpg") == 0 || strcmp(dot, ".jpeg") == 0) return "image/jpeg";
    if (strcmp(dot, ".webp") == 0) return "image/webp";
    if (strcmp(dot, ".ico") == 0) return "image/x-icon";
    return NULL;
}

static int safe_character(unsigned char c)
{
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
           (c >= '0' && c <= '9') || c == '_' || c == '-' || c == '.';
}

/* No percent decoding. Reject any ambiguous or reserved URL syntax.
   This strict subset intentionally excludes queries, backslashes and dotfiles. */
static int valid_path(const char *relative)
{
    size_t length = strlen(relative);
    if (length == 0 || length > ARES_MAX_STATIC_PATH) return 0;
    const char *part = relative;
    for (size_t i = 0; i <= length; ++i) {
        if (relative[i] == '/' || relative[i] == '\0') {
            size_t part_length = (size_t)(&relative[i] - part);
            if (part_length == 0 || part[0] == '.') return 0;
            part = relative + i + 1;
        } else if (!safe_character((unsigned char)relative[i])) {
            return 0;
        }
    }
    return 1;
}

int ares_static_open(int public_fd, const char *target, ares_response *response)
{
    const char *prefix = "/static/";
    size_t prefix_length = strlen(prefix);
    if (public_fd < 0 || strncmp(target, prefix, prefix_length) != 0)
        return 404;
    const char *relative = target + prefix_length;
    if (!valid_path(relative)) return 404;

    char path[ARES_MAX_STATIC_PATH + 1u];
    memcpy(path, relative, strlen(relative) + 1u);
    char *segment = path;
    int current = public_fd; /* The caller retains ownership of this fd. */
    int owned = -1;
    for (;;) {
        char *slash = strchr(segment, '/');
        if (slash) *slash = '\0';
        if (!slash && mime_type(segment) == NULL) {
            if (owned >= 0) close(owned);
            return 404;
        }
        int flags = O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK;
        if (slash) flags |= O_DIRECTORY;
        int next = openat(current, segment, flags);
        if (owned >= 0) close(owned);
        owned = -1;
        if (next < 0) return 404; /* Never disclose filesystem state. */
        if (slash) {
            owned = next;
            current = next;
            segment = slash + 1;
            continue;
        }
        struct stat st;
        if (fstat(next, &st) < 0 || !S_ISREG(st.st_mode)) {
            close(next);
            return 404;
        }
        if (st.st_size < 0 || (uintmax_t)st.st_size > ARES_MAX_STATIC_BYTES) {
            close(next);
            return 403;
        }
        response->status = 200;
        response->content_type = mime_type(segment);
        response->body = NULL;
        response->body_length = (size_t)st.st_size;
        response->allow = NULL;
        response->file_fd = next;
        return 200;
    }
}
