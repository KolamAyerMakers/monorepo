# Read permissions

Quest: read-permissions

## Mission

From `~/playground`, add owner execute permission to `permission-demo.txt`, then run `ls -l permission-demo.txt` and explain its file type plus the owner, group, and other permission triplets.

## Commands You Will Use

- `chmod`
- `ls -l`

## Steps

1. Run `mkdir -p ~/playground`, then `cd ~/playground`.
2. Run `touch permission-demo.txt`.
3. Run `ls -l permission-demo.txt`.
4. Run `chmod u+x permission-demo.txt`, then `ls -l permission-demo.txt` again.
5. Identify the first character as the file type and read the owner, group, and other triplets.
6. Answer the guide with what each class can do in this final state.

A file that started with `-rw-r--r--` now has this permission string:

```text
-rwxr--r-- 1 username username 0 Aug 8 10:00 permission-demo.txt
```

The owner's `rwx` allows reading, writing, and execution. `chmod u+x` does not change group or other permissions. Read your actual listing if those triplets differ.

## Hints

1. `-` means regular file and `d` means directory.
2. The next three characters are owner permissions.
3. The next two triplets belong to group and other users.

## If Check Fails

Run `chmod u+x permission-demo.txt` and `ls -l permission-demo.txt` again. Name the file type plus what owner, group, and other users can do in that listing.

## Related Reading

- [ls -l](../commands/ls-l.md)
- [chmod](../commands/chmod.md)
- [permissions](../concepts/permissions.md)
