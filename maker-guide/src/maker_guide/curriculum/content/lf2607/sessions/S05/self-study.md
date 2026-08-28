# S5 Self-Study Guide: Make The Shell Work For You

Session: S5

## Study Path

1. Save three familiar commands in one file and watch Bash run them in order.
2. Try `./maker-report.sh` before changing permissions and observe `Permission denied`.
3. Read the permission triplets, add execute permission for yourself, and run the file directly.
4. Accept one title argument and preserve its spaces with quotes.
5. Generate a complete Markdown report with one grouped redirection.
6. Publish the generated report as HTML.

The same `~/scripts/maker-report.sh` improves at every stage. Its final job is concrete:

```text
maker-report.sh -> maker-report.md -> build-website -> maker-report.html
```

## Preflight

Run these commands on the remote classroom shell:

```bash
whoami
hostname
date
mkdir -p ~/scripts
build-website
ls -ld ~/scripts ~/src/pages
```

The first three commands answer which account, machine, and time you are using. Let the first site build finish. After this release it may refresh locked packages once; later builds reuse them.

If `npm ci` fails, check the network and rerun `build-website`; the dependency refresh will retry.

If all of `~/src` is missing, run `build-website` once. If only `~/src/pages` is missing, first inspect the class marker:

```bash
ls -l ~/src/.astro-starter-marker
```

If the marker exists, run `mkdir -p ~/src/pages`. If `~/src` exists without the marker, stop and ask for help so you do not overwrite another project.

## Exercise 1: Save Known Commands

Move to the script directory and open one new file:

```bash
cd ~/scripts
micro maker-report.sh
```

Inside Micro, type this exact file:

```bash
#!/bin/bash

# Show the account and computer running this script.
whoami
hostname

# Show the current date and time.
date
```

Lines beginning with `#` are comments for people, so Bash skips them. The first line is a special exception called a shebang; Exercise 2 explains it.

Save with `Ctrl-S`, quit with `Ctrl-Q`, inspect, and run it:

```bash
cat maker-report.sh
bash maker-report.sh
```

`bash maker-report.sh` explicitly starts Bash and gives it the text file. Bash reads each saved line from top to bottom. This route does not need execute permission on the file.

Now turn on Bash's execution trace:

```bash
bash -x maker-report.sh
```

Lines beginning with `+` show commands Bash is about to run. Normal command output has no `+`. The trace goes to stderr, so it remains visible even when stdout is redirected later.

## Exercise 2: Direct Execution

You are still in `~/scripts`. Before changing permissions, try the current-directory path:

```bash
./maker-report.sh
```

Expected result: `Permission denied`.

`.` means the current directory, so `./maker-report.sh` names the file here. `./` identifies the file; it does not give permission to run it.

Inspect the permission string:

```bash
ls -l maker-report.sh
```

Read a result such as `-rw-r--r--` in groups:

```text
- rw- r-- r--
  ^^^
  permissions for the user who owns the file
```

You created this file, so you are its owning user. `rw-` means you may read and write it. The missing `x` means you may not execute it.

Add only that permission and inspect the change:

```bash
chmod u+x maker-report.sh
ls -l maker-report.sh
```

Read `u+x` as: `u` is the owning user, `+` means add, and `x` means execute. Your triplet changes from `rw-` to `rwx`.

The first line you already typed is called a shebang:

```bash
#!/bin/bash
```

It tells Linux to use `/bin/bash` to read and run this file. It must be the first line. Later lines beginning with `#` are ordinary comments.

Verify the shebang and run directly:

```bash
head -n 1 maker-report.sh
ls -l maker-report.sh
./maker-report.sh
```

Compare direct execution with explicitly starting Bash:

```bash
bash maker-report.sh
./maker-report.sh
```

## Exercise 3: One Reusable Input

Run one value after the script path:

```bash
./maker-report.sh "My Maker Report"
```

Inside a script, `$1` is the first argument after the path. Open `micro maker-report.sh` and add these lines after the shebang:

```bash
report_title="$1"
printf 'title=<%s>\n' "$report_title"
```

`%s` is one string slot and `\n` ends the line. If Bash `printf` receives extra values, it reuses the format for each one. That behavior makes the later quoting mistake visible as several headings.

The assignment has no spaces around `=`. This is assignment:

```bash
report_title="$1"
```

This is not assignment:

```bash
report_title = "$1"
```

With spaces, Bash treats `report_title` as a command name.

Save and compare two calls:

```bash
./maker-report.sh My Maker Report
./maker-report.sh "My Maker Report"
```

The first call gives `$1` only `My`. The second gives it one value containing spaces.

Keep the call quoted. In Micro, compare these two lines one at a time:

```bash
printf '# %s\n' $report_title
printf '# %s\n' "$report_title"
```

The unquoted expansion can print three headings because `printf` receives three values. Restore the quoted expansion. Leave this intermediate script on disk:

```bash
#!/bin/bash

report_title="$1"

printf '# %s\n\n' "$report_title"
whoami
hostname
date
```

Save, then run the unquoted and quoted forms once more. Leave the quoted form working.

## Final Project: Generate A Markdown Report

The target file should contain this plain-text structure:

````markdown
# My Maker Report

* User: learner
* Host: classroom
* Date: ...

## Shell fields in /etc/passwd

```text
/bin/bash
/usr/sbin/nologin
...
```
````

`#` and `##` create headings. `*` starts a list item. Triple backticks on lines by themselves open and close a fenced code block; the optional `text` labels its contents as plain text. To print a fence, use a single-quoted value such as `printf '%s\n' '```text'`: single quotes make the backticks ordinary output, not a Bash command. The exact shell list varies by machine.

Rebuild the data pipeline at the prompt before putting it in the script:

```bash
cut -d: -f7 /etc/passwd
cut -d: -f7 /etc/passwd | sort -u
```

The pipeline splits local `/etc/passwd` entries on `:`, keeps field seven, sorts the values, and removes duplicates. It does not enumerate learners stored in the classroom identity service.

Open `micro maker-report.sh` and replace the temporary report body with these commands, without braces or redirection yet:

````bash
printf '# %s\n\n' "$report_title"
printf '* User: '
whoami
printf '* Host: '
hostname
printf '* Date: '
date
printf '\n## Shell fields in /etc/passwd\n\n'
printf '%s\n' '```text'
cut -d: -f7 /etc/passwd | sort -u
printf '%s\n' '```'
````

Save, check syntax, and keep the output visible once:

```bash
bash -n maker-report.sh
./maker-report.sh "My Maker Report"
```

`bash -n` checks Bash syntax without running the commands. It normally prints nothing when the syntax is valid.

Continue only when the terminal shows one heading, three labeled lines, one subheading, and one closed code block.

Now make the script write the file itself. Put `{` before the first report `printf`. Put this after the final `printf`:

```bash
} > ~/src/pages/maker-report.md
```

The braces group many commands into one stdout stream. The single `>` sends that whole stream to one file. Errors remain visible because stderr was not redirected.

The complete script is:

````bash
#!/bin/bash

report_title="$1"

{
  printf '# %s\n\n' "$report_title"
  printf '* User: '
  whoami
  printf '* Host: '
  hostname
  printf '* Date: '
  date
  printf '\n## Shell fields in /etc/passwd\n\n'
  printf '%s\n' '```text'
  cut -d: -f7 /etc/passwd | sort -u
  printf '%s\n' '```'
} > ~/src/pages/maker-report.md
````

Check, generate, inspect, and publish:

```bash
bash -n maker-report.sh
./maker-report.sh "S5 Report"
cat ~/src/pages/maker-report.md
build-website
ls -l ~/public_html/maker-report.html
```

Open [your report page](https://lf2607.kolamayermakers.org/~your-handle/maker-report.html), replacing `your-handle` with your account name. The new page is not automatically linked from your homepage.

Rerunning the script replaces the generated Markdown. Rerun `build-website` after every report generation to refresh the HTML.

## Restart Or Reset

The generation step is repeatable. Normally, fix the script and run it again.

To restart only S5 from blank files, inspect each exact path before removing it:

```bash
ls -l ~/scripts/maker-report.sh ~/src/pages/maker-report.md
rm -i ~/scripts/maker-report.sh ~/src/pages/maker-report.md
build-website
```

Do not remove `~/scripts`, `~/src`, `~/src/pages`, or `~/public_html`.

This resets files only. It does not erase durable course progress.

## Troubleshooting

| Symptom | Check | Repair |
|---|---|---|
| Micro changes do not appear | `cat ~/scripts/maker-report.sh` | Save with `Ctrl-S`, then quit with `Ctrl-Q`. |
| `Permission denied` | `ls -l ~/scripts/maker-report.sh` | Run `chmod u+x ~/scripts/maker-report.sh`. |
| `bad interpreter` | `head -n 1 ~/scripts/maker-report.sh` | Make the first line exactly `#!/bin/bash`. |
| `maker-report.sh: command not found` | `pwd` | From `~/scripts`, use `./maker-report.sh`; elsewhere, use `~/scripts/maker-report.sh`. |
| `report_title: command not found` | Inspect the assignment | Remove spaces around `=`. |
| Title is only `My` | Inspect the invocation | Put quotes around `"My Maker Report"`. |
| One title becomes several headings | Inspect the `printf` argument | Use `"$report_title"`, including the quotes. |
| Markdown file is absent or partial | `bash -x maker-report.sh "Debug Report"` | Read the last traced command, repair it, then rerun the script. |
| `~/src/pages` is missing | `ls -l ~/src/.astro-starter-marker` | If the marker exists, run `mkdir -p ~/src/pages`; otherwise ask for help. |
| Build succeeds but page is absent | `ls -l ~/src/pages/maker-report.md` | Rerun the script, then `build-website`, then inspect `~/public_html/maker-report.html`. |

## Proof Checklist

- `bash maker-report.sh` runs saved commands from `~/scripts`.
- `bash -x maker-report.sh` reveals the command sequence.
- `./maker-report.sh` means the executable file in the current directory.
- The script starts with `#!/bin/bash`, and your permission triplet contains `x`.
- `report_title="$1"` has no spaces around `=`.
- A quoted multi-word title remains one heading.
- One grouped redirection makes the script write `~/src/pages/maker-report.md`.
- The Markdown contains a triple-backtick `text` block.
- `build-website` creates `~/public_html/maker-report.html`.

## Optional Appendix: When Bash Stops

This unscored lab takes about 15 minutes. Keep it in `~/playground`; do not add these options to `maker-report.sh` yet.

Create `~/playground/options-demo.sh`:

```bash
#!/bin/bash
set -u

report_title="$1"

printf 'title=<%s>\n' "$report_title"
printf 'before failure\n'
ls /no/such/s5-path
printf 'after failure\n'
```

Make it executable:

```bash
chmod u+x ~/playground/options-demo.sh
```

Before each run, predict the last line that will execute.

First, omit the argument:

```bash
~/playground/options-demo.sh
```

Expect a diagnostic containing `unbound variable`. `$1` is unset, so `set -u` stops the script before the title is printed. An explicitly supplied empty argument, `""`, is set and does not trigger `-u`.

Now supply a title:

```bash
~/playground/options-demo.sh "Options Demo"
```

The `ls` command reports failure, but `after failure` is still printed. `set -u` reacts to unset values, not failed commands. Because stdout and stderr are separate, displayed line ordering can vary; look only for `after failure`.

Add this immediately after `set -u`:

```bash
set -e
```

Rerun with the title. This time `after failure` is not printed. In this exact straight-line script, `set -e` exits when the standalone `ls` command returns nonzero.

`set -e` is not a universal "stop on every error" rule. Commands tested by `if`, `while`, or `until`, non-final commands in `&&` and `||` lists, commands under `!`, and non-final pipeline stages have exceptions. S6 introduces the control flow needed to handle expected failures explicitly.

Do not add `set -u` to the final report before it has a deliberate missing-title check. Do not assume `set -e` makes every pipeline safe.

## Docs Pointers

- Run `man bash`, then search for `SHELL SCRIPTS` and `INVOCATION`.
- Run `help printf`.
- Read [Shell Scripting](../../concepts/shell-scripting.md).
- Read [Shebang](../../concepts/shebang.md).
- Read [Script Permissions](../../concepts/script-permissions.md).
- Read [Path](../../concepts/path.md).
- Read [Variables](../../concepts/variables.md).
- Read [Script Arguments](../../concepts/script-arguments.md).
- Read [Stream Redirection](../../concepts/stream-redirection.md).
- Read [`set`](../../commands/set.md) only after completing the optional appendix.
