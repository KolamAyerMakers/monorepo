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
  printf '* Uptime: '
  uptime
  printf '\n## Shell fields in /etc/passwd\n\n'
  printf '%s\n' '```text'
  cut -d: -f7 /etc/passwd | sort -u
  printf '%s\n' '```'
} > ~/src/pages/maker-report.md
