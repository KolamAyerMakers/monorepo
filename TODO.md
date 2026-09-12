# TODO

- [ ] Build and deploy the updated Maker Guide artifact and classroom configuration with the operator.
- [ ] After operator deployment, validate one-task `guide now` advancement and concise `guide check` feedback on `lf-dev`.
- [x] Verify S6 DNS, HTTP, and site-check progression on `lf-dev` after deploying the hostname validation fix.
- [ ] Deploy the updated daemon and CLI together; validate S6 behavioral checks, equivalent implementations, and published guidance on `lf-dev`. Verify live site health separately.
- [ ] Verify S6 learner-only execution, timeout cleanup, stale-result rejection, source-free reports, and IRC shell guidance with the operator. Existing completions must remain unchanged.
- [ ] Change the S6 checker to accept page arguments; align behavioral checks, examples, and later-session invocations.
- [ ] Confirm the S6 start time (catalog: 2026-09-12 17:00 Asia/Singapore, 09:00 UTC).
- [ ] Preview the S6-S10 decks and complete their classroom preflights before delivery.
- [ ] Update external Forgejo, Caddy, and Classroom references after the monorepo deployment succeeds.
- [ ] Remove the Presenterm export pseudo-terminal wrapper after [the non-TTY export fix](https://github.com/mfontanini/presenterm/pull/857) is released and deployed.
- [ ] Migrate pulumi stacks to KAM account
- [ ] Migrate domain name to KAM account
- [ ] Encrypt secrets with KAM shared key
