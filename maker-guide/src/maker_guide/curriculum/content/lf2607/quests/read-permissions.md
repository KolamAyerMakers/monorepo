# Read permissions

Quest: read-permissions

## Mission

From `~/playground`, run `ls -l permission-demo.txt` and explain its file type plus the owner, group, and other permission triplets.

## Commands You Will Use

- `ls -l`

## Steps

1. Run `cd ~/playground`.
2. Run `touch permission-demo.txt`.
3. Run `ls -l permission-demo.txt`.
4. Identify the first character as the file type.
5. Read the owner, group, and other triplets.
6. Answer the guide with what each class can do.

## Hints

1. `-` means regular file and `d` means directory.
2. The next three characters are owner permissions.
3. The next two triplets belong to group and other users.

## If Check Fails

Run `ls -l` again and name the file type plus what owner, group, and other users can do.

## Related Reading

- [ls -l](../commands/ls-l.md)
- [permissions](../concepts/permissions.md)
