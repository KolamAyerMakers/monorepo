# bg

## Use

```bash
bg
```

## What It Does

`bg` resumes a stopped job in the background.

## Practice

Run `sleep 60`, press `Ctrl-Z`, then run `jobs` and `bg`. The job changes from stopped to running. Bring it back with `fg` and press `Ctrl-C` to finish the experiment.

## Watch Out

Background jobs still belong to your shell. Use tmux for durable work.
