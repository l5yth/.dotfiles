# SPDX-FileCopyrightText: 2026 Afri Blank (@l5yth)
# SPDX-License-Identifier: Unlicense
#
# This is free and unencumbered software released into the public domain.
# For more information, please refer to <https://unlicense.org>
"""Unit tests for ``guard-bash.py``.

Run from this directory: ``python3 -m unittest test_guard_bash``.
"""

import importlib.util
import io
import json
import os
import runpy
import unittest
from contextlib import redirect_stdout
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "guard-bash.py")
_spec = importlib.util.spec_from_file_location("guard_bash", SCRIPT)
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)

SPEC = guard.SPEC
PROJECT = "/tmp/guard-bash-test/project"


def decide(command, cwd, tool="Bash", run=None):
    """Feed one tool call to the guard and return its decision.

    Args:
        command: The Bash command text.
        cwd: The working directory of the call, or None to omit the field.
        tool: The tool name in the event.
        run: Callable that executes the guard; defaults to ``guard.main``.

    Returns:
        ``"deny"`` when the guard printed a deny decision, else ``"pass"``.
    """
    event = {"tool_name": tool, "tool_input": {"command": command}}
    if cwd is not None:
        event["cwd"] = cwd
    out = io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(json.dumps(event))), redirect_stdout(out):
        try:
            (run or guard.main)()
        except SystemExit:
            pass
    text = out.getvalue().strip()
    if not text:
        return "pass"
    return json.loads(text)["hookSpecificOutput"]["permissionDecision"]


class GuardTest(unittest.TestCase):
    """Decisions for commands in and outside the spec repository."""

    CASES = [
        (PROJECT, "git commit -m x", "deny"),
        (PROJECT, "git -C ~/.src/l5yth/spec commit -m x", "pass"),
        (PROJECT, f"git -C {SPEC} push origin main", "pass"),
        (SPEC, "git -C sub commit -m x", "pass"),
        (SPEC, "git commit -m spec && git push origin main", "pass"),
        (PROJECT, "git -C . push", "deny"),
        (PROJECT, 'bash -c "git push"', "deny"),
        (SPEC, "sh -c 'git push --force'", "deny"),
        (SPEC, "git push --force-with-lease", "deny"),
        (SPEC, "git push origin +main", "deny"),
        (SPEC, "git tag v1", "deny"),
        (PROJECT, 'cd ~/.src/l5yth/spec && git commit -m "x"', "pass"),
        (SPEC, f"cd {PROJECT} && git commit", "deny"),
        (PROJECT, "/usr/bin/git push", "deny"),
        (PROJECT, "git -c user.name=x commit", "deny"),
        (PROJECT, "git --git-dir=/x/.git commit", "deny"),
        (PROJECT, "git --git-dir /x/.git commit", "deny"),
        (PROJECT, "git --work-tree /x commit", "deny"),
        (PROJECT, "\\git push", "deny"),
        (PROJECT, '"git" push', "deny"),
        (SPEC, "GIT_DIR=/tmp/x/.git git commit", "deny"),
        (PROJECT, "env GIT_DIR=x git push", "deny"),
        (PROJECT, "FOO=1 git commit", "deny"),
        (PROJECT, "xargs git push", "deny"),
        (PROJECT, "nohup git push &", "deny"),
        (PROJECT, "timeout 30 git push", "deny"),
        (PROJECT, "echo x | xargs -n1 git tag", "deny"),
        (PROJECT, "x=$(git commit -m y)", "deny"),
        (PROJECT, "npm run deploy", "deny"),
        (PROJECT, "cd x && npm run-script deploy", "deny"),
        (PROJECT, "yarn deploy", "deny"),
        (PROJECT, "npx gh-pages -d public", "deny"),
        (PROJECT, "./node_modules/.bin/gh-pages -d public", "deny"),
        (PROJECT, "git status && git log --oneline -3", "pass"),
        (PROJECT, "git stash push -m wip", "pass"),
        (PROJECT, "git log --grep=push", "pass"),
        (PROJECT, 'grep -n "git push" README.md', "pass"),
        (PROJECT, 'echo "git commit"', "pass"),
        (PROJECT, "grep gh-pages package.json", "pass"),
        (PROJECT, "npm run build", "pass"),
        (PROJECT, "", "pass"),
    ]

    def test_cases(self):
        """Every case gets its expected decision."""
        for cwd, command, want in self.CASES:
            with self.subTest(command=command, cwd=cwd):
                self.assertEqual(decide(command, cwd), want)

    def test_other_tools_pass(self):
        """Only the Bash tool is inspected."""
        self.assertEqual(decide("git push", PROJECT, tool="Read"), "pass")

    def test_missing_cwd_uses_process_cwd(self):
        """Without a cwd field the process directory decides."""
        with mock.patch("os.getcwd", return_value=PROJECT):
            self.assertEqual(decide("git commit -m x", None), "deny")
        with mock.patch("os.getcwd", return_value=SPEC):
            self.assertEqual(decide("git commit -m x", None), "pass")

    def test_deny_reason(self):
        """A deny names the rule in its reason."""
        event = {
            "tool_name": "Bash",
            "tool_input": {"command": "git push"},
            "cwd": PROJECT,
        }
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(json.dumps(event))), redirect_stdout(
            out
        ):
            with self.assertRaises(SystemExit):
                guard.main()
        decision = json.loads(out.getvalue())["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertIn("outside", decision["permissionDecisionReason"])

    def test_target_repo_chains_c_options(self):
        """Several -C options resolve one after another."""
        self.assertEqual(
            guard.target_repo(" -C /a -C b", "/base"), os.path.realpath("/a/b")
        )
        self.assertEqual(guard.target_repo("", "/base"), os.path.realpath("/base"))

    def test_runs_as_script(self):
        """Running the file as a script applies the same decision."""
        run = lambda: runpy.run_path(SCRIPT, run_name="__main__")
        self.assertEqual(decide("git commit -m x", PROJECT, run=run), "deny")


if __name__ == "__main__":
    unittest.main()
