# Starship Prompts

Salt installs three Starship prompt profiles for deployed users:

| Profile | Shape |
| --- | --- |
| `default` | Existing full prompt |
| `minimal` | Colored `$` only |
| `classic` | `user@host:current-directory$` |

Switch profiles in the current shell and future shells:

```bash
starship-prompt minimal
starship-prompt classic
starship-prompt default
```

Show the selected profile:

```bash
starship-prompt
```
