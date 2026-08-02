# Linux Foundations S6

Session: S6

Control flow and networking primer

<!-- end_slide -->

# Today's Story

Scripts become useful when they make decisions and talk to the outside world.

Teacher demos the pattern, then learners write one branch, one loop, and one network check.

<!-- end_slide -->

# Hands-On Spine

Hands-on now: type each block, then explain what changed.

```bash
if [[ -f file ]]; then
  printf 'exists\n'
fi

for item in one two three; do
  printf '%s\n' "$item"
done

curl -H 'Accept: text/plain' https://example.org
host kolamayermakers.org
ping -c 3 1.1.1.1
curl -I https://example.org
```

<!-- end_slide -->

# Exit Goal

Learners write simple control flow, run one DNS or ping check, inspect HTTP headers, and fetch external text.
<!-- end_slide -->

# Between-Session Practice Route

Highly recommended after class or for catch-up:

Use the guide throughout class and between sessions: run `guide now` for your current session objective; after you complete it, it shows your current quest. Submit prompted answers with `guide answer 'your answer'`, and run `guide check` after practical work. A passing check records your progress.

1. Write a `for` loop that counts to ten.
2. Branch on file existence with `if` and `[[ ]]`.
3. Write a `while` countdown.
4. Measure network latency with `ping`.
5. Inspect HTTP headers with `curl -I`.
6. Combine ping, `$1`, and branching in `alive.sh`.
7. Fetch HTTP output into Markdown and rebuild.

<!-- end_slide -->

# Debugging Question

When a script surprises you, ask which test succeeded and which branch ran.
