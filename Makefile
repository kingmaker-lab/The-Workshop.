.PHONY: help setup build test test-ares test-ares-tcp test-ares-http test-argus test-raven \
	run-ares run-ares-tcp run-ares-http-demo run-argus run-raven clean status \
	build-local test-local run-local

.DEFAULT_GOAL := help

ARES_MAKEFILE := $(wildcard ares/Makefile)

CC ?= cc
CPPFLAGS ?= -D_POSIX_C_SOURCE=200809L -Iinclude
CFLAGS ?= -std=c11 -Wall -Wextra -Wpedantic -Werror -O2
LDFLAGS ?=

BUILD_DIR := .build
VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip

SERVER_SOURCES := src/main.c src/server.c src/http_parser.c src/response.c src/router.c
SERVER_OBJECTS := $(SERVER_SOURCES:src/%.c=$(BUILD_DIR)/%.o)

help:
	@echo "THE WORKSHOP"
	@echo "============"
	@echo "make setup       Install/setup project dependencies"
	@echo "make build       Build all components"
	@echo "make test        Run the complete test suite"
	@echo "make test-ares   Run ARES tests (HTTP + TCP Foundation + parser v0.2)"
	@echo "make test-ares-tcp  Run TCP Foundation integration tests"
	@echo "make test-ares-http Run HTTP Parser v0.2 tests"
	@echo "make test-argus  Run ARGUS tests"
	@echo "make test-raven  Run RAVEN tests"
	@echo "make run-ares    Run ARES locally"
	@echo "make run-ares-tcp Run isolated TCP v0.1 locally"
	@echo "make run-ares-http-demo Inspect an HTTP request offline (v0.2)"
	@echo "make run-argus   Run ARGUS locally"
	@echo "make run-raven   Run RAVEN locally"
	@echo "make clean       Remove generated artifacts"
	@echo "make status      Show Workshop component status"

setup:
	@echo "[WORKSHOP] Setting up Python environment..."
	python3 -m venv $(VENV_DIR)
	$(PIP) install -r argus/requirements.txt
	@echo "[WORKSHOP] Checking Ruby toolchain..."
	@if ! command -v ruby >/dev/null 2>&1; then \
		echo "[ERROR] Ruby is not installed. Install Ruby and Bundler before running RAVEN."; \
		exit 1; \
	fi
	@if ! command -v bundle >/dev/null 2>&1; then \
		echo "[ERROR] Bundler is not installed. Install bundler or run the system package manager for Ruby."; \
		exit 1; \
	fi
	cd raven && bundle install

build:
ifneq ($(strip $(ARES_MAKEFILE)),)
	$(MAKE) -C ares
else
	$(MAKE) build-local
endif

test: test-ares test-argus test-raven
	@echo ""
	@echo "[WORKSHOP] All test suites passed."

test-ares:
	@echo "[ARES] Running C tests..."
ifneq ($(strip $(ARES_MAKEFILE)),)
	$(MAKE) -C ares test
else
	$(MAKE) test-local
endif

	$(MAKE) -C ares/tcp-foundation test
	$(MAKE) -C ares/http-parser test

test-ares-tcp:
	$(MAKE) -C ares/tcp-foundation test

test-ares-http:
	$(MAKE) -C ares/http-parser test

test-argus:
	@echo "[ARGUS] Running Python tests..."
	$(PYTHON) -m unittest discover -s argus/tests -v

test-raven:
	@echo "[RAVEN] Running Ruby tests..."
	@if ! command -v bundle >/dev/null 2>&1; then \
		echo "[ERROR] Ruby/Bundler is required for RAVEN. Run 'make setup' after installing Ruby and Bundler."; \
		exit 1; \
	fi
	cd raven && bundle exec rspec

run-ares:
ifneq ($(strip $(ARES_MAKEFILE)),)
	$(MAKE) -C ares run
else
	$(MAKE) run-local
endif

run-ares-tcp:
	$(MAKE) -C ares/tcp-foundation run

run-ares-http-demo:
	$(MAKE) -C ares/http-parser demo

run-argus:
	$(PYTHON) -m argus.main serve

run-raven:
	cd raven && bin/raven --rules rules --input samples/auth.jsonl

clean:
	$(MAKE) -C ares/http-parser clean
	$(MAKE) -C ares/tcp-foundation clean
ifneq ($(strip $(ARES_MAKEFILE)),)
	$(MAKE) -C ares clean
endif
	rm -rf $(BUILD_DIR) $(VENV_DIR)
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

status:
	@echo ""
	@echo "THE WORKSHOP"
	@echo "============"
	@echo "ARES      [ ACTIVE ]  C"
	@echo "ARGUS     [ ACTIVE ]  Python"
	@echo "RAVEN     [ ACTIVE ]  Ruby"
	@echo "CERBERUS  [ LOCKED ]  Integration"
	@echo ""

build-local: $(BUILD_DIR)/ares

$(BUILD_DIR)/ares: $(SERVER_OBJECTS)
	$(CC) $(LDFLAGS) -o $@ $^

$(BUILD_DIR)/%.o: src/%.c | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c -o $@ $<

$(BUILD_DIR):
	mkdir -p $@

$(BUILD_DIR)/test_parser: tests/test_parser.c src/http_parser.c | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ $^

test-local: $(BUILD_DIR)/test_parser
	./$(BUILD_DIR)/test_parser

run-local: build-local
	./$(BUILD_DIR)/ares
