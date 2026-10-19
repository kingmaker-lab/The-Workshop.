#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int ares_serve(uint16_t port);
int main(int argc, char **argv)
{
    uint16_t port = 8080;
    if (argc != 1) {
        if (argc != 3 || strcmp(argv[1], "--port") != 0 ||
            argv[2][0] == '-' || argv[2][0] == '\0') {
            fprintf(stderr, "Usage: %s [--port 0..65535]\n", argv[0]);
            return 2;
        }
        char *end;
        errno = 0;
        unsigned long parsed = strtoul(argv[2], &end, 10);
        if (errno != 0 || *end != '\0' || parsed > UINT16_MAX) {
            fprintf(stderr, "Invalid port\n");
            return 2;
        }
        port = (uint16_t)parsed;
    }
    return ares_serve(port);
}
