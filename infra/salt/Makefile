SALT_LINT_TARGETS ?= $(shell find states pillar -name '*.sls' -print)
RUFF_CHECK_TARGETS ?= scripts states tests
RUFF_FORMAT_TARGETS ?= scripts states tests
MAKER_GUIDE_SOURCE ?= $(abspath ../..)/maker-guide
MAKER_GUIDE_ARTIFACT_DIRECTORY ?= $(MAKER_GUIDE_SOURCE)/dist/venv

.PHONY: help check salt-lint ruff-check ruff-format basedpyright pytest maker-guide-artifact

check: salt-lint ruff-check ruff-format basedpyright pytest ## Run the full SaltStack validation suite

salt-lint: ## Run salt-lint on Salt states and pillar data
	uv run salt-lint $(SALT_LINT_TARGETS)

ruff-check: ## Run Ruff checks on Python sources
	uv run ruff check $(RUFF_CHECK_TARGETS)

ruff-format: ## Verify Ruff formatting on Python sources
	uv run ruff format --check $(RUFF_FORMAT_TARGETS)

basedpyright: ## Run basedpyright type checking
	uv run basedpyright -p pyproject.toml states tests

pytest: ## Run the SaltStack test suite
	uv run pytest -x -q

maker-guide-artifact: ## Rebuild and import the Maker Guide venv tarball
	$(MAKE) -C "$(MAKER_GUIDE_SOURCE)" venv-artifact
	@set -- "$(MAKER_GUIDE_ARTIFACT_DIRECTORY)"/maker-guide.*.tar.gz; [ "$$#" -eq 1 ] && [ -f "$$1" ] || { printf 'Expected one Maker Guide artifact\n'; exit 1; }; \
	artifact_path="$$1"; \
	install -d -m 0755 states/roles/kam-classroom/files/maker-guide; \
	rm -f states/roles/kam-classroom/files/maker-guide/maker-guide*; \
	install -m 0644 "$$artifact_path" states/roles/kam-classroom/files/maker-guide/"$${artifact_path##*/}"
