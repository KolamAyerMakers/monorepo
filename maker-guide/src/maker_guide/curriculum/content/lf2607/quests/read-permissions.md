# Read permissions

Quest: read-permissions

## Mission

Run `ls -l ~/playground/hi.txt` and explain the owner permission bits.

## Commands You Will Use

- `ls -l`

## Steps

1. Run `ls -l ~/playground/hi.txt`.
2. Read the first permission triplet after the file type character.
3. Decide whether the owner can read, write, or execute the file.
4. Answer the guide in words.

## Hints

1. The first character is file type.
2. The next three characters are owner permissions.
3. For a normal text file, expect read and write, not execute.

## If Check Fails

Run `ls -l` again and answer with read, write, or execute permissions for the owner.

## Related Reading

- [ls -l](../commands/ls-l.md)
- [permissions](../concepts/permissions.md)
