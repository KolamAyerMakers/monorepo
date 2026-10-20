# S5 — Make the Shell Work for You

Turn familiar commands into a script that generates a Markdown report.

**You need:** Bash, Micro, and the site source at `~/src/pages`. Run these exercises in your classroom shell or Ubuntu terminal. [Home setup](../../guides/continue-at-home.md) provides the local site.

Keep an existing `maker-report.sh` if you already wrote one. Read it first and continue from the stage you need; do not erase a working version to repeat the lesson.

## 1. Save commands in a file

```bash
mkdir -p ~/scripts
cd ~/scripts
micro maker-report.sh
```

Save this text in the editor:

```bash
#!/bin/bash

# Report the account, machine, and time.
whoami
hostname
date
```

Then run:

```bash
bash maker-report.sh
bash -x maker-report.sh
```

Bash reads the file from top to bottom. `-x` prints each command before running it, prefixed with `+`. The trace goes to stderr; normal results go to stdout. Avoid tracing scripts containing secrets.

Ordinary `#` lines are comments. The first line, `#!/bin/bash`, is a **shebang**: it tells Linux which interpreter to use for direct execution.

## 2. Run the file directly

For a newly created file, try:

```bash
./maker-report.sh
```

Expect `Permission denied` if it has no execute permission. An existing executable script will already run.

```bash
ls -l maker-report.sh
chmod u+x maker-report.sh
ls -l maker-report.sh
./maker-report.sh
```

The owner's triplet gains `x`. `./` means “the file in this directory”; it does not grant permission.

- `bash maker-report.sh` explicitly starts Bash; the file needs read permission, not execute permission.
- `./maker-report.sh` executes the path; this script needs execute permission and its Bash shebang.

## 3. Accept a title

Add these lines after the shebang:

```bash
report_title="$1"
printf 'title=<%s>\n' "$report_title"
```

`$1` is the first argument. Assignment has **no spaces around `=`**. `printf` replaces `%s` with the supplied string; `\n` ends the line.

Predict, then compare:

```bash
./maker-report.sh My Maker Report
./maker-report.sh "My Maker Report"
```

The first call passes three arguments; `$1` is only `My`. The quoted call passes one title containing spaces.

Quotes matter inside the script too. Compare these lines one at a time, then keep the quoted version:

```bash
printf '# %s\n' $report_title
printf '# %s\n' "$report_title"
```

The unquoted expansion splits words and can expand filename patterns. Here, `printf` reuses its format for extra values, producing several headings.

## 4. Generate the report

Markdown uses `#` for a heading, `*` for a list item, and triple backticks for a code block.

First inspect the data you will include:

```bash
cut -d: -f7 /etc/passwd | sort -u
```

This selects the shell field from local account records and removes duplicates. It does not list every learner in the classroom's identity service.

Adapt your script to the complete example below. The braces group stdout from several commands; one `>` writes it all to the report file. Single quotes make the backticks literal text rather than command substitution.

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

Check syntax, generate, and inspect:

```bash
bash -n ~/scripts/maker-report.sh
~/scripts/maker-report.sh "My Maker Report"
cat ~/src/pages/maker-report.md
```

`bash -n` checks syntax **without running commands**. No output usually means valid syntax, not a correct report. Check for one title, three labelled facts, and a closed code block.

Rerunning replaces `maker-report.md`. Keep handwritten notes in another file. This teaching version can leave partial output if a command fails; the [worked answer](../../guides/self-study-answers.md#s5-shell-scripts) explains the safer supplied version.

## 5. Publish and preserve

**In class:** run `build-website`, then open `https://lf2607.kolamayermakers.org/~username/maker-report.html` using your username.

**At home:** run `cd ~/src && node scripts/build.mjs`, then open `http://localhost:8080/maker-report.html` with the local preview running.

Check the title and facts in the rendered page. Regeneration changes Markdown; building changes HTML. Neither step automatically adds a homepage link.

To keep your script in Git, inspect any existing `~/src/scripts/maker-report.sh` before copying:

```bash
mkdir -p ~/src/scripts
cp -i ~/scripts/maker-report.sh ~/src/scripts/
git -C ~/src status
```

Use S4's inspect → stage → commit workflow for this exact path. The copy in `~/scripts` remains your working script.

## Check yourself

1. Why can Bash run a file that `./` cannot yet execute?
2. Where must the shebang appear?
3. Why are quotes needed both when calling the script and using its title?
4. Which stream goes to the Markdown file? Where do errors go?
5. Why must you rebuild after generating a new report?

[Answers](../../guides/self-study-answers.md#s5-shell-scripts). References: [Shebang](../../concepts/shebang.md), [Script Arguments](../../concepts/script-arguments.md), and [Variables](../../concepts/variables.md).

## If you get stuck

| Symptom | Check |
|---|---|
| `report_title: command not found` | Remove spaces around `=`. |
| `bad interpreter` | Make the first line exactly `#!/bin/bash`; check for Windows line endings if copied from elsewhere. |
| `maker-report.sh: command not found` | Use `./maker-report.sh` in its directory, or its full path elsewhere. |
| Missing or partial report | Confirm `~/src/pages` exists; use `bash -x` and read the failing command. |
| Old browser page | Inspect the Markdown, resolve build errors, then reload. |
