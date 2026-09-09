# Conditionals

## Core Idea

Conditionals make scripts choose based on a command result or test result.

## Command Result

```bash
if curl -I --max-time 10 https://example.org; then
  printf 'A response arrived; inspect its HTTP status.\n'
else
  printf 'The request failed; inspect the curl error.\n'
fi
```

The branch depends on the exit code: `0` succeeds, nonzero fails.

This curl command can exit `0` even for `404`: it received a response. Transport success is not the same as a successful HTTP status.

## Test Result

```bash
path=/etc/hostname
if [[ -e "$path" ]]; then
  printf 'exists\n'
fi
```

Use `[[ ]]` for Bash tests on files, strings, and numbers.

## Capture Both Results

```bash
curl_exit_code=0
status=$(curl -sS -I --max-time 10 -o /dev/null -w '%{http_code}' https://example.org) \
  || curl_exit_code=$?
if [[ "$curl_exit_code" -eq 0 ]]; then
  if [[ "$status" == "200" ]]; then
    printf 'Request returned HTTP 200.\n'
  else
    printf 'Response returned HTTP %s instead.\n' "$status"
  fi
else
  printf 'Request failed; read the curl diagnostic.\n'
fi
```

`status` stores curl's printed HTTP code. `curl_exit_code` starts at `0`; `||` records `$?` only if the capture fails, without letting `set -e` stop the script. `-eq` compares numbers. The outer decision handles command failure; the inner decision interprets an actual response.

## Done When

You can predict which branch runs before executing the script.

## Docs Pointers

- Read [if](../commands/if.md), [`[[ ]]`](../commands/double-brackets.md), [control flow](control-flow.md), [quoting](quoting.md), and [one-liners](oneliner.md).
