# Build a playground

Quest: build-playground

## Mission

Create `~/playground/`, create `one.txt`, `two.txt`, and `three.txt` inside it, and list them with `ls -l`.

## Why This Matters

You need a safe place to practice. A playground directory is where you can create, inspect, and remove files without touching your homepage source.

## Commands You Will Use

- `mkdir`
- `touch`
- `ls -l`

## Steps

1. Run `mkdir -p ~/playground`.
2. Run `touch ~/playground/one.txt`.
3. Run `touch ~/playground/two.txt`.
4. Run `touch ~/playground/three.txt`.
5. Run `ls -l ~/playground`.
6. Ask the guide to check your work.

## Hints

1. Create the directory before creating files inside it.
2. `touch` can create an empty file.
3. The guide checks for `one.txt`, `two.txt`, and `three.txt` inside `~/playground`.

## If Check Fails

Run `ls -l ~/playground` and compare the listing with the required names. Missing files need another `touch` command. If the guide cannot traverse your home directory, run `chmod 711 ~` yourself, then ask it to check again.

## Related Reading

- [mkdir](../commands/mkdir.md)
- [touch](../commands/touch.md)
- [ls -l](../commands/ls-l.md)
- [file-creation](../concepts/file-creation.md)
