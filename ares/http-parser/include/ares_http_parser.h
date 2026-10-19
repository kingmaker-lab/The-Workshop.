#ifndef ARES_HTTP_PARSER_H
#define ARES_HTTP_PARSER_H
#include <stddef.h>
#define ARES_MAX_HEADER_BYTES 8192u
#define ARES_MAX_REQUEST_LINE 2048u
#define ARES_MAX_HEADER_LINE 2048u
#define ARES_MAX_HEADERS 32u
#define ARES_MAX_METHOD 16u
#define ARES_MAX_TARGET 2048u
#define ARES_MAX_NAME 64u
#define ARES_MAX_VALUE 1024u
typedef enum {
    ARES_NEED_MORE = 0,
    ARES_COMPLETE = 1,
    ARES_BAD_REQUEST = -1,
    ARES_TOO_LARGE = -2,
    ARES_TOO_MANY_HEADERS = -3,
    ARES_UNSUPPORTED_BODY = -4,
    ARES_INVALID_STATE = -5
} ares_result;
typedef struct {
    char name[ARES_MAX_NAME + 1];
    char value[ARES_MAX_VALUE + 1];
} ares_header;
typedef struct {
    char method[ARES_MAX_METHOD + 1];
    char target[ARES_MAX_TARGET + 1];
    unsigned major;
    unsigned minor;
    size_t header_count;
    ares_header headers[ARES_MAX_HEADERS];
} ares_request;
typedef struct {
    unsigned char buffer[ARES_MAX_HEADER_BYTES];
    size_t used;
    ares_result state;
    ares_request request;
} ares_parser;
void ares_parser_init(ares_parser *parser);
ares_result ares_parser_feed(ares_parser *parser, const void *data,
                             size_t length, size_t *consumed);
const char *ares_result_string(ares_result result);
const char *ares_header_get(const ares_request *request, const char *name);
#endif
