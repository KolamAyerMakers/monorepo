# Command: `rmdir`

Remove an empty directory.

```bash
work=$(mktemp -d)
mkdir "$work/empty-directory"
rmdir "$work/empty-directory"
ls -la "$work"
```

If the directory contains files, `rmdir` refuses. That refusal is useful safety.
