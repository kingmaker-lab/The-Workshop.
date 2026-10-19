CC ?= cc
CPPFLAGS ?= -D_POSIX_C_SOURCE=200809L -Iinclude -I../http-parser/include
CFLAGS ?= -std=c17 -O2 -Wall -Wextra -Wpedantic -Werror
LDFLAGS ?=
SOURCES := src/main.c src/server.c src/response.c src/router.c ../http-parser/src/ares_http_parser.c
HEADERS := include/ares_response.h ../http-parser/include/ares_http_parser.h
.PHONY: all run test clean
all: build/ares
build/ares: $(SOURCES) $(HEADERS)
	@mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -o $@ $(SOURCES)
run: all
	./build/ares
test: all
	python3 -m unittest discover -s tests -v
clean:
	rm -rf build
