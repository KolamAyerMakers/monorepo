# Agent Notes

## Repository

- `maker-guide/` is the learner-support application. Read `maker-guide/AGENTS.md` before changing it.
- `website/` is the public Astro website.
- `branding/` contains source brand assets.
- `infra/pulumi/` defines cloud resources. Read `infra/pulumi/README.md` before changing it.
- `infra/salt/` configures the classroom. Read `infra/salt/AGENTS.md` before changing it.
- `infra/ops/` contains manual recovery tools. Do not run them against a target without explicit instruction.

## Validation

- There is no root build or test command. Use the affected subproject command.
- Do not run checks before committing. Lefthook runs relevant checks on commit; fix and recommit only when that gate fails.
- Add checks to `lefthook.yml` and CI when adding an independently validated component.

## Safety

- Track pending repository work in `TODO.md`.
- Never run `git push` unless the user explicitly requests a push in the current conversation. A completed local commit is not permission to push.
- Do not run `pulumi up`, apply Salt, decrypt secrets, mutate deployment state, or change DNS without explicit instruction.
- Committed Pulumi `secure:` values and Age-encrypted pillar values are ciphertext configuration. Keep them tracked. Private keys and decrypted values do not belong in Git.
- CI must not contact production services, decrypt secrets, run Salt remotely, or apply Pulumi.
