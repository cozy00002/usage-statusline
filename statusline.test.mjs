// Tests for statusline.mjs. The log goes to a temp folder via USAGE_LOG_FILE.
// Run: node --test
import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const script = path.join(path.dirname(fileURLToPath(import.meta.url)), 'statusline.mjs');

const dirs = [];
after(() => Promise.all(dirs.map((d) => rm(d, { recursive: true, force: true }))));

async function newLog() {
  const dir = await mkdtemp(path.join(tmpdir(), 'statusline-test-'));
  dirs.push(dir);
  return path.join(dir, 'usage-log.tsv');
}

function run(input, logFile, extraEnv = {}) {
  const env = { ...process.env, USAGE_LOG_FILE: logFile, ...extraEnv };
  if (!('STATUSLINE_LANG' in extraEnv)) delete env.STATUSLINE_LANG;
  const r = spawnSync(process.execPath, [script], {
    input: typeof input === 'string' ? input : JSON.stringify(input),
    env,
    encoding: 'utf8',
  });
  assert.equal(r.status, 0, r.stderr);
  return r.stdout.trim();
}

const readLines = async (f) => (await readFile(f, 'utf8')).trimEnd().split('\n');

const full = (session, week) => ({
  model: { display_name: 'Opus' },
  context_window: { used_percentage: 12.4 },
  rate_limits: { five_hour: { used_percentage: session }, seven_day: { used_percentage: week } },
  session_id: '0123456789abcdef',
});

test('shows model, context and usage (rounded) and writes one log line', async () => {
  const log = await newLog();
  assert.equal(run(full(19.6, 41), log), 'Opus | ctx 12% | session 20% / week 41%');
  const lines = await readLines(log);
  assert.equal(lines.length, 1);
  assert.match(lines[0], /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}\t20\t41\t01234567$/);
});

test('STATUSLINE_LANG=ja uses Japanese labels', async () => {
  const log = await newLog();
  assert.equal(run(full(20, 41), log, { STATUSLINE_LANG: 'ja' }), 'Opus | ctx 12% | セッション 20% / 週 41%');
});

test('writes only when the usage changes', async () => {
  const log = await newLog();
  run(full(20, 41), log);
  run(full(20, 41), log);
  run(full(21, 41), log);
  run(full(21, 42), log);
  const lines = await readLines(log);
  assert.deepEqual(lines.map((l) => l.split('\t').slice(1, 3).join('/')), ['20/41', '21/41', '21/42']);
});

test('broken input: does not fail, prints ?, writes no log', async () => {
  const log = await newLog();
  assert.equal(run('{broken JSON', log), '?');
  assert.ok(!existsSync(log));
});

test('no usage yet (before the first response): no usage shown, no log', async () => {
  const log = await newLog();
  assert.equal(run({ model: { display_name: 'Opus' }, context_window: { used_percentage: 3 } }, log), 'Opus | ctx 3%');
  assert.ok(!existsSync(log));
});

test('only one limit present: the other shows -, the log column is empty', async () => {
  const log = await newLog();
  const input = { model: { display_name: 'Opus' }, rate_limits: { seven_day: { used_percentage: 41 } } };
  assert.equal(run(input, log), 'Opus | session -% / week 41%');
  assert.match((await readLines(log))[0], /^\S+ \S+\t\t41$/);
  run(input, log);
  assert.equal((await readLines(log)).length, 1, 'empty columns count as the same');
});

test('session only, no session ID: the same value is not written twice', async () => {
  const log = await newLog();
  const input = { model: { display_name: 'Opus' }, rate_limits: { five_hour: { used_percentage: 20 } } };
  run(input, log);
  run(input, log);
  assert.equal((await readLines(log)).length, 1);
});

test('null input: does not fail, prints ?, writes no log', async () => {
  const log = await newLog();
  assert.equal(run('null', log), '?');
  assert.ok(!existsSync(log));
});

test('still shows the line when the log cannot be written', async () => {
  const log = path.join(await newLog(), 'missing', 'folder', 'usage-log.tsv');
  assert.equal(run(full(20, 41), log), 'Opus | ctx 12% | session 20% / week 41%');
});
