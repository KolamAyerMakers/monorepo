# Linux Foundations S2

Session: S2

Files, editing, identity

<!-- end_slide -->

# Schedule Change

S5, Scripting begins, moves from Saturday, August 15 to Saturday, August 22.

<!-- end_slide -->

# Today

Last session you read the machine.

Today you set up SSH keys early, make files, edit them, break a site safely, and rebuild it.

<!-- end_slide -->

# Your Public Page

Your site source Markdown lives here:

```bash
~/src/pages/
```

Your generated public page lives here:

```bash
~/public_html/
```

Hands-on now: inspect both directories.

```bash
ls -l ~/src/pages/
ls -l ~/public_html/
```

Which directory has Markdown you edit? Which has HTML visitors receive?

<!-- end_slide -->

# SSH Keys: What and Why

An SSH key pair lets your computer prove it is you without asking you to enter your account password for every login.

- Private key: stays secret on your computer. Never send it anywhere.
- Public key: can be installed on a server.

When you connect, the server sends a one-time challenge. Your private key signs it. The server verifies that signature with your public key, then lets you in.

We use keys for safer SSH login without your account password. Choose a strong, memorable passphrase: it protects the private key on your computer and is not sent to the server. If the private key is lost or copied, replace it and remove its public key from the server.

<!-- end_slide -->

# Create, Install, and Use a Key

Hands-on now: do this from your own computer. A prompt ending in `@lf2607` means you are on the server, so run `exit` first.

This course assumes you do not have an SSH key yet.

1. Run `ssh-keygen`, accept the default location, and choose a passphrase.
2. Install the public key using the personal SSH address from your registration command, never `new@...`.

`ssh-keygen` creates `~/.ssh/id_ed25519`, your private key that stays on your computer, and `~/.ssh/id_ed25519.pub`, the public key you install on the server.

On macOS or Linux, run:

```bash
ssh-copy-id <handle>@lf2607.kolamayermakers.org
```

Replace `<handle>` with your username. Reconnect with the same command without entering your account password, then run `whoami`. The guide records a successful public-key login automatically.

<!-- end_slide -->

# Install a Key from Windows

In Windows Terminal or PowerShell, run `Get-Content ~/.ssh/id_ed25519.pub`, copy the one public-key line, then sign in with your personal command and password. On the server, run:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
cat >> ~/.ssh/authorized_keys
```

Paste the public-key line, press Enter and Ctrl-D, then run `chmod 600 ~/.ssh/authorized_keys`. This appends your key without replacing others. Exit, reconnect with the same command without entering your account password, then run `whoami`. If you cannot log in, use browser SSH recovery or ask the instructor.

<!-- end_slide -->

# Create a Playground

Hands-on now: create files where mistakes are cheap.

```bash
mkdir -p ~/playground         # Create a directory
touch ~/playground/one.txt    # Create an empty file
touch ~/playground/two.txt
touch ~/playground/three.txt
ls -l ~/playground
```

The playground is where mistakes are cheap.

<!-- end_slide -->

# Edit A File

Hands-on now: save the file, then prove it exists.

```bash
micro ~/playground/micro-note.txt  # Edit a file
cat ~/playground/micro-note.txt    # See the file contents
```

In Micro, type the exact note `edited with micro`. `Ctrl-S` saves. `Ctrl-Q` quits. Save the file, then prove it exists.

<!-- end_slide -->

# Edit Your Page

Hands-on now: edit source, build it, then inspect generated output.

```bash
micro ~/src/pages/index.md
build-website
cat ~/public_html/index.html
```

Replace this starter heading in `~/src/pages/index.md` with any text:

```text
A Linux site under construction
```

Save with `Ctrl-S`, quit with `Ctrl-Q`. Do not edit `~/public_html/index.html`.

Before you exit, make this real source edit and build it successfully.

<!-- end_slide -->

# Redirection

Hands-on now: read the file after each command and compare replacement versus append.

```bash
cd ~/playground
echo "hello makers" > hi.txt               # Overwrite
cat hi.txt                                 # Read one line
echo again >> hi.txt                       # Append
cat hi.txt                                 # Read two lines
echo "first version" > overwrite-demo.txt  # Write a file
cat overwrite-demo.txt                     # Read first version
echo replacement > overwrite-demo.txt      # Overwrite it
cat overwrite-demo.txt                     # Read replacement
```

`>` replaces.

`>>` appends.

This distinction matters.

<!-- end_slide -->

# Copy And Inspect

Hands-on now: copy, inspect, and read the owner column.

```bash
cat /etc/hostname                       # Read the original
cp /etc/hostname ~/playground/hostname  # Copy it
cat ~/playground/hostname               # Read the copy
ls -l ~/playground/hostname             # Inspect its owner
```

A copy you create in your home directory is your file.

Read the owner column.

<!-- end_slide -->

# Move and Remove Files

Hands-on now: copy, rename, move, and remove playground files safely.

```bash
cd ~/playground                  # Work here
cp one.txt one-copy.txt          # Copy a file
mv one-copy.txt one-renamed.txt  # Rename it
mkdir moved                      # Create a directory
mv one-renamed.txt moved/        # Move the file
mkdir empty-directory            # Create an empty directory
rmdir empty-directory            # Remove the empty directory
rm -i moved/one-renamed.txt      # Confirm, then remove file
rmdir moved                      # Remove the empty directory
ls -l                            # Inspect what remains
```

`mv` moves or renames. `rm -i` asks before removing a file. `rmdir` removes empty directories and refuses non-empty ones. `rm -rf` recursively forces removal, so do not run it in S2. There is no trash where you can recover files. Make mistakes in the playground, not in source.

<!-- end_slide -->

# Delete and Rebuild

Hands-on now: confirm a successful build, delete generated output only, then rebuild it.

```bash
build-website                    # Generate the public page
ls ~/public_html/index.html      # Confirm it exists
rm -i ~/public_html/index.html   # Confirm, then delete output
build-website                    # Generate it again
ls ~/public_html/index.html      # Confirm it returned
```

The generated page can be deleted because it is rebuildable.

Do not destroy source casually.

<!-- end_slide -->

# S2 Recap

Today you created, edited, copied, moved, and removed files in the playground.

You know the difference between source in `~/src/pages/index.md` and generated output in `~/public_html/`.

You started safe SSH-key login with a passphrase.

Run `guide now` for your current session objective. After you complete it, `guide now` shows your current quest. Submit prompted answers with `guide answer 'your answer'`. Run `guide check` after practical work. A passing check records your progress.

If possible, complete all S2 quests for reinforcement or catch-up. S3 starts from today's live learning, not quest completion.
