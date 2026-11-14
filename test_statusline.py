# Tests for statusline.py (the same cases as statusline.test.mjs, plus Python-specific ones).
# The log goes to a temp folder via USAGE_LOG_FILE.
# Run: python -m unittest -v
import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "statusline.py")


def run(inp, log_file, extra_env=None):
    if not isinstance(inp, str):
        inp = json.dumps(inp, ensure_ascii=False)
    env = dict(os.environ, USAGE_LOG_FILE=log_file)
    env.pop("STATUSLINE_LANG", None)
    env.update(extra_env or {})
    r = subprocess.run([sys.executable, SCRIPT], input=inp.encode("utf-8"), capture_output=True, env=env)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    return r.stdout.decode("utf-8").strip()


def read_lines(f):
    with open(f, encoding="utf-8") as fh:
        return fh.read().rstrip().split("\n")


def full(session, week):
    return {
        "model": {"display_name": "Opus"},
        "context_window": {"used_percentage": 12.4},
        "rate_limits": {"five_hour": {"used_percentage": session}, "seven_day": {"used_percentage": week}},
        "session_id": "0123456789abcdef",
    }


class StatuslineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="statusline-test-")
        self.log = os.path.join(self.tmp.name, "usage-log.tsv")

    def tearDown(self):
        self.tmp.cleanup()

    def test_shows_usage_and_writes_one_log_line(self):
        self.assertEqual(run(full(19.6, 41), self.log), "Opus | ctx 12% | session 20% / week 41%")
        lines = read_lines(self.log)
        self.assertEqual(len(lines), 1)
        self.assertRegex(lines[0], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}\t20\t41\t01234567$")

    def test_japanese_labels(self):
        out = run(full(20, 41), self.log, {"STATUSLINE_LANG": "ja"})
        self.assertEqual(out, "Opus | ctx 12% | セッション 20% / 週 41%")

    def test_writes_only_when_usage_changes(self):
        for s, w in [(20, 41), (20, 41), (21, 41), (21, 42)]:
            run(full(s, w), self.log)
        self.assertEqual(["/".join(l.split("\t")[1:3]) for l in read_lines(self.log)], ["20/41", "21/41", "21/42"])

    def test_broken_input(self):
        self.assertEqual(run("{broken JSON", self.log), "?")
        self.assertFalse(os.path.exists(self.log))

    def test_no_usage_yet(self):
        inp = {"model": {"display_name": "Opus"}, "context_window": {"used_percentage": 3}}
        self.assertEqual(run(inp, self.log), "Opus | ctx 3%")
        self.assertFalse(os.path.exists(self.log))

    def test_only_one_limit_present(self):
        inp = {"model": {"display_name": "Opus"}, "rate_limits": {"seven_day": {"used_percentage": 41}}}
        self.assertEqual(run(inp, self.log), "Opus | session -% / week 41%")
        self.assertRegex(read_lines(self.log)[0], r"^\S+ \S+\t\t41$")
        run(inp, self.log)
        self.assertEqual(len(read_lines(self.log)), 1, "empty columns count as the same")

    def test_session_only_without_session_id(self):
        inp = {"model": {"display_name": "Opus"}, "rate_limits": {"five_hour": {"used_percentage": 20}}}
        run(inp, self.log)
        run(inp, self.log)
        self.assertEqual(len(read_lines(self.log)), 1)

    def test_null_input(self):
        self.assertEqual(run("null", self.log), "?")
        self.assertFalse(os.path.exists(self.log))

    def test_log_cannot_be_written(self):
        log = os.path.join(self.tmp.name, "missing", "folder", "usage-log.tsv")
        self.assertEqual(run(full(20, 41), log), "Opus | ctx 12% | session 20% / week 41%")

    # Python-specific: match JavaScript's behavior

    def test_half_rounds_up(self):
        self.assertEqual(run(full(2.5, 0.5), self.log), "Opus | ctx 12% | session 3% / week 1%")

    def test_booleans_are_not_numbers(self):
        inp = {"model": {"display_name": "Opus"}, "context_window": {"used_percentage": True}}
        self.assertEqual(run(inp, self.log), "Opus")

    def test_non_dict_values_do_not_fail(self):
        self.assertEqual(run([1, 2, 3], self.log), "?")
        self.assertEqual(run({"model": "Opus", "rate_limits": [1]}, self.log), "?")
        self.assertFalse(os.path.exists(self.log))

    def test_c_locale_with_japanese_labels(self):
        extra = {"STATUSLINE_LANG": "ja", "LANG": "C", "LC_ALL": "C", "PYTHONIOENCODING": "ascii"}
        self.assertEqual(run(full(20, 41), self.log, extra), "Opus | ctx 12% | セッション 20% / 週 41%")


if __name__ == "__main__":
    unittest.main()
