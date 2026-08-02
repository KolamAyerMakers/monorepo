# Quotas

This state manages user filesystem quotas from pillar data.

Linux quotas apply to a filesystem, not a directory. If `/home` is not a
separate mount, the quota applies to the filesystem that contains `/home`.

## User Commands

Users can inspect their own quota with:

```sh
quota -s
```

They can inspect current disk usage in their home directory with:

```sh
du -sh "$HOME"
```

They can inspect free space on the filesystem containing their home directory
with:

```sh
df -h "$HOME"
```

If `quota -s` shows a grace period, the user is above the soft limit. They must
delete files or move below the soft limit before the grace period expires. The
hard limit cannot be exceeded.

## Admin Commands

Check which filesystem owns `/home`:

```sh
findmnt --target /home
```

Check whether user quotas are enabled on that filesystem:

```sh
quotaon -pu "$(findmnt --target /home --noheadings --output TARGET | head -n 1)"
```

Show all user quotas for the filesystem containing `/home`:

```sh
repquota -s -u "$(findmnt --target /home --noheadings --output TARGET | head -n 1)"
```

Show one user's quota:

```sh
quota -s -u alice
```

Check that NSS can resolve the group used by a quota policy:

```sh
getent group example-group
```

Re-apply the Salt-managed quota policy manually:

```sh
/usr/local/sbin/apply-user-quotas --configuration /etc/quotas/user-quotas.json
```

Apply the policy for one newly created or repaired user:

```sh
/usr/local/sbin/apply-user-quotas \
  --configuration /etc/quotas/user-quotas.json \
  --username alice \
  --user-id-number 10001 \
  --group example-group
```

Check the boot-time quota service:

```sh
systemctl status apply-user-quotas
```

Inspect quota service logs:

```sh
journalctl -u apply-user-quotas
```

## Policy Changes

Quota policy lives in pillar, not in manual `setquota` calls. Edit the pillar
file that configures the role or host using this state.

Default limits are group based. Limits are expressed in KiB:

```yaml
quotas:
  filesystems:
    home:
      path: /home
      group_defaults:
        example-group:
          soft_block_limit_kib: 1572864
          hard_block_limit_kib: 2097152
      user_overrides: {}
```

Per-user overrides go under `user_overrides`:

```yaml
quotas:
  filesystems:
    home:
      path: /home
      group_defaults:
        example-group:
          soft_block_limit_kib: 1572864
          hard_block_limit_kib: 2097152
      user_overrides:
        alice:
          soft_block_limit_kib: 3145728
          hard_block_limit_kib: 4194304
```

After changing pillar, apply Salt normally:

```sh
./scripts/run_salt.py ssh-apply <target>
```

## Manual Overrides

Manual `setquota` changes are temporary. The next Salt run, boot-time service
run, or account creation helper can set the user back to the pillar policy.

Use manual `setquota` only for emergency repair:

```sh
setquota -u alice 1572864 2097152 0 0 /home
```

If `/home` is not a separate mount, replace `/home` with the mount point shown
by:

```sh
findmnt --target /home --noheadings --output TARGET
```
