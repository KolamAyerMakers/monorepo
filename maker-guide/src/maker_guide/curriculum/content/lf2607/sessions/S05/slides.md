# Linux Foundations S5

Session: S5

Scripting begins

<!-- end_slide -->

# Today: Build A Command That Writes A Web Page

You will create one file:

```text
~/scripts/maker-report.sh
```

First it will print your account, computer, and date.

By the end, this command:

```bash
./maker-report.sh "S5 Report"
```

will write `maker-report.md` for your website.

Every exercise improves the same file.

<!-- end_slide -->

# Start With The Report Data

Run the three commands that will become your first report:

```bash
whoami      # Which account am I using?
hostname    # Which computer am I on?
date        # What time does this computer report?
```

Right now, you must type three commands.

Saving them in a script will turn those three steps into one repeatable command.

<!-- end_slide -->

# Prepare The Two Directories

The script will live in `~/scripts`.

The page it creates will live in `~/src/pages`.

```bash
mkdir -p ~/scripts
build-website
ls -ld ~/scripts ~/src/pages
```

`build-website` creates the website files if needed. `ls -ld` verifies that both directories are ready.

<!-- end_slide -->

# Build This Exact Script

At the prompt:

```bash
cd ~/scripts
micro maker-report.sh
```

Inside Micro:

```bash
#!/bin/bash

# Show the account and computer running this script.
whoami
hostname

# Show the current date and time.
date
```

Lines beginning with `#` are notes for people. Bash skips them. We will explain the special first line soon.

<!-- end_slide -->

# Exercise 1: Run The Saved File

Save with `Ctrl-S`, quit with `Ctrl-Q`, then inspect the file:

```bash
cat maker-report.sh
```

Ask Bash to run it:

```bash
bash maker-report.sh
```

Bash reads the saved file from top to bottom:

```text
whoami -> hostname -> date
```

This route does not require execute permission.

<!-- end_slide -->

# Bash Has X-Ray Vision

Run the same file with tracing enabled:

```bash
bash -x maker-report.sh
```

Expected shape:

```text
+ whoami
learner
+ hostname
classroom
+ date
...
```

Lines beginning with `+` show what Bash is about to run. The other lines are normal command output.

<!-- end_slide -->

# Exercise 2: Try Running The File Directly

Do not change permissions yet. Run:

```bash
./maker-report.sh
```

Expected result:

```text
Permission denied
```

Read the path:

```text
.                  current directory
/                  path separator
./maker-report.sh  the file named maker-report.sh here
```

`./` identifies the file. It does not give permission to run it.

<!-- end_slide -->

# Read The File Permissions

Inspect the file:

```bash
ls -l maker-report.sh
```

Expected permission shape:

```text
- rw- r-- r--
  ^^^
  permissions for the user who owns the file
```

You created this file, so you are its owning user.

`rw-` means you may read and write it. The missing `x` explains `Permission denied`.

<!-- end_slide -->

# Add Execute Permission For Yourself

Run:

```bash
chmod u+x maker-report.sh
ls -l maker-report.sh
```

Read `u+x` one character at a time:

```text
u  the user who owns the file
+  add a permission
x  permission to execute the file
```

Expected change:

```text
before: rw-
after:  rwx
```

<!-- end_slide -->

# Why The First Line Is Special

Your script already starts with:

```bash
#!/bin/bash
```

This special first line is called a shebang.

It tells Linux: use `/bin/bash` to read and run this file.

It must be the first line.

Later lines beginning with `#` are ordinary comments for people.

<!-- end_slide -->

# Exercise 2: Verify And Run

Verify both requirements:

```bash
head -n 1 maker-report.sh
ls -l maker-report.sh
```

You should see:

```text
first line:              #!/bin/bash
your permission triplet: rwx
```

Now run the file directly:

```bash
./maker-report.sh
```

<!-- end_slide -->

# One Script, Different Titles

Run a value after the script path:

```bash
./maker-report.sh "My Maker Report"
                  ^^^^^^^^^^^^^^^^^
                  first argument
```

Inside the script, `$1` means the first argument supplied after the path.

Temporarily print it:

```bash
printf 'first=<%s>\n' "$1"
```

`%s` is one string slot. `\n` ends the line. If `printf` receives extra values, it reuses the format.

<!-- end_slide -->

# Assignment Has No Spaces

Give `$1` a readable name:

```bash
report_title="$1"
```

Read that exact token:

```text
report_title  variable name
=             assignment, touching both sides
"$1"          value to store
```

This is wrong:

```bash
report_title = "$1"
```

With spaces, Bash tries to run a command named `report_title`.

<!-- end_slide -->

# Quotes At The Call Site

Keep this probe inside the script:

```bash
printf 'title=<%s>\n' "$report_title"
```

Compare:

```bash
./maker-report.sh My Maker Report
./maker-report.sh "My Maker Report"
```

Expected probes:

```text
title=<My>
title=<My Maker Report>
```

Quotes make three words arrive as one argument.

<!-- end_slide -->

# Quotes Inside The Script

Keep the call quoted. Compare these lines inside the script:

```bash
printf '# %s\n' $report_title
printf '# %s\n' "$report_title"
```

Without quotes:

```text
# My
# Maker
# Report
```

With quotes:

```text
# My Maker Report
```

Restore the quoted expansion.

<!-- end_slide -->

# Exercise 3: Personalize It

Leave this intermediate script on disk:

```bash
#!/bin/bash

report_title="$1"

printf '# %s\n\n' "$report_title"
whoami
hostname
date
```

Compare an unquoted and quoted title, then leave the quoted form working:

```bash
./maker-report.sh My Maker Report
./maker-report.sh "My Maker Report"
```

<!-- end_slide -->

# Read The Markdown Target

The script will create this plain-text structure:

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

Triple backticks on lines by themselves open and close a code block. The optional `text` labels its contents as plain text. Use single quotes when printing them so Bash treats the backticks as ordinary output. The shell list varies by computer.

<!-- end_slide -->

# Rebuild One Useful Pipeline

Run each stage at the prompt first:

```bash
cut -d: -f7 /etc/passwd
cut -d: -f7 /etc/passwd | sort -u
```

Read it left to right:

```text
split on : -> keep field 7 -> sort -> remove duplicates
```

The result shows shell fields from local `/etc/passwd` entries. It does not list every classroom learner.

<!-- end_slide -->

# Bash Magic: Redirect A Whole Block

Braces turn several commands into one output source:

```bash
{
  printf '# Demo\n'
  whoami
  hostname
} > ~/src/pages/maker-report.md
```

The single `>` applies to output from every command inside the braces.

```text
many commands -> one output stream -> one file
```

Errors still appear in the terminal because only normal output was redirected.

<!-- end_slide -->

# The Complete Report Generator

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

One run now writes the Markdown file itself.

<!-- end_slide -->

# Exercise 4: Generate And Publish

Check syntax, run, inspect, then build:

```bash
bash -n maker-report.sh
./maker-report.sh "S5 Report"
cat ~/src/pages/maker-report.md
build-website
ls -l ~/public_html/maker-report.html
```

`bash -n` checks syntax without running the script. Success normally prints nothing.

Open `/~your-handle/maker-report.html` on the class site.

Rerun the script for fresh Markdown. Rerun `build-website` for fresh HTML.

<!-- end_slide -->

# You Built A Real Generator

```text
three familiar commands
  -> one saved script
  -> one executable ./ command
  -> one quoted title
  -> one generated Markdown file
  -> one published web page
```

Three sequential extensions are available after the live objectives:

1. Add uptime to the report.
2. Run the script from another directory.
3. Preserve the script in Git.

<!-- end_slide -->

# Next Session: Decisions And Networks

Your script always writes the same report. It types, it does not choose.

In S6, it learns to make decisions and to talk to the network.

Make sure `maker-report.sh` works. S6 keeps building on it.

<!-- end_slide -->

# Optional Appendix: `-u` Finds Missing Values

Keep this experiment in `~/playground/options-demo.sh`:

```bash
#!/bin/bash
set -u

report_title="$1"
printf 'title=<%s>\n' "$report_title"
printf 'before failure\n'
ls /no/such/s5-path
printf 'after failure\n'
```

```bash
chmod u+x ~/playground/options-demo.sh
~/playground/options-demo.sh
~/playground/options-demo.sh "Options Demo"
```

No argument: `$1` is unset, so `-u` stops the script. With a title, the failed `ls` does not stop it.

<!-- end_slide -->

# Optional Appendix: `-e` Stops This Sequence

Add one line immediately after `set -u`:

```bash
set -e
```

Run with the required title:

```bash
~/playground/options-demo.sh "Options Demo"
```

This time `after failure` is not printed.

In this straight-line example, `-e` exits after the standalone `ls` returns nonzero.

It is not a universal "stop on every error" rule. Tests, `&&`, `||`, `!`, and pipelines have exceptions.

These options expose failures; they do not replace explicit validation or error handling.
