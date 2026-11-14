# usage-statusline

[日本語](README.ja.md)

A tiny Claude Code status line that shows your plan's usage limits and keeps a log of them.

```
Opus | ctx 12% | session 20% / week 41%
```

- Shows the model, context usage, and the 5-hour session / 7-day week usage that Claude Code passes to status line scripts.
- Appends a line to `usage-log.tsv` only when the usage changes, so you can look back at how much each piece of work used.
- One file, about 50 lines. Node.js, or Python 3 if you do not have Node.js. No dependencies, no network access, no extra API calls.

## Install

Requires Node.js 18 or later.

1. Copy `statusline.mjs` to `~/.claude/statusline.mjs`.
2. Add this to `~/.claude/settings.json` (or a project's `.claude/settings.json`):

```json
{
  "statusLine": {
    "type": "command",
    "command": "node ~/.claude/statusline.mjs"
  }
}
```

The usage numbers appear after the first response in a session.

### Without Node.js (Python)

`statusline.py` does the same thing with Python 3's standard library (tested on 3.11 and 3.13). Copy it to `~/.claude/statusline.py` and use this command instead:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude/statusline.py"
  }
}
```

## The log

`usage-log.tsv` is written next to the script. Columns are separated by tabs:

| Column | Example |
|---|---|
| Local time | `2026-11-13 10:25` |
| Session % (5 hours) | `7` |
| Week % (7 days) | `13` |
| Session ID (first 8 characters) | `a1b2c3d4` |

The usage is account-wide, so if you run several sessions at once, each one's line includes the others' usage. The session ID column tells you which session wrote the line.

## Options

| Environment variable | Meaning |
|---|---|
| `USAGE_LOG_FILE` | Path of the log file |
| `STATUSLINE_LANG` | `ja` for Japanese labels |

## Notes

- It depends on the `rate_limits` field of the JSON that Claude Code passes to status line scripts. If that changes, the usage part disappears, but the rest keeps working.
- If you want pace indicators or projections of when you will hit the limit, other community status lines do that. This one stays small on purpose.

## Test

```bash
node --test          # statusline.mjs
python3 -m unittest  # statusline.py
```

## License

MIT
