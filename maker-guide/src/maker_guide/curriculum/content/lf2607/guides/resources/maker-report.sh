#!/bin/bash

set -euo pipefail

if [[ "$#" -ne 1 ]]; then
  printf 'Usage: maker-report.sh TITLE\n' >&2
  exit 2
fi

report_title="$1"
temporary_report=$(mktemp "$HOME/src/pages/.maker-report.XXXXXX")
trap 'rm -f -- "$temporary_report"' EXIT

# Keep the previous report until collection and writing both succeed.
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
} > "$temporary_report"

chmod 644 "$temporary_report"
mv -T -- "$temporary_report" "$HOME/src/pages/maker-report.md"
