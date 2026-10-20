# jobs

## Use

```bash
jobs
```

## What It Does

`jobs` lists jobs controlled by your current shell.

## Practice

Run `sleep 60`, press `Ctrl-Z`, then run `jobs`. Expect a stopped job with a bracketed job number. Run `fg`, then press `Ctrl-C` to stop the sleep.

## Watch Out

Jobs are per shell. A different terminal may not show the same jobs.
