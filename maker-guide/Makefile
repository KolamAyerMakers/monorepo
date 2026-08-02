SHELL := /bin/bash

VENV_DIRECTORY := dist/venv
VENV_ARTIFACT_LABEL := $(shell git describe --always | tr -d '\n' | tr -cs '[:alnum:]._' '-')

.PHONY: venv-artifact clean-venv-artifact

venv-artifact:
	@artifact_label="$(VENV_ARTIFACT_LABEL)"; \
	if [[ -n "$$(git --work-tree=.. status --porcelain --untracked-files=normal)" ]]; then \
		artifact_label="$$artifact_label-dirty.$$(date +%s%N)"; \
	fi; \
	install -d -m 0755 $(VENV_DIRECTORY); \
	./scripts/build-venv-artifact $(VENV_DIRECTORY) "$$artifact_label"

clean-venv-artifact:
	rm -rf $(VENV_DIRECTORY)
