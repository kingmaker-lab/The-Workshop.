#ifndef ARES_RESPONSE_H
#define ARES_RESPONSE_H
#include <stddef.h>
#include "ares_http_parser.h"
typedef struct {
    int status;
    const char *content_type;
    const char *body;
    size_t body_length;
    const char *allow;
} ares_response;
void ares_route(const ares_request *request, ares_response *response);
void ares_error(int status, ares_response *response);
int ares_write_response(int fd, const ares_response *response, int head_only);
#endif
