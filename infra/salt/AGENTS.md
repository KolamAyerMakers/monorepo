# Classroom Salt Configuration

Salt states, pillar, custom modules, and Salt-SSH tooling for the classroom.

## Layout

- `config/`: Salt and roster configuration.
- `pillar/`: configuration data, including role-specific data.
- `states/`: Salt states, templates, static files, custom modules, and custom states.
- `tests/`: focused pytest coverage.
- `scripts/salt_runner.py`: required wrapper for local and Salt-SSH operations.

Role dispatch is grain-based. The tracked targets and their roles are in `config/roster`. Keep configuration data in pillar and actions in states.

## State Conventions

- States must be idempotent. Use explicit, narrow requisites. Do not rely on state or include order.
- States consuming pillar data must fail early with `test.check_pillar`, and dependent states must require that guard.
- Do not put service, package, port, path, or policy defaults in states or templates. Put them in pillar.
- Use `bootstrap_package_installed()` and `bootstrap_binary_package()` where their bootstrap ordering is required. Binary downloads require `github::download_egress::ready`.
- Keep templates with their state subtree unless they are deliberately shared. Convert templates that no longer render data to static files.
- Custom Salt modules belong in `states/_modules/` and custom state modules in `states/_states/`. Type public functions and provide Salt-style docstrings.

## Tests And Validation

Add focused behavioral tests for meaningful logic, trust boundaries, destructive behavior, security invariants, or regressions. Do not add source-text, pillar-snapshot, or one-test-per-file coverage.

Do not run checks before committing. The repository pre-commit hook runs:

```sh
make -C infra/salt check
```

## Salt Operations

Run Salt only through the runner from this directory:

```sh
uv run salt-runner local-test [state]
uv run salt-runner ssh-test <target> [state]
uv run salt-runner call --config-dir=config state.show_sls <state>
```

Never apply Salt without explicit instruction in the current request. This includes `local-apply`, `ssh-apply`, direct `state.apply`, and equivalent commands. Use `ssh-test` before a requested `ssh-apply`.

Do not directly install, upgrade, downgrade, or remove managed system tools. Change the relevant pillar data and apply Salt only when explicitly instructed.
