# Keep a pipeline copy

Quest: keep-pipeline-copy

## Mission

Extract login shells, save the stream with `tee`, and count its lines.

## Commands You Will Use

- `mkdir`
- `cut`
- `tee`
- `wc`
- `cat`

This quest also uses pipe syntax.

## Steps

1. Run `mkdir -p ~/playground` if the directory is missing.
2. Run `cut -d: -f7 /etc/passwd | tee ~/playground/login-shells.txt | wc -l`.
3. Run `cat ~/playground/login-shells.txt` and confirm it contains shell paths.
4. Ask the guide to check your work.

## Hints

1. `cut -d: -f7` selects the login-shell field.
2. `tee` copies stdin to the file and also sends it onward through stdout.
3. The exact pipeline and `~/playground/login-shells.txt` are both checked.

## If Check Fails

- If the command is missing, run the complete pipeline exactly as shown.
- If the file is missing or empty, run each stage alone, then reconnect the pipeline.
- If `~/playground` is missing, create it with `mkdir -p ~/playground`.

## Related Reading

- [pipes](../concepts/pipes.md)
- [tee](../commands/tee.md)
- [cut](../commands/cut.md)
- [wc](../commands/wc.md)
