# tee

## Use

```bash
cut -d: -f7 /etc/passwd | tee ~/playground/login-shells.txt | wc -l
```

## What It Does

`tee` is a T-junction: it copies stdin to a file and also sends it onward through stdout.

## Practice

Use it when a stream must continue to another pipeline stage and also be saved.

## Watch Out

Plain `tee file` replaces the file. Use `tee -a file` to append.

## Docs Pointers

- Run `man tee`.
- Read [pipes](../concepts/pipes.md) and [stream redirection](../concepts/stream-redirection.md).
