# Complementary Linux knowledge

Fourteen original complementary pages extend the S01–S08 topic checklist; one
additional maintenance page completes the centralized Package Management chapter.
They follow the same editorial rules; no purchased artwork is used.
This directory is a source inventory, not a chapter or reading order.
[`../contents.toml`](../contents.toml) determines prerequisites and placement.

| Source | Purpose |
| :--- | :--- |
| `spaces.svg` | Quoting keeps a filename with spaces in one argument. |
| `wildcards.svg` | The shell expands filename patterns before running a command. |
| `find.svg` | Search for file paths inside a stated directory tree. |
| `copy-directories.svg` | Recursively copy a directory into a new destination. |
| `symlinks.svg` | A symbolic link refers to another path, not a second content copy. |
| `disk-space.svg` | Filesystem capacity and directory usage answer different questions. |
| `grep.svg` | Select matching text lines, with visible input and numbered output. |
| `exit-status.svg` | Success/failure status controls conditional commands. |
| `environment.svg` | Exported values are inherited by child processes. |
| `path.svg` | Command lookup searches directories, unless a path is specified. |
| `git-unstage.svg` | Remove a tracked change from staging without erasing the edit. |
| `git-discard.svg` | Restore a tracked working file from the last commit, with an adjacent loss warning. |
| `backups.svg` | An independent recoverable copy protects against loss of the working disk. |
| `jobs.svg` | Background and foreground jobs belong to an interactive shell. |
| `package-maintenance.svg` | Refreshing information, upgrading installed software and removing packages. |

GNU utilities are common on full Debian/Ubuntu and Fedora installations, not
guaranteed on minimal systems. Bash examples identify their shell requirement;
Git restore examples require Git 2.23 or newer and an existing commit. Examples
do not assume a supplied home directory, backup device, remote account or service.

All generated page exports and review previews stay ignored under `local/`.
Final review status is tracked in [`../REVIEW.md`](../REVIEW.md).
