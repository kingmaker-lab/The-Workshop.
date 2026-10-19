#include "ares_response.h"
#include <string.h>

static const char index_body[] =
    "ARES v0.4 — Static Files\n"
    "Build. Break. Understand. Rebuild.\n"
    "GET /, /health, /about, /static/index.html\n";
static const char health_body[] =
    "{\"status\":\"ok\",\"server\":\"ares\",\"version\":\"0.4\"}\n";
static const char about_body[] =
    "ARES HTTP/1.1 lab: TCP + HTTP Parser v0.2 + routing v0.3 + files v0.4\n";

void ares_route(int public_fd, const ares_request *request, ares_response *response)
{
    if (strcmp(request->method, "GET") != 0 &&
        strcmp(request->method, "HEAD") != 0) {
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
    else if (strncmp(request->target, "/static", 7) == 0) {
        int result = ares_static_open(public_fd, request->target, response);
        if (result != 200) ares_error(result, response);
        return;
    }
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
