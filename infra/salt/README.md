# Classroom Salt Operations

`config/roster` is the tracked static Salt-SSH inventory. Each target supplies its host, SSH settings, deployment environment, and `roles` grain. Add future hosts there without changing the role dispatcher.

The Age private identity is not in Git. Obtain it through the existing secret-management process, or provide `AGE_IDENTITY` or `AGE_IDENTITY_FILE` for local commands. Encrypted pillar files remain committed ciphertext.

From the repository root, build the deployment artifact and run a dry-run against the tracked `lf2607` target:

```sh
make -C infra/salt maker-guide-artifact
uv --directory infra/salt run salt-runner ssh-test lf2607
```

Review the dry-run before applying. It does not execute `nft -c` or verify connectivity. For firewall changes, keep a recovery console and an existing SSH session available. Apply only with explicit authorization:

```sh
uv --directory infra/salt run salt-runner ssh-apply lf2607
```

The live state validates rules before starting or reloading nftables. CI does not decrypt pillar data or contact managed hosts.

## Network Diagnostics

The [network-diagnostics pillar](pillar/roles/kam-classroom/network-diagnostics.sls) selects the diagnostic tools and traceroute port range, including `procps` for `ps`, `iproute2` for `ss`, and `netcat-openbsd` for `nc -C -N -w`. UDP egress to any destination on ports `33434-33534` is allowed for the identity pillar's `humans` GID. This permits all UDP traffic in that range, not only the traceroute executable. Verify diagnostics from an ordinary account after deployment.

## Shared Caddy

The [Caddy pillar](pillar/caddy.sls) places the shared administration endpoint at `unix//run/caddy/admin.sock`. The service owns a private `0700` runtime directory and uses a `0077` umask. Its systemd reload command explicitly targets that socket, not the default TCP admin endpoint. Applying the migration restarts shared Caddy; a missing socket triggers recovery on later applications even if the files are unchanged. Schedule that interruption and verify ordinary learner accounts cannot access the shared admin endpoint afterward.

Learner routes reconcile on every Salt application, after Caddy and participant initialization. The root-only `refresh-learner-routes` command locks a stable file before rendering and skips reload only when the routes match and no previous publication is pending. Validation and reload failures restore the previous routes. The `.pending` backup remains until a successful reload, so an interrupted publication is retried rather than mistaken for an already-loaded configuration. If restoration itself fails, preserve that backup for recovery. Missing legacy POSIX accounts produce a warning on stderr and no route; their UID lookup is retried later without blocking other routes.

Learner `caddy file-server` processes remain separate from shared Caddy. Their assigned ports are not opened externally. Verify the deployed IPv4/IPv6 firewall and all included fragments before relying on wildcard listeners, then exercise local HTTP, personal HTTPS, and independent static delivery in a practice account.

## Participant Lingering

The [identity pillar](pillar/roles/kam-classroom/identity.sls) explicitly selects `linux-foundations` members in the reserved UID range `10000-20999` for lingering and installs `libpam-systemd` and `dbus-user-session`. The root-only `/usr/local/sbin/kam-classroom-lingering` helper reads `/etc/kam-classroom-lingering.json`, resolves explicit group members through NSS, and enables lingering idempotently. Salt reconciles existing participants; learner creation and `--resume` reconcile the new account before refreshing its routes. The daemon remains unprivileged.

Account deletion disables scoped lingering before deleting the identity; full classroom reset does so before stopping LDAP. Before removing a participant from the policy group or changing that group, an authorized operator must disable that participant's lingering while the old membership still resolves. Reconciliation does not revoke unrelated or former members' administrator-managed settings.

Lingering preserves the user manager, not arbitrary processes started in an SSH session. Learners must still enable their own units. After authorized deployment, check each participant's effective `Linger` value and test an enabled service after closing every login session. No live logout or reboot behavior is established by these declarations alone.

## Learner Journals

The [systemd pillar](pillar/roles/kam-classroom/systemd.sls) enables persistent journals with `SplitMode=uid`. Salt creates `/var/log/journal` as `root:systemd-journal` with mode `2755`, restarts journald when either the directory or its configuration changes, then runs `journalctl --flush` if this boot has no `/run/systemd/journal/flushed` marker. The flush is not restricted to configuration changes, so reapplying activates an unflushed boot even when the earlier configuration is already installed. Salt checks that the flush produced its marker; a failed command or missing marker fails the state, and an absent marker allows retry on the next application. The marker is systemd's flush bookkeeping, not proof of learner access or healthy storage. No manual restart or flush is part of deployment.

Journald grants each ordinary UID read access to its own journal through file ACLs. Learners are not added to `adm` or `systemd-journal`, and system journals are not made world-readable. Splitting applies to new records after activation: flushing existing runtime records copies them into the system journal, not into per-user journals. A learner with no new records may still have no user journal to read.

After authorized deployment, verify fresh user-service output and `journalctl --user -u` access as `ss79`, plus denial of another learner's journal and the system journal. Confirm the actual machine identity first: the roster defines separate `lf2607` and `lf-dev` targets, and a root prompt on one does not establish deployment on the other. If fresh records remain inaccessible on the confirmed host, inspect the effective journald configuration, learner UID, storage health, and journal ACLs. These live conditions are not established by Salt render tests. See the upstream [journald storage and splitting documentation](https://www.freedesktop.org/software/systemd/man/latest/journald.conf.html).

## Local Checks

The commit gate requires Caddy 2 on `PATH` for the shared-admin regression. It starts an isolated HTTP-only loopback server with a private Unix admin socket; it does not invoke systemd or contact the classroom. Route-refresh tests stub privileged commands while exercising real temporary files and locks. CI already installs Caddy before the Salt checks. Follow the repository's commit-gate validation policy.
