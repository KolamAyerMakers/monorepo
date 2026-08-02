# Discover packages without sudo

Quest: discover-packages-without-sudo

## Mission

Run `apt search ascii` and `apt show cmatrix`, then report what `cmatrix` does.

## Commands You Will Use

- `apt search`
- `apt show`

## Steps

1. Run `apt search ascii`.
2. Run `apt show cmatrix`.
3. Read the package description.
4. Answer the guide with what the package does.

## Hints

1. Searching packages is safe.
2. Installing packages is not part of learner permissions on the shared server.
3. The answer should mention Matrix-style terminal output.

## If Check Fails

Read the `Description` field from `apt show cmatrix` again.

## Related Reading

- [apt search](../commands/apt-search.md)
- [apt show](../commands/apt-show.md)
- [package-discovery](../concepts/package-discovery.md)
