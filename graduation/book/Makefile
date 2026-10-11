SOURCE ?= $(HOME)/Books/Julia Evans Wizard Zines
OUTPUT ?= local/proofs

.PHONY: all build preflight print check

all: build

build:
	uv run assemble.py "$(SOURCE)" --output "$(OUTPUT)"
	uv run preflight.py "$(SOURCE)" --output "$(OUTPUT)"

preflight:
	uv run preflight.py "$(SOURCE)" --output "$(OUTPUT)"

# Export existing approved-layout proofs; no purchased files are used by CI.
print:
	uv run print_export.py --input "$(OUTPUT)" --output local/print

check:
	uv run ruff check
	uv run ruff format --check
	uv run basedpyright
	uv run pytest test_assembly.py
