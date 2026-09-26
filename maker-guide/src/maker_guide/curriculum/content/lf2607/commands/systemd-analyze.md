# systemd-analyze

## Use

Check a unit file for mistakes without starting the service.

Create a sample file named for your account:

```bash
micro "/tmp/$USER-example.service"
```

Add this content. `/usr/bin/true` is a command that simply succeeds:

```ini
[Service]
ExecStart=/usr/bin/true
```

Save with `Ctrl-S`, exit with `Ctrl-Q`, then check it as a user unit:

```bash
systemd-analyze --user verify "/tmp/$USER-example.service"
```

`--user` selects the user manager's rules; `verify` checks the named file without installing or starting it. The command reports unknown settings, invalid values, and missing executables. Fix errors and warnings, then check again. A clean result normally prints nothing.

## Watch Out

A valid unit file does not prove the service works: `verify` does not check the program's command-line options. Use [systemctl](systemctl.md) to inspect its state and [journalctl](journalctl.md) to read runtime errors.

## Docs Pointers

- Run `man systemd-analyze` and read the `verify` section.
- Read the [systemd-analyze manual](https://www.freedesktop.org/software/systemd/man/latest/systemd-analyze.html).
