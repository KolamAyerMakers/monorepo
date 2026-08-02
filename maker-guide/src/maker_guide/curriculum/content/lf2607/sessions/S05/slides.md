# Linux Foundations S5

Session: S5

Scripting begins

<!-- end_slide -->

# Today's Story

If you type it twice, teach the machine to type it for you.

Teacher writes the first tiny script live, then learners write their own.

<!-- end_slide -->

# Hands-On Spine

Hands-on now: build one script, run it, break it, fix it.

```bash
#!/bin/bash
set -euo pipefail
printf 'Hello %s\n' "$1"
printf 'status=%s\n' "$?"
read name
```

<!-- end_slide -->

# Exit Goal

Learners write and run their first useful shell script.
<!-- end_slide -->

# Between-Session Practice Route

Highly recommended after class or for catch-up:

Use the guide throughout class and between sessions: run `guide now` for your current session objective; after you complete it, it shows your current quest. Submit prompted answers with `guide answer 'your answer'`, and run `guide check` after practical work. A passing check records your progress.

1. Write `~/scripts/hello.sh` with `$1`.
2. Replace `echo` with `printf`.
3. Build `info.sh` from known commands.
4. Use `read` for interactive input.
5. Reverse two arguments deliberately.

<!-- end_slide -->

# Script Rules

Start with a shebang.

Exit status: `0` means success, nonzero means failure.

Prefer `printf`.

Quote variables unless you can explain why not.
