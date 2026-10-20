# fg

## Use

```bash
fg
```

## What It Does

`fg` brings a background or stopped job back to the foreground.

## Practice

Run `sleep 60`, press `Ctrl-Z`, then run `jobs` and `fg`. The sleep returns to the foreground; press `Ctrl-C` to stop it. With multiple jobs, `fg %1` selects shell job number `1`, not process ID `1`.

## Watch Out

Foreground jobs take over your terminal until they finish, stop, or exit.
