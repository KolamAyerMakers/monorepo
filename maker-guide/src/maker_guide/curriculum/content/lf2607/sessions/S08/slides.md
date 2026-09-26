# Keep Your Server Running

Session: S8

2026-09-26

Your website ran only while your terminal stayed open.

How to keep it running when you leave?

<!-- end_slide -->

# SSH Was Already Running

The SSH server starts when the machine boots, ready before you connect.

Let's follow what happens during startup.

<!-- end_slide -->

# What Starts When Linux Boots?

The **kernel** is the core of Linux. It manages hardware, memory, and processes.

During startup, it starts the first process outside the kernel: **PID 1**, process number 1.

This process has the **init** role, short for initialization: bringing up the rest of the system.

<!-- end_slide -->

# Meet systemd

**systemd** fills this role on many Linux distributions, including ours. Other init systems exist.

It starts and supervises **services**, programs managed independently of your terminal. It coordinates startup and shutdown, and can restart failed programs when configured to do so.

In your SSH session, inspect it with `ps`. `-p 1` selects process 1:

```bash
ps -p 1
```

<!-- end_slide -->

# Your Services, Your Account

The **system manager** (PID 1) manages machine-wide services such as SSH.

Your **user manager** is a separate systemd process for your account.

We will use it for Caddy, without changing anyone else's services.

<!-- end_slide -->

# Give It Instructions

A **unit file** tells systemd what to run and what to do if it fails.

A service unit's filename ends in `.service`. Ours will be `site.service`.

`ExecStart` specifies the command. Reuse the one from S7, with two changes:

- `12345` must become your actual port number. This is not Bash: do not use `$PORT` or shell calculations here.
- `%h` means your home directory in a unit file.

`/usr/bin/caddy` is the full path to the Caddy program.

```ini
ExecStart=/usr/bin/caddy file-server --listen :12345 --root %h/public_html --access-log
```

<!-- end_slide -->

# What Else Does systemd Need?

`WorkingDirectory` sets the folder the program starts in. Use `%h`, your home directory.

`Restart=on-failure` retries after a crash, but not after a deliberate stop.

`Description` is a label for people.

A **target** groups units. `default.target` is your user manager's normal startup group.

`WantedBy=default.target` lets us add this service to that group when we enable it. Writing this line alone does not start the service.

<!-- end_slide -->

# Create Your Service File

User unit files live in `~/.config/systemd/user/`.

Print your assigned port, then create the service unit file:

```bash
echo "$((10000 + $(id -u)))"
mkdir -p ~/.config/systemd/user
micro ~/.config/systemd/user/site.service
```

<!-- end_slide -->

# Put The Instructions Together

The section headings group the label, the running instructions, and the automatic-start setting.

Replace `12345` with your printed port.

```ini
[Unit]
Description=Personal website service

[Service]
WorkingDirectory=%h
ExecStart=/usr/bin/caddy file-server --listen :12345 --root %h/public_html --access-log
Restart=on-failure

[Install]
WantedBy=default.target
```

<!-- end_slide -->

# Check Before You Start

`systemd-analyze verify` checks unit configuration syntax without starting the service:

```bash
systemd-analyze --user verify ~/.config/systemd/user/site.service
```

Look for unknown settings, invalid values, or missing program paths. Read warnings too.

Fix the reported mistakes, save, and run the check again before continuing.

Valid configuration does not prove the service will run or the website will work.

<!-- end_slide -->

# Ask systemd To Start It

**systemctl** sends instructions to systemd. `--user` selects your user manager.

- `daemon-reload` reads the unit file you saved.
- `start` runs the service now.
- `enable` arranges startup whenever your user manager starts.
- `status` shows its state. Press `q` to return to the shell.

```bash
systemctl --user daemon-reload
systemctl --user start site.service
systemctl --user enable site.service
systemctl --user status site.service
```

Look for `Active: active (running)`.

If it failed, try to diagnose and fix it using the [self-study guide](self-study.md#troubleshooting).

If you're still stuck, ask for help and explain what you tried.

<!-- end_slide -->

# Hands-On: Run Your Site

<!-- column_layout: [9, 11] -->

<!-- column: 0 -->

**1. Create the unit file**

```bash
echo "$((10000 + $(id -u)))"
mkdir -p ~/.config/systemd/user
micro ~/.config/systemd/user/site.service
```

Replace `12345` with the printed port:

```ini
[Unit]
Description=Personal website service

[Service]
WorkingDirectory=%h
ExecStart=/usr/bin/caddy file-server --listen :12345 --root %h/public_html --access-log
Restart=on-failure

[Install]
WantedBy=default.target
```

<!-- column: 1 -->

**2. Verify, then start**

```bash
systemd-analyze --user verify \
  ~/.config/systemd/user/site.service
systemctl --user daemon-reload
systemctl --user start site.service
systemctl --user enable site.service
systemctl --user status site.service
```

Look for `Active: active (running)`.

**3. Request the page**

```bash
curl -i "http://127.0.0.1:$((10000 + $(id -u)))/"
curl -I "https://$USER.lf2607.kolamayermakers.org/"
```

Check for successful HTTP statuses and your page's HTML in the local response.

Open your [service homepage](https://your-handle.lf2607.kolamayermakers.org/) on your laptop, replacing `your-handle`.

<!-- reset_layout -->

<!-- alignment: center -->

**Can You Close SSH Now?**

<!-- end_slide -->

# Hands-On: Does It Run Without You?

Your site should work while you are logged out. Checking only after reconnecting could hide a restart.

**1. Before leaving, note what is running.**

`status` already shows `Main PID` (the process ID) and the date and time after `since` on the `Active:` line. Keep both on your laptop:

```bash
systemctl --user status site.service
```

**2. Close all your SSH connections, then visit your site.**

Refresh the page in your browser before reconnecting to SSH. Does it still load?

**3. Reconnect and run the same command again.**

Compare the PID and activation time, not just `active`. If they changed, Caddy restarted. A page that worked while you were away, with both values unchanged, is evidence it kept running during the test.

<!-- end_slide -->

# You Still Control Your Server

`stop` ends the service. `restart` stops and starts it again.

Run these one at a time, checking the service homepage after each:

```bash
systemctl --user stop site.service
systemctl --user start site.service
```

`Restart=on-failure` restarts a crashed service, not one you deliberately stopped.

<!-- end_slide -->

# Read Your Server's Logs

systemd stores Caddy's messages in the **journal**. **journalctl** reads it; `--since` selects how far back to look:

```bash
journalctl --user -u site.service --since "5 minutes ago"
```

Press `q` to leave. Add `-f` to watch new messages arrive:

```bash
journalctl --user -u site.service -f
```

Visit your homepage, then `/missing.html`. Find both requests and their status codes.

`Ctrl-C` stops watching, not the server.

<!-- end_slide -->

# Hands-On: Watch And Update Your Site

<!-- column_layout: [3, 2] -->

<!-- column: 0 -->

**1. Control your service**

Run these one at a time; check the [service homepage](https://your-handle.lf2607.kolamayermakers.org/) after each, replacing `your-handle`:

```bash
systemctl --user stop site.service
systemctl --user start site.service
```

`Restart=on-failure` restarts a crashed service, not one you deliberately stopped.

**2. Read and follow its journal**

Press `q` after reading, then run the second command:

```bash
journalctl --user -u site.service --since "5 minutes ago"
journalctl --user -u site.service -f
```

<!-- column: 1 -->

**3. Match requests to log entries**

Visit your service homepage, then `/missing.html` on the same site.

Find each request's time, `request.method`, `request.uri`, and `status`.

Press `Ctrl-C` to stop following. Reload the page: Caddy should still respond.

**4. Publish a visible change**

Edit an existing page under `~/src/pages`, then:

```bash
build-website
```

Caddy reads the files from disk for each request. Updated files are served without restarting it.

<!-- reset_layout -->

<!-- end_slide -->

# Read, Then Repair

**Inspect before editing**

```bash
systemctl --user cat site.service
```

Compare the unit with the status, logs, and local page response.

**Unit problem**

After editing: **verify**, **daemon-reload**, then **restart**.

Retry limit reached? Fix the cause, then clear the limit:

```bash
systemctl --user reset-failed site.service
```

<!-- end_slide -->

# Hands-On: Solve Five Issues

`guide` breaks things for you so you can have fun troubleshooting and fixing them. Run `guide now` to start each issue.

<!-- column_layout: [3, 2] -->

<!-- column: 0 -->

**1. Investigate before editing**

```bash
systemctl --user cat site.service
systemctl --user status site.service
journalctl --user -u site.service --since "5 minutes ago"
curl -i "http://127.0.0.1:$((10000 + $(id -u)))/"
```

Press `q` to leave each paged view.

What failed: starting the program, connecting, or serving the right page?

**2. Repair what the evidence explains**

For unit changes, edit:

```bash
micro ~/.config/systemd/user/site.service
```

For page problems, inspect the source and published files. Keep your source intact.

<!-- column: 1 -->

**3. Apply a unit repair**

```bash
systemd-analyze --user verify \
  ~/.config/systemd/user/site.service
```

Fix reported mistakes. If retries hit the limit, run `systemctl --user reset-failed site.service` first. Then:

```bash
systemctl --user daemon-reload
systemctl --user restart site.service
```

**4. Check and explain**

Repeat the status and local page checks. Is your page back?

Run `guide answer 'Your cause and repair explanation'`.

After completion, run `guide now` for the next issue.

<!-- reset_layout -->

<!-- alignment: center -->

`guide` is still here to help you investigate. Ask it for a hint when stuck.

<!-- end_slide -->

# Keep The Site. Keep The Lesson.

Finish with your page working. Keep the reviewed unit at `~/src/services/site.service`, outside published pages: [Preserve the working unit](self-study.md#4-preserve-the-working-unit).

Keep short notes on the causes, repairs, and logout result. No credentials or private logs.

You can now run, inspect, and repair your service without leaving a terminal open.

Next: schedule Linux to refresh your report and publish it. S9: **2026-10-10**.
