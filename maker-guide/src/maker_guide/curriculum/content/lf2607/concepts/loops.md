# Loops

## Core Idea

Loops repeat commands for lists or while a condition stays true.

## Practice Alone

Use `for` for known lists and `while` for condition-driven repetition.

```bash
for name in Ada Grace Linus; do
  printf 'Hello, %s\n' "$name"
done
```

Expect three greetings, one per name. Add a fourth name to the list and predict the new output. The [while card](../commands/while.md) gives a bounded countdown; keep its decrement so it stops.

## Done When

You can replace five repeated command lines with one loop.

## Go Deeper

- [One-liners](oneliner.md) shows compact `for` loops at the prompt.
- Use a script file when the loop becomes hard to read.
