CC ?= cc
CPPFLAGS ?= -D_POSIX_C_SOURCE=200809L
CFLAGS ?= -std=c17 -O2 -Wall -Wextra -Wpedantic -Werror
LDFLAGS ?=

TARGET := build/ares-tcp
.PHONY: all run test clean
all: $(TARGET)

$(TARGET): src/main.c
	@mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -o $@ $<

run: all
	./$(TARGET)

test: all
	python3 -m unittest discover -s tests -v

clean:
	rm -rf build
