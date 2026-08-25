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
  printf '```text\n'
  cut -d: -f7 /etc/passwd | sort -u
  printf '```\n'
} > ~/src/pages/maker-report.md
