#include "ares_response.h"
#include <string.h>
/* Static lab routes; no filesystem reads, template evaluation, or user input echo. */
static const char index_body[] =
    "ARES v0.3 — Responses & Routing\n"
    "Build. Break. Understand. Rebuild.\n"
    "GET /, /health, /about\n";
static const char health_body[] = "{\"status\":\"ok\",\"server\":\"ares\",\"version\":\"0.3\"}\n";
static const char about_body[] = "ARES HTTP/1.1 lab: TCP + Parser v0.2 + Responses & Routing v0.3\n";
void ares_route(const ares_request *request, ares_response *response)
{
    if (strcmp(request->method, "GET") != 0 && strcmp(request->method, "HEAD") != 0) {
        ares_error(405, response);
        return;
    }
    const char *body = NULL;
    const char *type = "text/plain; charset=utf-8";
    if (strcmp(request->target, "/") == 0) body = index_body;
    else if (strcmp(request->target, "/health") == 0) {
        body = health_body;
        type = "application/json; charset=utf-8";
    } else if (strcmp(request->target, "/about") == 0) body = about_body;
    if (body == NULL) {
        ares_error(404, response);
        return;
    }
    response->status = 200;
    response->content_type = type;
    response->body = body;
    response->body_length = strlen(body);
    response->allow = NULL;
}
