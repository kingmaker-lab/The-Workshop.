#include "ares_http_parser.h"
#include <string.h>

static int token(unsigned char c)
{
    if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
        (c >= '0' && c <= '9')) return 1;
    return strchr("!#$%&'*+-.^_`|~", (int)c) != NULL;
}

static int ascii_equal(const char *a, const char *b)
{
    while (*a && *b) {
        unsigned char x = (unsigned char)*a++;
        unsigned char y = (unsigned char)*b++;
        if (x >= 'A' && x <= 'Z') x = (unsigned char)(x + 32);
        if (y >= 'A' && y <= 'Z') y = (unsigned char)(y + 32);
        if (x != y) return 0;
    }
    return *a == 0 && *b == 0;
}

static int copy_checked(char *dst, size_t capacity,
                        const unsigned char *src, size_t len)
{
    if (len == 0 || len >= capacity) return 0;
    memcpy(dst, src, len);
    dst[len] = 0;
    return 1;
}

static ares_result parse_start_line(ares_request *request,
                                    const unsigned char *line, size_t len)
{
    if (len == 0 || len > ARES_MAX_REQUEST_LINE) return ARES_BAD_REQUEST;
    size_t first = 0;
    while (first < len && line[first] != ' ') first++;
    if (first == len || first == 0) return ARES_BAD_REQUEST;
    size_t second = first + 1;
    while (second < len && line[second] != ' ') second++;
    if (second == len || second == first + 1) return ARES_BAD_REQUEST;
    for (size_t i = 0; i < first; i++) if (!token(line[i])) return ARES_BAD_REQUEST;
    if (!copy_checked(request->method, sizeof(request->method), line, first) ||
        !copy_checked(request->target, sizeof(request->target),
                      line + first + 1, second - first - 1)) return ARES_BAD_REQUEST;
    if (request->target[0] != '/') return ARES_BAD_REQUEST;
    for (size_t i = first + 1; i < second; i++) {
        if (line[i] < 0x21 || line[i] > 0x7e || line[i] == '#') return ARES_BAD_REQUEST;
    }
    size_t version_length = len - second - 1;
    const unsigned char *version = line + second + 1;
    if (version_length != 8 || memcmp(version, "HTTP/1.", 7) != 0 ||
        (version[7] != '0' && version[7] != '1')) return ARES_BAD_REQUEST;
    request->major = 1;
    request->minor = (unsigned)(version[7] - '0');
    return ARES_COMPLETE;
}

static ares_result parse_header_line(ares_request *request,
                                     const unsigned char *line, size_t len,
                                     int *host_seen, int *length_seen)
{
    if (len == 0 || len > ARES_MAX_HEADER_LINE) return ARES_BAD_REQUEST;
    if (request->header_count >= ARES_MAX_HEADERS) return ARES_TOO_MANY_HEADERS;
    if (line[0] == ' ' || line[0] == '\t') return ARES_BAD_REQUEST;
    size_t colon = 0;
    while (colon < len && line[colon] != ':') colon++;
    if (colon == 0 || colon == len || colon > ARES_MAX_NAME) return ARES_BAD_REQUEST;
    for (size_t i = 0; i < colon; i++) if (!token(line[i])) return ARES_BAD_REQUEST;
    size_t start = colon + 1;
    while (start < len && (line[start] == ' ' || line[start] == '\t')) start++;
    size_t end = len;
    while (end > start && (line[end - 1] == ' ' || line[end - 1] == '\t')) end--;
    if (end - start > ARES_MAX_VALUE) return ARES_TOO_LARGE;
    for (size_t i = start; i < end; i++) {
        unsigned char c = line[i];
        if (!(c == '\t' || (c >= 0x20 && c <= 0x7e))) return ARES_BAD_REQUEST;
    }
    ares_header *out = &request->headers[request->header_count];
    memcpy(out->name, line, colon);
    out->name[colon] = 0;
    memcpy(out->value, line + start, end - start);
    out->value[end - start] = 0;
    if (ascii_equal(out->name, "host")) {
        if (*host_seen || start == end) return ARES_BAD_REQUEST;
        for (size_t i = start; i < end; i++) {
            if (line[i] == ' ' || line[i] == '\t' || line[i] == ',' ||
                line[i] == '/' || line[i] == '@') return ARES_BAD_REQUEST;
        }
        *host_seen = 1;
    }
    if (ascii_equal(out->name, "transfer-encoding")) return ARES_UNSUPPORTED_BODY;
    if (ascii_equal(out->name, "content-length")) {
        if (*length_seen || (end - start) != 1 || line[start] != '0')
            return ARES_UNSUPPORTED_BODY;
        *length_seen = 1;
    }
    if (ascii_equal(out->name, "expect")) return ARES_UNSUPPORTED_BODY;
    request->header_count++;
    return ARES_COMPLETE;
}

static ares_result parse_headers(ares_request *request,
                                 const unsigned char *data, size_t len)
{
    memset(request, 0, sizeof(*request));
    size_t offset = 0;
    size_t line_number = 0;
    int host_seen = 0;
    int length_seen = 0;
    while (offset < len) {
        size_t stop = offset;
        while (stop + 1 < len && !(data[stop] == '\r' && data[stop + 1] == '\n')) stop++;
        if (stop + 1 >= len) return ARES_BAD_REQUEST;
        size_t line_length = stop - offset;
        if (line_number == 0) {
            ares_result r = parse_start_line(request, data + offset, line_length);
            if (r != ARES_COMPLETE) return r;
        } else if (line_length == 0) {
            if (stop + 2 != len) return ARES_BAD_REQUEST;
            return (request->minor == 1 && !host_seen) ? ARES_BAD_REQUEST : ARES_COMPLETE;
        } else {
            ares_result r = parse_header_line(request, data + offset, line_length,
                                              &host_seen, &length_seen);
            if (r != ARES_COMPLETE) return r;
        }
        line_number++;
        offset = stop + 2;
    }
    return ARES_BAD_REQUEST;
}

void ares_parser_init(ares_parser *parser)
{
    if (parser == NULL) return;
    memset(parser, 0, sizeof(*parser));
    parser->state = ARES_NEED_MORE;
}

ares_result ares_parser_feed(ares_parser *parser, const void *data,
                             size_t length, size_t *consumed)
{
    if (consumed != NULL) *consumed = 0;
    if (parser == NULL || consumed == NULL || (length != 0 && data == NULL))
        return ARES_INVALID_STATE;
    if (parser->state != ARES_NEED_MORE) return ARES_INVALID_STATE;
    const unsigned char *bytes = data;
    for (size_t i = 0; i < length; i++) {
        if (parser->used == sizeof(parser->buffer)) {
            parser->state = ARES_TOO_LARGE;
            return parser->state;
        }
        parser->buffer[parser->used++] = bytes[i];
        (*consumed)++;
        size_t n = parser->used;
        if (n >= 4 && parser->buffer[n - 4] == '\r' &&
            parser->buffer[n - 3] == '\n' && parser->buffer[n - 2] == '\r' &&
            parser->buffer[n - 1] == '\n') {
            parser->state = parse_headers(&parser->request, parser->buffer, n);
            return parser->state;
        }
    }
    return ARES_NEED_MORE;
}

const char *ares_header_get(const ares_request *request, const char *name)
{
    if (request == NULL || name == NULL) return NULL;
    for (size_t i = 0; i < request->header_count; i++) {
        if (ascii_equal(request->headers[i].name, name))
            return request->headers[i].value;
    }
    return NULL;
}

const char *ares_result_string(ares_result result)
{
    switch (result) {
        case ARES_NEED_MORE: return "NEED_MORE";
        case ARES_COMPLETE: return "COMPLETE";
        case ARES_BAD_REQUEST: return "BAD_REQUEST";
        case ARES_TOO_LARGE: return "TOO_LARGE";
        case ARES_TOO_MANY_HEADERS: return "TOO_MANY_HEADERS";
        case ARES_UNSUPPORTED_BODY: return "UNSUPPORTED_BODY";
        case ARES_INVALID_STATE: return "INVALID_STATE";
        default: return "UNKNOWN";
    }
}
