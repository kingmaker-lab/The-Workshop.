#include "ares_http_parser.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned checks = 0;

static ares_result parse_chunks(const void *input, size_t length, size_t chunk,
                                ares_parser *output, size_t *total)
{
    ares_parser_init(output);
    size_t offset = 0;
    ares_result status = ARES_NEED_MORE;
    while (offset < length) {
        size_t span = length - offset;
        if (span > chunk) span = chunk;
        size_t consumed = 0;
        status = ares_parser_feed(output, (const unsigned char *)input + offset,
                                  span, &consumed);
        assert(consumed <= span);
        offset += consumed;
        if (status != ARES_NEED_MORE) break;
    }
    *total = offset;
    return status;
}

static void expect(const char *name, const void *input, size_t length,
                   ares_result expected)
{
    size_t chunks[] = {1, 2, 3, 7, 128, 16384};
    for (size_t i = 0; i < sizeof(chunks) / sizeof(chunks[0]); i++) {
        ares_parser p;
        size_t consumed = 0;
        ares_result actual = parse_chunks(input, length, chunks[i], &p, &consumed);
        if (actual != expected) {
            fprintf(stderr, "FAIL %s (chunk=%zu): expected %s got %s\n",
                    name, chunks[i], ares_result_string(expected),
                    ares_result_string(actual));
            exit(1);
        }
        if (expected == ARES_COMPLETE) {
            assert(consumed <= length);
            assert(p.request.major == 1);
        }
        checks++;
    }
}
#define EXPECT(name, literal, result) expect(name, literal, sizeof(literal) - 1u, result)

static void valid_requests(void)
{
    EXPECT("HTTP11 minimal", "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n", ARES_COMPLETE);
    EXPECT("HTTP10 minimal", "GET / HTTP/1.0\r\n\r\n", ARES_COMPLETE);
    EXPECT("HEAD & query", "HEAD /status?x=1 HTTP/1.1\r\nhOsT: example.test\r\n\r\n", ARES_COMPLETE);
    EXPECT("extensions", "SOME-METHOD /path HTTP/1.1\r\nHost: localhost\r\nX-Foo: alpha beta\r\n\r\n", ARES_COMPLETE);
    EXPECT("zero content-length", "POST / HTTP/1.1\r\nHost: localhost\r\nContent-Length: 0\r\n\r\n", ARES_COMPLETE);
    EXPECT("empty header value", "GET / HTTP/1.1\r\nHost: localhost\r\nX-Empty: \r\n\r\n", ARES_COMPLETE);
    EXPECT("trim optional whitespace", "GET / HTTP/1.1\r\nHOST:  localhost \t\r\nX-Test:\t A \t\r\n\r\n", ARES_COMPLETE);
    const char raw[] = "GET /foo?q=2 HTTP/1.1\r\nHost: Example.Test\r\nX-Foo: Bar\r\n\r\n";
    ares_parser p;
    size_t consumed;
    assert(parse_chunks(raw, sizeof(raw) - 1, 2, &p, &consumed) == ARES_COMPLETE);
    assert(consumed == sizeof(raw) - 1);
    assert(strcmp(p.request.method, "GET") == 0);
    assert(strcmp(p.request.target, "/foo?q=2") == 0);
    assert(p.request.minor == 1);
    assert(p.request.header_count == 2);
    assert(strcmp(ares_header_get(&p.request, "host"), "Example.Test") == 0);
    assert(strcmp(ares_header_get(&p.request, "x-foo"), "Bar") == 0);
    assert(ares_header_get(&p.request, "does-not-exist") == NULL);
    checks += 8;
}

static void invalid_requests(void)
{
    EXPECT("missing host", "GET / HTTP/1.1\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("duplicate host", "GET / HTTP/1.1\r\nHost: a\r\nHost: b\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("blank host", "GET / HTTP/1.1\r\nHost: \r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("spaced host", "GET / HTTP/1.1\r\nHost: bad host\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("userinfo host", "GET / HTTP/1.1\r\nHost: admin@example.com\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("bad http version", "GET / HTTP/2.0\r\nHost: a\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("bare LF", "GET / HTTP/1.1\nHost: a\n\n", ARES_NEED_MORE);
    EXPECT("bad method", "GE[T / HTTP/1.1\r\nHost: a\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("bad method spaces", "GET  / HTTP/1.1\r\nHost: a\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("missing target", "GET  HTTP/1.1\r\nHost: a\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("absolute-form unsupported", "GET http://x/ HTTP/1.1\r\nHost: x\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("asterisk unsupported", "OPTIONS * HTTP/1.1\r\nHost: a\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("target fragment", "GET /foo#bar HTTP/1.1\r\nHost: a\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("target NUL", "GET /a\0b HTTP/1.1\r\nHost: a\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("header without colon", "GET / HTTP/1.1\r\nHost a\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("header colon spacing", "GET / HTTP/1.1\r\nHost : a\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("obs-fold", "GET / HTTP/1.1\r\nHost: a\r\n folded\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("header NUL", "GET / HTTP/1.1\r\nHost: a\r\nX: hi\0there\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("header CR", "GET / HTTP/1.1\r\nHost: a\r\nX: hello\rworld\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("high ASCII unsupported", "GET / HTTP/1.1\r\nHost: a\r\nX: \xff\r\n\r\n", ARES_BAD_REQUEST);
    EXPECT("transfer encoding", "POST / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n", ARES_UNSUPPORTED_BODY);
    EXPECT("positive length", "POST / HTTP/1.1\r\nHost: a\r\nContent-Length: 5\r\n\r\n", ARES_UNSUPPORTED_BODY);
    EXPECT("zero padded length", "POST / HTTP/1.1\r\nHost: a\r\nContent-Length: 00\r\n\r\n", ARES_UNSUPPORTED_BODY);
    EXPECT("duplicate content length", "POST / HTTP/1.1\r\nHost: a\r\nContent-Length: 0\r\nContent-Length: 0\r\n\r\n", ARES_UNSUPPORTED_BODY);
    EXPECT("expect continue", "POST / HTTP/1.1\r\nHost: a\r\nExpect: 100-continue\r\n\r\n", ARES_UNSUPPORTED_BODY);
    EXPECT("incomplete", "GET / HTTP/1.1\r\nHost: a\r\n", ARES_NEED_MORE);
    EXPECT("empty input", "", ARES_NEED_MORE);
}

static void boundaries_and_state(void)
{
    char request[20000];
    size_t off = 0;
    const char *head = "GET / HTTP/1.1\r\nHost: a\r\n";
    memcpy(request, head, strlen(head));
    off = strlen(head);
    for (size_t i = 0; i < ARES_MAX_HEADERS - 1; i++) {
        memcpy(request + off, "X-A: x\r\n", 8);
        off += 8;
    }
    memcpy(request + off, "\r\n", 2);
    off += 2;
    expect("32 headers allowed", request, off, ARES_COMPLETE);
    off -= 2;
    memcpy(request + off, "X-B: x\r\n\r\n", 10);
    off += 10;
    expect("33 headers rejected", request, off, ARES_TOO_MANY_HEADERS);
    off = 0;
    memcpy(request, head, strlen(head));
    off = strlen(head);
    memcpy(request + off, "X-A: ", 5);
    off += 5;
    memset(request + off, 'b', ARES_MAX_VALUE);
    off += ARES_MAX_VALUE;
    memcpy(request + off, "\r\n\r\n", 4);
    off += 4;
    expect("max value allowed", request, off, ARES_COMPLETE);
    request[off - 4] = 'b';
    request[off - 3] = '\r';
    request[off - 2] = '\n';
    request[off - 1] = '\r';
    request[off++] = '\n';
    expect("oversized value", request, off, ARES_TOO_LARGE);
    memset(request, 'X', sizeof(request));
    expect("header byte limit", request, sizeof(request), ARES_TOO_LARGE);
    const char pipelined[] = "GET / HTTP/1.1\r\nHost: x\r\n\r\nGET /next HTTP/1.1\r\nHost: x\r\n\r\n";
    ares_parser parser;
    size_t used = 0;
    assert(ares_parser_feed(NULL, pipelined, 3, &used) == ARES_INVALID_STATE);
    ares_parser_init(&parser);
    assert(ares_parser_feed(&parser, pipelined, sizeof(pipelined) - 1, &used) == ARES_COMPLETE);
    assert(used < sizeof(pipelined) - 1);
    assert(ares_parser_feed(&parser, pipelined, 1, &used) == ARES_INVALID_STATE);
    ares_parser_init(&parser);
    assert(parser.used == 0 && parser.state == ARES_NEED_MORE);
    checks += 5;
}

static void randomized_fragmentation(void)
{
    const char msg[] = "GET /test?value=1 HTTP/1.1\r\nHost: localhost\r\nX-Trace: abc\r\n\r\n";
    unsigned seed = 0x51a7u;
    for (size_t trial = 0; trial < 1000; trial++) {
        ares_parser parser;
        ares_parser_init(&parser);
        size_t off = 0;
        while (off < sizeof(msg) - 1) {
            seed = seed * 1664525u + 1013904223u;
            size_t chunk = (seed % 17u) + 1u;
            size_t left = sizeof(msg) - 1 - off;
            if (chunk > left) chunk = left;
            size_t used;
            ares_result r = ares_parser_feed(&parser, msg + off, chunk, &used);
            assert(used == chunk);
            off += used;
            if (off < sizeof(msg) - 1) assert(r == ARES_NEED_MORE);
            else assert(r == ARES_COMPLETE);
        }
        checks++;
    }
    unsigned char bytes[512];
    for (size_t trial = 0; trial < 1500; trial++) {
        seed = seed * 1664525u + 1013904223u;
        size_t len = seed % sizeof(bytes);
        for (size_t i = 0; i < len; i++) {
            seed = seed * 1664525u + 1013904223u;
            bytes[i] = (unsigned char)(seed >> 24);
        }
        ares_parser parser;
        size_t used;
        ares_parser_init(&parser);
        ares_result status = ares_parser_feed(&parser, bytes, len, &used);
        assert(status == ARES_NEED_MORE || status == ARES_COMPLETE || status < 0);
        assert(used <= len);
        checks++;
    }
}

int main(void)
{
    valid_requests();
    invalid_requests();
    boundaries_and_state();
    randomized_fragmentation();
    printf("ARES HTTP Parser v0.2: %u checks passed\n", checks);
    return 0;
}
