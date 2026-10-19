#include "ares_http_parser.h"
#include <stdio.h>
#include <string.h>
/* Offline parser inspection tool. Not an HTTP server; stdin only. */
int main(void)
{
    ares_parser parser;
    ares_parser_init(&parser);
    unsigned char input[256];
    size_t n;
    ares_result status = ARES_NEED_MORE;
    while ((n = fread(input, 1, sizeof(input), stdin)) != 0) {
        size_t used = 0;
        status = ares_parser_feed(&parser, input, n, &used);
        if (status == ARES_COMPLETE) {
            /* No bodies, request pipelining or bytes after headers. */
            if (used != n || fgetc(stdin) != EOF) {
                fputs("REJECT: extra bytes after headers (unsupported)\n", stderr);
                return 2;
            }
            printf("PARSE: %s\nMETHOD: %s\nTARGET: %s\nVERSION: HTTP/%u.%u\nHEADERS: %zu\n",
                   ares_result_string(status), parser.request.method,
                   parser.request.target, parser.request.major,
                   parser.request.minor, parser.request.header_count);
            for (size_t i = 0; i < parser.request.header_count; i++)
                printf("  %s: %s\n", parser.request.headers[i].name,
                       parser.request.headers[i].value);
            return 0;
        }
        if (status != ARES_NEED_MORE) {
            fprintf(stderr, "REJECT: %s\n", ares_result_string(status));
            return 2;
        }
    }
    if (ferror(stdin)) {
        perror("stdin");
        return 1;
    }
    fputs("REJECT: incomplete HTTP headers\n", stderr);
    return 2;
}
