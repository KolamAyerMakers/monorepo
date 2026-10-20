# Command: `touch`

Create an empty file or update a file timestamp.

```bash
work=$(mktemp -d)
touch "$work/one.txt"
ls -l "$work/one.txt"
```

Use it as the simplest way to make practice files.

Expect a file of size `0`. On an existing file, `touch` updates timestamps without emptying the content.
