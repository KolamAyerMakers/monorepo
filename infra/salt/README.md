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

The [network-diagnostics pillar](pillar/roles/kam-classroom/network-diagnostics.sls) selects the diagnostic tools and traceroute port range. UDP egress to any destination on ports `33434-33534` is allowed for the identity pillar's `humans` GID. This permits all UDP traffic in that range, not only the traceroute executable. Verify diagnostics from an ordinary account after deployment.
