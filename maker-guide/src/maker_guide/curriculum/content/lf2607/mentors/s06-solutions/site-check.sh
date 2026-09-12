#!/bin/bash
set -euo pipefail

if [[ "$#" -eq 0 ]]; then
  printf 'Usage: site-check.sh PAGE [PAGE ...] (use "" for homepage)\n' >&2
  exit 2
fi

base_url="https://lf2607.kolamayermakers.org/~$USER"

for page in "$@"; do
  url="$base_url/$page"
  curl_exit_code=0
  status=$(curl -sS -I --max-time 10 -o /dev/null -w '%{http_code}' "$url") \
    || curl_exit_code=$?
  if [[ "$curl_exit_code" -eq 0 ]]; then
    if [[ "$status" == "200" ]]; then
      printf 'OK: %s returned HTTP 200\n' "$url"
    elif [[ "$page" == "maker-report.html" && "$status" == "404" ]]; then
      printf 'MISSING: maker-report.html returned HTTP 404\n'
      printf 'Run ~/scripts/maker-report.sh "S5 Report", then build-website.\n'
    else
      printf 'CHECK: %s returned HTTP %s\n' "$url" "$status"
      printf 'Inspect headers with: curl -I %s\n' "$url"
    fi
  else
    printf 'CONNECTION FAILED: %s\n' "$url"
    printf 'Read the curl error: check name, connection, or certificate.\n'
  fi
done
