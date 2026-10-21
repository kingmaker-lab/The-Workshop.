CC ?= cc
CFLAGS ?= -std=c11 -O2 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror
CPPFLAGS ?= -Iinclude
BIN := build/wolfvm

.PHONY: all examples test clean sanitize
all: $(BIN)

$(BIN): src/main.c src/wolfvm.c include/wolfvm.h
	@mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) src/main.c src/wolfvm.c -o $(BIN)

examples: $(BIN)
	@mkdir -p build/examples
	python3 tools/assemble.py examples/arith.wva -o build/examples/arith.wvm
	python3 tools/assemble.py examples/function.wva -o build/examples/function.wvm
	python3 tools/assemble.py examples/loop.wva -o build/examples/loop.wvm
	python3 tools/assemble.py examples/memory.wva -o build/examples/memory.wvm

test: examples
	python3 -m unittest discover -s tests -v

sanitize:
	$(MAKE) clean
	$(MAKE) CFLAGS='-std=c11 -O1 -g -Wall -Wextra -Wpedantic -Wconversion -Wshadow -fsanitize=address,undefined -fno-omit-frame-pointer' test

clean:
	rm -rf build
