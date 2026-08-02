# Classroom Salt Operations

`config/roster` is the tracked static Salt-SSH inventory. Each target supplies its host, SSH settings, deployment environment, and `roles` grain. Add future hosts there without changing the role dispatcher.

The Age private identity is not in Git. Obtain it through the existing secret-management process, or provide `AGE_IDENTITY` or `AGE_IDENTITY_FILE` for local commands. Encrypted pillar files remain committed ciphertext.

Build the deployment artifact from this repository, then apply it manually:

```sh
make -C infra/salt maker-guide-artifact
uv --directory infra/salt run salt-runner ssh-apply classroom
```

Use `ssh-test` before `ssh-apply` for a remote rendering pass. CI does not decrypt pillar data or contact managed hosts.
