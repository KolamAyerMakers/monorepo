SOURCE ?= $(HOME)/Books/Julia Evans Wizard Zines
OUTPUT ?= local/proofs

.PHONY: all build preflight check

all: build

build:
	uv run assemble.py "$(SOURCE)" --output "$(OUTPUT)"
	uv run preflight.py "$(SOURCE)" --output "$(OUTPUT)"

preflight:
	uv run preflight.py "$(SOURCE)" --output "$(OUTPUT)"

check:
	uv run ruff check
	uv run ruff format --check
	uv run basedpyright
	uv run pytest test_assembly.py
