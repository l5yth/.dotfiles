# SPDX-FileCopyrightText: 2026 Afri Blank (@l5yth)
# SPDX-License-Identifier: Unlicense
#
# This is free and unencumbered software released into the public domain.
# For more information, please refer to <https://unlicense.org>
"""Unit tests for ``worktree.py``.

Run from this directory: ``python3 -m unittest test_worktree``. Every test builds
throwaway repositories in a temporary directory, with git isolated from the
user's configuration, so nothing touches the real tree or the network.
"""

import contextlib
import fcntl
import importlib.util
import io
import json
import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "worktree.py")
_spec = importlib.util.spec_from_file_location("worktree", SCRIPT)
wt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wt)

# No global or system config: no signing key, no identity include, no hooks.
ISOLATED = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@example.invalid",
}
# Local submodules need the file transport, which git refuses by default.
FILE_PROTOCOL = {
    "GIT_CONFIG_COUNT": "1",
    "GIT_CONFIG_KEY_0": "protocol.file.allow",
    "GIT_CONFIG_VALUE_0": "always",
}


def run(*args, cwd):
    """Run a fixture git command and return its stripped stdout.

    Args:
        *args: The arguments after ``git``.
        cwd: The directory to run in.

    Returns:
        The command's stdout without surrounding whitespace.
    """
    done = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def write(path, text):
    """Write ``text`` to ``path``, creating parent directories.

    Args:
        path: The file to write.
        text: Its new content.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as handle:
        handle.write(text)


class Case(unittest.TestCase):
    """A scratch ``~/.src`` with an origin and a primary clone at ``o/r``."""

    def setUp(self):
        """Isolate git, patch the module's paths, build the fixture."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = os.path.realpath(tmp.name)
        env = mock.patch.dict(os.environ, ISOLATED)
        env.start()
        self.addCleanup(env.stop)
        for key in ("GIT_SSH_COMMAND", "GIT_DIR", "GIT_WORK_TREE"):
            os.environ.pop(key, None)
        self.src = os.path.join(self.tmp, ".src")
        self.root = os.path.join(self.src, ".wt")
        spec = os.path.join(self.src, "l5yth", "spec")
        for name, value in (("SRC", self.src), ("SPEC", spec), ("ROOT", self.root)):
            patcher = mock.patch.object(wt, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.origin = self.make_origin("")
        self.primary = self.clone(self.origin, "o", "r")

    def make_origin(self, tag, submodule=None):
        """Return a bare origin whose ``main`` has two commits.

        The second commit adds ``two.txt``; ``docs/a.txt`` exists from the first.

        Args:
            tag: Suffix that keeps several fixtures apart.
            submodule: A repository to add as the submodule ``sub``, or ``None``.

        Returns:
            The bare origin's path.
        """
        seed = os.path.join(self.tmp, f"seed{tag}")
        run("init", "-q", "-b", "main", seed, cwd=self.tmp)
        write(os.path.join(seed, "README.md"), "one\n")
        write(os.path.join(seed, "docs", "a.txt"), "a\n")
        run("add", ".", cwd=seed)
        run("commit", "-q", "-m", "one", cwd=seed)
        if submodule:
            run(
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                "-q",
                submodule,
                "sub",
                cwd=seed,
            )
        write(os.path.join(seed, "README.md"), "two\n")
        write(os.path.join(seed, "two.txt"), "2\n")
        run("add", ".", cwd=seed)
        run("commit", "-q", "-m", "two", cwd=seed)
        origin = os.path.join(self.tmp, f"origin{tag}.git")
        run("clone", "-q", "--bare", seed, origin, cwd=self.tmp)
        return origin

    def clone(self, origin, *parts):
        """Clone ``origin`` below the scratch tree and return the clone's path.

        Args:
            origin: The repository to clone.
            *parts: Path components below the scratch ``~/.src``.

        Returns:
            The clone's path.
        """
        path = os.path.join(self.src, *parts)
        run("clone", "-q", origin, path, cwd=self.tmp)
        return path

    def create(self, name, cwd=None):
        """Run ``create`` for ``name``.

        Args:
            name: The worktree name.
            cwd: The event's working directory; the primary clone by default.

        Returns:
            ``(path, stderr)``.
        """
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            path = wt.create({"name": name, "cwd": cwd or self.primary})
        return path, err.getvalue()

    def refused(self, event):
        """Run ``create`` and expect a refusal.

        Args:
            event: The create event.

        Returns:
            The refusal's message.
        """
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(wt.Refusal) as caught:
                wt.create(event)
        return str(caught.exception)

    def remove(self, path):
        """Run ``remove`` for ``path``.

        Args:
            path: The worktree path in the event.

        Returns:
            ``(removed, stderr)``.
        """
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            removed = wt.remove({"worktree_path": path})
        return removed, err.getvalue()

    def sweep(self):
        """Run ``sweep``.

        Returns:
            ``(stdout lines, stderr)``.
        """
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            wt.sweep()
        return out.getvalue().splitlines(), err.getvalue()

    def branch_exists(self, name):
        """Report whether the primary has the local branch ``name``.

        Args:
            name: The branch name.

        Returns:
            True when ``refs/heads/<name>`` exists.
        """
        done = subprocess.run(
            ["git", "-C", self.primary, "rev-parse", "--verify", "--quiet", name],
            capture_output=True,
        )
        return done.returncode == 0


class CreateTest(Case):
    """``create``: placement, branch, base, resume and refusals."""

    def test_branch_at_remote_default(self):
        """An ``l5y-`` name gets its own branch at origin/HEAD, untracked."""
        path, err = self.create("l5y-a-b")
        self.assertEqual(path, os.path.join(self.root, "o", "r", "l5y-a-b"))
        self.assertEqual(run("symbolic-ref", "--short", "HEAD", cwd=path), "l5y-a-b")
        self.assertEqual(
            run("rev-parse", "HEAD", cwd=path),
            run("rev-parse", "refs/remotes/origin/HEAD", cwd=self.primary),
        )
        config = subprocess.run(
            ["git", "-C", self.primary, "config", "branch.l5y-a-b.merge"],
            capture_output=True,
        )
        self.assertNotEqual(config.returncode, 0)
        self.assertFalse(os.path.exists(os.path.join(self.primary, ".claude")))
        self.assertNotIn("primary", err)

    def test_resume_reuses_without_fetching(self):
        """A second create returns the same worktree, even with origin gone."""
        path, _ = self.create("l5y-a-b")
        run(
            "remote",
            "set-url",
            "origin",
            os.path.join(self.tmp, "gone.git"),
            cwd=self.primary,
        )
        again, err = self.create("l5y-a-b")
        self.assertEqual(again, path)
        self.assertIn("reusing", err)

    def test_other_names_detach(self):
        """A subagent's name gets a detached worktree and no branch."""
        path, _ = self.create("agent-0123456789abcdef0")
        head = subprocess.run(
            ["git", "-C", path, "symbolic-ref", "-q", "HEAD"], capture_output=True
        )
        self.assertNotEqual(head.returncode, 0)
        self.assertFalse(self.branch_exists("agent-0123456789abcdef0"))

    def test_existing_local_branch(self):
        """An existing local branch of that name is checked out as it is."""
        run("branch", "l5y-l-t", "HEAD~1", cwd=self.primary)
        path, _ = self.create("l5y-l-t")
        self.assertEqual(
            run("rev-parse", "HEAD", cwd=path),
            run("rev-parse", "l5y-l-t", cwd=self.primary),
        )
        self.assertEqual(run("symbolic-ref", "--short", "HEAD", cwd=path), "l5y-l-t")

    def test_single_remote_branch(self):
        """A branch only origin has is checked out tracking origin."""
        run("branch", "l5y-r-t", "main~1", cwd=self.origin)
        path, _ = self.create("l5y-r-t")
        self.assertEqual(run("symbolic-ref", "--short", "HEAD", cwd=path), "l5y-r-t")
        self.assertEqual(
            run("config", "branch.l5y-r-t.merge", cwd=self.primary),
            "refs/heads/l5y-r-t",
        )

    def test_unsafe_names(self):
        """Names that are not one safe path component are refused."""
        for name in ("../x", "a/b", "", ".hidden"):
            with self.subTest(name=name):
                message = self.refused({"name": name, "cwd": self.primary})
                self.assertIn("unsafe worktree name", message)
        self.assertFalse(os.path.exists(self.root))

    def test_worktree_path_fallback(self):
        """Without ``name``, the basename of ``worktree_path`` serves."""
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            path = wt.create(
                {
                    "worktree_path": "/elsewhere/.claude/worktrees/l5y-w-p/",
                    "cwd": self.primary,
                }
            )
        self.assertEqual(path, os.path.join(self.root, "o", "r", "l5y-w-p"))

    def test_refused_locations(self):
        """The spec clone and anything not at ~/.src/<org>/<repo> are refused."""
        spec = self.clone(self.origin, "l5yth", "spec")
        outside = os.path.join(self.tmp, "elsewhere", "r")
        run("clone", "-q", self.origin, outside, cwd=self.tmp)
        deep = self.clone(self.origin, "a", "b", "c")
        hidden = self.clone(self.origin, ".wt", "x")
        plain = os.path.join(self.tmp, "plain")
        os.makedirs(plain)
        for cwd, words in (
            (spec, "spec clone"),
            (outside, "not a primary clone"),
            (deep, "not a primary clone"),
            (hidden, "not a primary clone"),
            (self.origin, "not a primary clone"),
            (plain, "not inside a git repository"),
        ):
            with self.subTest(cwd=cwd):
                self.assertIn(words, self.refused({"name": "l5y-x-y", "cwd": cwd}))
        self.assertEqual(os.listdir(self.root), ["x"])

    def test_fetch_failure(self):
        """A failed fetch creates nothing (maintainer, 2026-10-03)."""
        run(
            "remote",
            "set-url",
            "origin",
            os.path.join(self.tmp, "gone.git"),
            cwd=self.primary,
        )
        self.assertIn("fetch", self.refused({"name": "l5y-f-t", "cwd": self.primary}))
        self.assertFalse(os.path.exists(os.path.join(self.root, "o", "r", "l5y-f-t")))

    def test_unset_origin_head(self):
        """An origin/HEAD the fetch cannot recreate stops creation and names the fix."""
        run("config", "remote.origin.followRemoteHEAD", "never", cwd=self.primary)
        run("remote", "set-head", "origin", "-d", cwd=self.primary)
        message = self.refused({"name": "l5y-h-t", "cwd": self.primary})
        self.assertIn("set-head origin --auto", message)

    def test_fetch_recreates_origin_head(self):
        """By default git's fetch recreates a missing origin/HEAD (git 2.48+)."""
        run("remote", "set-head", "origin", "-d", cwd=self.primary)
        path, _ = self.create("l5y-h-c")
        self.assertTrue(os.path.isdir(path))

    def test_branch_checked_out_elsewhere(self):
        """A branch the primary has checked out gets no second worktree."""
        run("switch", "-q", "-c", "l5y-busy", cwd=self.primary)
        message = self.refused({"name": "l5y-busy", "cwd": self.primary})
        self.assertIn("git worktree add", message)
        self.assertFalse(os.path.exists(os.path.join(self.root, "o", "r", "l5y-busy")))

    def test_existing_path_not_a_worktree(self):
        """A stray directory at the target is refused, not reused."""
        os.makedirs(os.path.join(self.root, "o", "r", "l5y-x-t"))
        message = self.refused({"name": "l5y-x-t", "cwd": self.primary})
        self.assertIn("exists and is not a worktree", message)

    def test_missing_cwd_uses_process_directory(self):
        """Without ``cwd`` the process's own directory decides."""
        with mock.patch("os.getcwd", return_value=self.primary):
            with contextlib.redirect_stderr(io.StringIO()):
                path = wt.create({"name": "l5y-c-w"})
        self.assertTrue(os.path.isdir(path))

    def test_takes_the_lock_and_batch_ssh(self):
        """Creation holds the repository lock and fetches through network_env."""
        with mock.patch.object(wt.fcntl, "flock", wraps=fcntl.flock) as flock:
            with mock.patch.object(wt, "network_env", wraps=wt.network_env) as net:
                self.create("l5y-l-k")
        self.assertIn(fcntl.LOCK_EX, [c.args[1] for c in flock.call_args_list])
        net.assert_called_with(self.primary)
        self.assertTrue(os.path.exists(os.path.join(self.primary, ".git", wt.LOCK)))


class SubmoduleTest(Case):
    """Submodules are initialised, a failed init rolls back, dirt keeps them."""

    def setUp(self):
        """Add a primary at ``o/s`` whose origin has the submodule ``sub``."""
        super().setUp()
        self.subseed = os.path.join(self.tmp, "subseed")
        run("init", "-q", "-b", "main", self.subseed, cwd=self.tmp)
        write(os.path.join(self.subseed, "lib.txt"), "lib\n")
        run("add", ".", cwd=self.subseed)
        run("commit", "-q", "-m", "lib", cwd=self.subseed)
        origin = self.make_origin("-s", submodule=self.subseed)
        self.primary = self.clone(origin, "o", "s")
        env = mock.patch.dict(os.environ, FILE_PROTOCOL)
        env.start()
        self.addCleanup(env.stop)

    def test_initialised_and_removable(self):
        """The submodule is checked out, and a clean worktree with it still goes."""
        path, _ = self.create("l5y-s-m")
        self.assertTrue(os.path.isfile(os.path.join(path, "sub", "lib.txt")))
        removed, _ = self.remove(path)
        self.assertTrue(removed)
        self.assertFalse(os.path.exists(path))

    def test_failed_init_rolls_back(self):
        """A failed submodule init removes the worktree and keeps the branch."""
        os.rename(self.subseed, self.subseed + ".moved")
        message = self.refused({"name": "l5y-s-f", "cwd": self.primary})
        self.assertIn("submodule update failed", message)
        self.assertFalse(os.path.exists(os.path.join(self.root, "o", "s", "l5y-s-f")))
        self.assertTrue(self.branch_exists("l5y-s-f"))

    def test_dirty_submodule_keeps(self):
        """An untracked file inside the submodule keeps the worktree."""
        path, _ = self.create("l5y-s-d")
        write(os.path.join(path, "sub", "wip.txt"), "wip\n")
        removed, err = self.remove(path)
        self.assertFalse(removed)
        self.assertIn("changes inside a submodule", err)


class PrimaryTest(Case):
    """The primary clone is reported, never blocks, and moves only when safe."""

    def test_fast_forwards_when_safe(self):
        """Clean, on its default branch and behind: fast-forwarded."""
        run("reset", "-q", "--keep", "HEAD~1", cwd=self.primary)
        _, err = self.create("l5y-f-f")
        self.assertIn("fast-forwarded 1 commit(s) to origin/main", err)
        self.assertEqual(
            run("rev-parse", "HEAD", cwd=self.primary),
            run("rev-parse", "origin/main", cwd=self.primary),
        )

    def test_reports_and_continues(self):
        """Another branch, a detached HEAD, dirt or local commits: reported only."""
        cases = (
            (("switch", "-q", "-c", "l5y-side"), "on l5y-side, not main"),
            (("switch", "-q", "--detach"), "on a detached HEAD, not main"),
        )
        for index, (command, words) in enumerate(cases):
            with self.subTest(words=words):
                run(*command, cwd=self.primary)
                path, err = self.create(f"l5y-p-{index}")
                self.assertTrue(os.path.isdir(path))
                self.assertIn(words, err)
                self.assertIn("not fast-forwarded", err)
                run("switch", "-q", "main", cwd=self.primary)

    def test_dirty_primary(self):
        """A dirty primary is reported and left exactly as it was."""
        run("reset", "-q", "--keep", "HEAD~1", cwd=self.primary)
        write(os.path.join(self.primary, "README.md"), "local\n")
        before = run("rev-parse", "HEAD", cwd=self.primary)
        _, err = self.create("l5y-d-p")
        self.assertIn("dirty; not fast-forwarded", err)
        self.assertEqual(run("rev-parse", "HEAD", cwd=self.primary), before)
        self.assertEqual(run("status", "--porcelain", cwd=self.primary), "M README.md")

    def test_primary_ahead(self):
        """Local commits on the primary are reported, not pushed or moved."""
        write(os.path.join(self.primary, "local.txt"), "x\n")
        run("add", ".", cwd=self.primary)
        run("commit", "-q", "-m", "local", cwd=self.primary)
        _, err = self.create("l5y-a-p")
        self.assertIn("1 ahead of and 0 behind origin/main", err)

    def test_fast_forward_failure(self):
        """A fast-forward git refuses is reported, and creation continues."""
        run("reset", "-q", "--keep", "HEAD~1", cwd=self.primary)
        write(os.path.join(self.primary, "two.txt"), "untracked\n")
        path, err = self.create("l5y-f-x")
        self.assertIn("fast-forward failed; not fast-forwarded", err)
        self.assertTrue(os.path.isdir(path))


class NetworkEnvTest(Case):
    """SSH runs in batch mode, and no prompt reaches a terminal."""

    def test_default_ssh(self):
        """Without configuration, plain ssh gains batch mode."""
        env = wt.network_env(self.primary)
        self.assertEqual(env["GIT_SSH_COMMAND"], "ssh -o BatchMode=yes")
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")

    def test_appends_to_core_sshcommand(self):
        """The repository's own ssh command keeps its identity file."""
        run("config", "core.sshCommand", "ssh -i /k", cwd=self.primary)
        env = wt.network_env(self.primary)
        self.assertEqual(env["GIT_SSH_COMMAND"], "ssh -i /k -o BatchMode=yes")

    def test_honours_environment(self):
        """A GIT_SSH_COMMAND already set is left alone."""
        with mock.patch.dict(os.environ, {"GIT_SSH_COMMAND": "ssh -p 2"}):
            env = wt.network_env(self.primary)
        self.assertEqual(env["GIT_SSH_COMMAND"], "ssh -p 2")


class RemoveTest(Case):
    """``remove``: only a worktree that holds no work goes."""

    def test_clean_worktree_goes_with_its_branch(self):
        """A clean worktree is removed and its branch deleted with -d."""
        path, _ = self.create("l5y-a-b")
        removed, _ = self.remove(path)
        self.assertTrue(removed)
        self.assertFalse(os.path.exists(path))
        self.assertFalse(self.branch_exists("l5y-a-b"))

    def test_work_keeps_it(self):
        """Untracked files, edits and commits that exist only here keep it."""
        path, _ = self.create("l5y-w-k")
        cases = (
            ("untracked", "uncommitted or untracked changes"),
            ("modified", "uncommitted or untracked changes"),
            ("committed", "commits that exist only here"),
        )
        for kind, words in cases:
            with self.subTest(kind=kind):
                if kind == "untracked":
                    write(os.path.join(path, "wip.txt"), "wip\n")
                elif kind == "modified":
                    os.remove(os.path.join(path, "wip.txt"))
                    write(os.path.join(path, "README.md"), "edited\n")
                else:
                    run("commit", "-q", "-am", "local", cwd=path)
                removed, err = self.remove(path)
                self.assertFalse(removed)
                self.assertIn(words, err)
                self.assertTrue(os.path.isdir(path))

    def test_in_use_keeps_it(self):
        """A process working inside the worktree keeps it."""
        path, _ = self.create("l5y-u-t")
        proc = subprocess.Popen(["sleep", "60"], cwd=path)
        self.addCleanup(proc.wait)
        self.addCleanup(proc.kill)
        removed, err = self.remove(path)
        self.assertFalse(removed)
        self.assertIn(f"in use by pid {proc.pid}", err)

    def test_own_ancestors_do_not_count(self):
        """The session asking for its own removal may stand inside it."""
        path, _ = self.create("l5y-o-a")
        here = os.getcwd()
        self.addCleanup(os.chdir, here)
        os.chdir(path)
        removed, _ = self.remove(path)
        self.assertTrue(removed)

    def test_locked_keeps_it(self):
        """A locked worktree stays: one --force does not override a lock."""
        path, _ = self.create("l5y-l-t")
        run("worktree", "lock", path, cwd=self.primary)
        removed, err = self.remove(path)
        self.assertFalse(removed)
        self.assertIn("locked", err)

    def test_status_failure_keeps_it(self):
        """A worktree git cannot read stays."""
        path, _ = self.create("l5y-s-x")
        write(
            os.path.join(self.primary, ".git", "worktrees", "l5y-s-x", "index"), "junk"
        )
        removed, err = self.remove(path)
        self.assertFalse(removed)
        self.assertIn("git status failed", err)

    def test_branch_kept_when_unmerged(self):
        """git branch -d refusing keeps the branch, and says so: never -D."""
        path, _ = self.create("l5y-k-t")
        run("reset", "-q", "--keep", "HEAD~1", cwd=self.primary)
        removed, err = self.remove(path)
        self.assertTrue(removed)
        self.assertTrue(self.branch_exists("l5y-k-t"))
        self.assertIn("kept branch l5y-k-t", err)

    def test_removal_failure_keeps_it(self):
        """When git cannot remove the worktree, it is reported as kept."""
        path, _ = self.create("l5y-r-f")
        real_git = wt.git

        def failing(args, cwd, **kwargs):
            """Fail ``worktree remove``; run every other git call for real."""
            if args[:2] == ["worktree", "remove"]:
                return subprocess.CompletedProcess(args, 1, "", "")
            return real_git(args, cwd, **kwargs)

        with mock.patch.object(wt, "git", side_effect=failing):
            removed, err = self.remove(path)
        self.assertFalse(removed)
        self.assertIn("git worktree remove failed", err)

    def test_refused_paths(self):
        """Paths outside ~/.src/.wt, missing paths and empty events stay."""
        os.makedirs(os.path.join(self.root, "o", "r", "plain"))
        path, _ = self.create("l5y-p-s")
        os.makedirs(os.path.join(path, "subdir"))
        for target, words in (
            ("/tmp", "not a worktree under"),
            (self.primary, "not a worktree under"),
            (os.path.join(self.root, "o", "r", "missing"), "not a worktree under"),
            (os.path.join(self.root, "o", "r", "plain"), "not a git worktree"),
            (os.path.join(path, "subdir"), "not a worktree of"),
        ):
            with self.subTest(target=target):
                removed, err = self.remove(target)
                self.assertFalse(removed)
                self.assertIn(words, err)
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertFalse(wt.remove({}))
        self.assertIn("an unnamed path", err.getvalue())

    def test_path_key_fallback(self):
        """An event naming ``path`` instead of ``worktree_path`` works too."""
        path, _ = self.create("l5y-p-k")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertTrue(wt.remove({"path": path}))


class SweepTest(Case):
    """``sweep``: one line per worktree, emptied folders removed."""

    def test_mixed(self):
        """Clean goes; untracked, locked and non-worktree folders stay."""
        clean, _ = self.create("l5y-s-1")
        dirty, _ = self.create("l5y-s-2")
        held, _ = self.create("l5y-s-3")
        write(os.path.join(dirty, "wip.txt"), "wip\n")
        run("worktree", "lock", held, cwd=self.primary)
        plain = os.path.join(self.root, "o", "r", "plain")
        os.makedirs(plain)
        write(os.path.join(self.root, "o", "r", "stray.txt"), "x\n")
        lines, _ = self.sweep()
        self.assertEqual(
            lines,
            [
                f"removed {clean}",
                f"kept {dirty}: uncommitted or untracked changes",
                f"kept {held}: locked",
                f"kept {plain}: not a git worktree",
            ],
        )
        self.assertTrue(os.path.isdir(os.path.join(self.root, "o", "r")))

    def test_empties_folders(self):
        """Folders a sweep leaves empty are removed."""
        self.create("l5y-e-f")
        lines, _ = self.sweep()
        self.assertEqual(len(lines), 1)
        self.assertFalse(os.path.exists(os.path.join(self.root, "o")))

    def test_keeps_its_own_worktree(self):
        """A sweep run from inside a worktree keeps that worktree."""
        path, _ = self.create("l5y-o-w")
        here = os.getcwd()
        self.addCleanup(os.chdir, here)
        os.chdir(path)
        lines, _ = self.sweep()
        self.assertEqual(lines, [f"kept {path}: in use by pid {os.getpid()}"])

    def test_nothing_to_sweep(self):
        """Without ~/.src/.wt a sweep prints nothing."""
        self.assertEqual(self.sweep(), ([], ""))


class ProcessTest(unittest.TestCase):
    """``ancestors`` and ``users`` read ``/proc`` and degrade quietly."""

    def test_ancestors(self):
        """This process and its parent are among the ancestors."""
        pids = wt.ancestors()
        self.assertIn(os.getpid(), pids)
        if os.getppid() > 1:
            self.assertIn(os.getppid(), pids)

    def test_ancestors_unreadable(self):
        """An unreadable /proc leaves only this process."""
        with mock.patch("builtins.open", side_effect=OSError):
            self.assertEqual(wt.ancestors(), {os.getpid()})

    def test_users(self):
        """A process inside the directory is found unless excluded."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = os.path.realpath(tmp)
            inner = os.path.join(tmp, "inner")
            os.makedirs(inner)
            proc = subprocess.Popen(["sleep", "60"], cwd=inner)
            try:
                self.assertIn(proc.pid, wt.users(tmp))
                self.assertNotIn(proc.pid, wt.users(tmp, {proc.pid}))
                self.assertNotIn(proc.pid, wt.users(tmp + "-other"))
            finally:
                proc.kill()
                proc.wait()

    def test_users_unreadable(self):
        """No /proc, or entries that vanish, yield no users."""
        with mock.patch.object(wt.os, "listdir", side_effect=OSError):
            self.assertEqual(wt.users("/x"), [])
        with mock.patch.object(wt.os, "listdir", return_value=["self", "999999999"]):
            self.assertEqual(wt.users("/x"), [])


class MainTest(Case):
    """``main`` dispatches the three verbs and turns refusals into exit 1."""

    def call(self, argv, stdin=""):
        """Run ``main`` with ``stdin``.

        Args:
            argv: The arguments after the script name.
            stdin: The text on stdin.

        Returns:
            ``(status, stdout, stderr)``.
        """
        out, err = io.StringIO(), io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(stdin)):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                status = wt.main(argv)
        return status, out.getvalue(), err.getvalue()

    def test_create_prints_the_path_alone(self):
        """stdout carries the path and nothing else: Claude Code starts there."""
        event = json.dumps({"name": "l5y-m-c", "cwd": self.primary})
        status, out, _ = self.call(["create"], event)
        self.assertEqual(status, 0)
        self.assertEqual(out, os.path.join(self.root, "o", "r", "l5y-m-c") + "\n")

    def test_remove_and_sweep(self):
        """remove exits 0 when the worktree went and 1 when it stayed."""
        path, _ = self.create("l5y-m-r")
        self.assertEqual(
            self.call(["remove"], json.dumps({"worktree_path": "/tmp"}))[0], 1
        )
        self.assertEqual(
            self.call(["remove"], json.dumps({"worktree_path": path}))[0], 0
        )
        self.assertEqual(self.call(["sweep"])[0], 0)

    def test_refusals_exit_1(self):
        """Usage errors, unreadable events and refusals exit 1 with a reason."""
        for argv, stdin, words in (
            ([], "", "usage"),
            (["bogus"], "", "usage"),
            (["create"], "not json", "unreadable event"),
            (["create"], "[]", "not a JSON object"),
            (["create"], json.dumps({"name": "../x", "cwd": self.primary}), "unsafe"),
        ):
            with self.subTest(argv=argv, stdin=stdin):
                status, out, err = self.call(argv, stdin)
                self.assertEqual((status, out), (1, ""))
                self.assertIn(words, err)

    def test_runs_as_script(self):
        """Running the file as a script exits with main's status."""
        with mock.patch.dict(os.environ, {"HOME": self.tmp}):
            with mock.patch.object(sys, "argv", ["worktree.py"]):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as caught:
                        runpy.run_path(SCRIPT, run_name="__main__")
        self.assertEqual(caught.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
