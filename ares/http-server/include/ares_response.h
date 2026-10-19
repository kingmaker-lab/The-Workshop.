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
    int file_fd; /* -1: in-memory response; >= 0: bounded regular-file response. */
} ares_response;

void ares_response_init(ares_response *response);
void ares_response_destroy(ares_response *response);
void ares_route(int public_fd, const ares_request *request, ares_response *response);
void ares_error(int status, ares_response *response);
int ares_write_response(int fd, const ares_response *response, int head_only);
int ares_static_open(int public_fd, const char *target, ares_response *response);

#endif
