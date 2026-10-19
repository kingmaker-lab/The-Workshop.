CC ?= cc
CPPFLAGS ?= -Iinclude
CFLAGS ?= -std=c17 -O2 -Wall -Wextra -Wpedantic -Werror
LDFLAGS ?=
.PHONY: all test clean demo
all: build/ares-http-inspect
build/ares-http-inspect: src/main.c src/ares_http_parser.c include/ares_http_parser.h
	@mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -o $@ src/main.c src/ares_http_parser.c
build/test_parser: tests/test_parser.c src/ares_http_parser.c include/ares_http_parser.h
	@mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -o $@ tests/test_parser.c src/ares_http_parser.c
test: build/test_parser build/ares-http-inspect
	./build/test_parser
	python3 -m unittest discover -s tests -p 'test_cli.py' -v
demo: all
	printf 'GET /health HTTP/1.1\r\nHost: localhost\r\nUser-Agent: ARES-Lab\r\n\r\n' | ./build/ares-http-inspect
clean:
	rm -rf build
