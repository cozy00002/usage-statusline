#!/usr/bin/env node
// Claude Code status line: shows the model, context usage, and your plan's usage limits (5-hour session / 7-day week),
// and appends a line to a TSV log only when the usage changes.
// Claude Code passes JSON on stdin: https://code.claude.com/docs/en/statusline
//
// Log columns: local time, session %, week %, first 8 chars of the session ID.
// Environment variables:
//   USAGE_LOG_FILE   path of the log (default: usage-log.tsv next to this script)
//   STATUSLINE_LANG  "ja" for Japanese labels (default: English)
import { readFileSync, appendFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const logFile = process.env.USAGE_LOG_FILE ?? path.join(path.dirname(fileURLToPath(import.meta.url)), 'usage-log.tsv');
const labels = process.env.STATUSLINE_LANG === 'ja' ? { session: 'セッション', week: '週' } : { session: 'session', week: 'week' };

let data = {};
try {
  data = JSON.parse(readFileSync(0, 'utf8'));
} catch {
  // Show whatever we can even if the input is unreadable
}

const pct = (v) => (typeof v === 'number' ? Math.round(v) : null);
const session = pct(data.rate_limits?.five_hour?.used_percentage);
const week = pct(data.rate_limits?.seven_day?.used_percentage);
const ctx = pct(data.context_window?.used_percentage);

const parts = [data.model?.display_name ?? '?'];
if (ctx !== null) parts.push(`ctx ${ctx}%`);
if (session !== null || week !== null) parts.push(`${labels.session} ${session ?? '-'}% / ${labels.week} ${week ?? '-'}%`);
console.log(parts.join(' | '));

// Skip writing when the usage is the same as the last line (the status line runs often)
if (session !== null || week !== null) {
  try {
    let last = '';
    try {
      last = readFileSync(logFile, 'utf8').trimEnd().split('\n').pop() ?? '';
    } catch {
      // No log yet
    }
    const [, lastSession, lastWeek] = last.split('\t');
    if (lastSession !== String(session ?? '') || lastWeek !== String(week ?? '')) {
      const now = new Date();
      const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16).replace('T', ' ');
      const id = String(data.session_id ?? '').slice(0, 8);
      appendFileSync(logFile, `${local}\t${session ?? ''}\t${week ?? ''}\t${id}\n`);
    }
  } catch {
    // Never break the display because the log cannot be written
  }
}
