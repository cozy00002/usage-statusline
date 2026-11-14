#!/usr/bin/env python3
# Claude Code status line (Python version of statusline.mjs, for machines without Node.js).
# Shows the model, context usage, and your plan's usage limits (5-hour session / 7-day week),
# and appends a line to a TSV log only when the usage changes.
# Claude Code passes JSON on stdin: https://code.claude.com/docs/en/statusline
# Standard library only. Behaves the same as statusline.mjs.
#
# Log columns: local time, session %, week %, first 8 chars of the session ID.
# Environment variables:
#   USAGE_LOG_FILE   path of the log (default: usage-log.tsv next to this script)
#   STATUSLINE_LANG  "ja" for Japanese labels (default: English)
import json
import math
import os
import sys
from datetime import datetime

# Do not fail on non-ASCII labels when called with a C locale
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

log_file = os.environ.get("USAGE_LOG_FILE")
if log_file is None:
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usage-log.tsv")
if os.environ.get("STATUSLINE_LANG") == "ja":
    labels = {"session": "セッション", "week": "週"}
else:
    labels = {"session": "session", "week": "week"}

data = {}
try:
    data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
except Exception:
    pass  # Show whatever we can even if the input is unreadable


def get(obj, *keys):
    """Like data.a?.b?.c in JavaScript: None if any step is not a dict"""
    for k in keys:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(k)
    return obj


def pct(v):
    """Round like JavaScript's Math.round (0.5 rounds up). None if not a number"""
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        return None
    return math.floor(v + 0.5)


def text(v):
    """A string close to JavaScript's String(v)"""
    if v is True:
        return "true"
    if v is False:
        return "false"
    return str(v)


session = pct(get(data, "rate_limits", "five_hour", "used_percentage"))
week = pct(get(data, "rate_limits", "seven_day", "used_percentage"))
ctx = pct(get(data, "context_window", "used_percentage"))

name = get(data, "model", "display_name")
parts = ["?" if name is None else text(name)]
if ctx is not None:
    parts.append(f"ctx {ctx}%")
if session is not None or week is not None:
    s_text = "-" if session is None else session
    w_text = "-" if week is None else week
    parts.append(f"{labels['session']} {s_text}% / {labels['week']} {w_text}%")
print(" | ".join(parts))

# Skip writing when the usage is the same as the last line (the status line runs often)
if session is not None or week is not None:
    try:
        last = ""
        try:
            with open(log_file, encoding="utf-8") as f:
                last = f.read().rstrip().split("\n")[-1]
        except OSError:
            pass  # No log yet
        cols = last.split("\t")
        # rstrip drops empty trailing columns, so treat missing ones as empty
        last_session = cols[1] if len(cols) > 1 else ""
        last_week = cols[2] if len(cols) > 2 else ""
        s = "" if session is None else str(session)
        w = "" if week is None else str(week)
        if last_session != s or last_week != w:
            local = datetime.now().strftime("%Y-%m-%d %H:%M")
            sid = get(data, "session_id")
            sid = "" if sid is None else text(sid)[:8]
            with open(log_file, "a", encoding="utf-8", newline="\n") as f:
                f.write(f"{local}\t{s}\t{w}\t{sid}\n")
    except Exception:
        pass  # Never break the display because the log cannot be written
