#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Afri Blank (@l5yth)
# SPDX-License-Identifier: Unlicense
#
# This is free and unencumbered software released into the public domain.
# For more information, please refer to <https://unlicense.org>
"""Worktree hook: one task, one branch, one worktree under ``~/.src/.wt``.

Registered for Claude Code's ``WorktreeCreate`` and ``WorktreeRemove`` events,
and run by hand for ``sweep`` (SPEC §Feature: Worktrees, WT1 to WT4):

- ``create`` reads the event on stdin, makes the worktree at
  ``~/.src/.wt/<org>/<repo>/<name>`` and prints its path, and nothing else, on
  stdout. Claude Code starts the session in whatever path it prints.
- ``remove`` reads the event on stdin and removes the worktree only when no
  work can be lost. Exit 1 keeps it: the directory stays and the removal fails.
- ``sweep`` applies the same test to every worktree under ``~/.src/.wt`` and
  prints one line per path.

Every git message goes to stderr. A refusal exits 1 with its reason on stderr.
"""

import contextlib
import fcntl
import json
import os
import re
import subprocess
import sys

SRC = os.path.realpath(os.path.expanduser("~/.src"))
SPEC = os.path.join(SRC, "l5yth", "spec")
ROOT = os.path.join(SRC, ".wt")
# Kept in the repository's common git directory, which every worktree shares.
LOCK = "l5y-worktree.lock"
# One path component: no separator, no leading dot, so no `..` and no hidden name.
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


class Refusal(Exception):
    """A reason to stop without a worktree, shown on stderr with exit 1."""


def say(message):
    """Write one line to stderr, where Claude Code and the terminal show it.

    Args:
        message: The text after the ``worktree:`` prefix.
    """
    print(f"worktree: {message}", file=sys.stderr)


def git(args, cwd, check=True, echo=False, env=None):
    """Run git in ``cwd`` and return the completed process.

    Args:
        args: The arguments after ``git -C <cwd>``.
        cwd: The directory git runs in.
        check: Raise ``Refusal`` when git exits non-zero.
        echo: Copy git's stdout to our stderr, for commands that report progress;
            our stdout is reserved for the worktree path.
        env: The child's environment; ``None`` inherits ours.

    Returns:
        The ``subprocess.CompletedProcess``, with ``stdout`` as text.

    Raises:
        Refusal: When ``check`` is set and git fails.
    """
    result = subprocess.run(
        ["git", "-C", cwd, *args], capture_output=True, text=True, env=env
    )
    if echo:
        sys.stderr.write(result.stdout)
    sys.stderr.write(result.stderr)
    if check and result.returncode:
        raise Refusal(f"git {' '.join(args)} failed in {cwd}")
    return result


def network_env(primary):
    """Return the environment for git commands that reach a remote.

    SSH runs in batch mode, appended to the repository's own
    ``core.sshCommand``, and git asks for no credentials on a terminal, so a
    host-key or password prompt fails at once instead of hanging until the
    hook's timeout: the trap ``install.sh`` closed for the spec clone. A
    ``GIT_SSH_COMMAND`` already in the environment is honoured.

    Args:
        primary: The primary clone, whose ``core.sshCommand`` applies.

    Returns:
        A copy of ``os.environ`` with the two settings applied.
    """
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    if "GIT_SSH_COMMAND" not in env:
        ssh = git(["config", "--get", "core.sshCommand"], primary, check=False)
        env["GIT_SSH_COMMAND"] = (ssh.stdout.strip() or "ssh") + " -o BatchMode=yes"
    return env


def common_dir(path):
    """Return the real path of the git directory every worktree of ``path`` shares.

    Args:
        path: A directory inside a repository or one of its worktrees.

    Returns:
        The common git directory, or an empty string outside a repository.
    """
    result = git(
        ["rev-parse", "--path-format=absolute", "--git-common-dir"], path, check=False
    )
    return "" if result.returncode else os.path.realpath(result.stdout.strip())


@contextlib.contextmanager
def locked(primary):
    """Hold the repository's exclusive lock while the block runs.

    Two sessions created at once would otherwise race on ``git fetch`` and on
    the worktree list.

    Args:
        primary: The primary clone.

    Yields:
        Nothing; the lock is released when the block ends.
    """
    with open(os.path.join(common_dir(primary), LOCK), "a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def primary_of(cwd):
    """Return the primary clone ``cwd`` belongs to, with its org and repo (WT3 step 1).

    Args:
        cwd: The event's working directory.

    Returns:
        ``(primary, org, repo)`` for a primary at exactly ``~/.src/<org>/<repo>``.

    Raises:
        Refusal: Outside a repository, for the spec clone, for a submodule or a
            bare repository, and for anything that is not ``~/.src/<org>/<repo>``.
    """
    common = common_dir(cwd)
    if not common:
        raise Refusal(f"{cwd} is not inside a git repository")
    primary = os.path.dirname(common)
    if primary == os.path.realpath(SPEC):
        raise Refusal("the spec clone takes no worktrees")
    parts = os.path.relpath(primary, SRC).split(os.sep)
    if (
        os.path.basename(common) != ".git"
        or len(parts) != 2
        or parts[0] in ("..", ".wt")
    ):
        raise Refusal(f"{primary} is not a primary clone at {SRC}/<org>/<repo>")
    return primary, parts[0], parts[1]


def name_of(event):
    """Return the worktree name a create event asks for (WT3 step 2).

    Claude Code 2.1.288 sends ``name``; the hooks reference describes
    ``worktree_path``, whose basename serves when ``name`` is absent.

    Args:
        event: The decoded ``WorktreeCreate`` input.

    Returns:
        The name, a single safe path component.

    Raises:
        Refusal: For an empty or unsafe name.
    """
    path = str(event.get("worktree_path") or "").rstrip("/")
    name = str(event.get("name") or os.path.basename(path))
    if not NAME.match(name):
        raise Refusal(f"unsafe worktree name: {name!r}")
    return name


def worktrees(primary):
    """Return the repository's worktrees and the attribute words git lists for each.

    Args:
        primary: The primary clone.

    Returns:
        ``{real path: {"HEAD", "branch", "locked", ...}}`` from
        ``git worktree list --porcelain``.
    """
    found, path = {}, None
    for line in git(["worktree", "list", "--porcelain"], primary).stdout.splitlines():
        if line.startswith("worktree "):
            path = os.path.realpath(line[len("worktree ") :])
            found[path] = set()
        elif line and path:
            found[path].add(line.split(" ", 1)[0])
    return found


def base_of(primary):
    """Return the remote default branch to branch from, such as ``origin/main`` (WT3 step 4).

    Args:
        primary: The primary clone.

    Returns:
        The ref ``refs/remotes/origin/HEAD`` points at, without ``refs/remotes/``.

    Raises:
        Refusal: When ``origin/HEAD`` is unset, naming the command that sets it.
    """
    ref = git(
        ["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"], primary, check=False
    )
    if not ref.stdout.strip():
        raise Refusal(
            f"origin/HEAD is not set; run: git -C {primary} remote set-head origin --auto"
        )
    return ref.stdout.strip().removeprefix("refs/remotes/")


def tend(primary, base):
    """Fast-forward the primary clone when that is safe, else report it (WT3 step 5).

    The primary's state never blocks: the task branches from ``base``, so
    nothing in the primary can leak into it.

    Args:
        primary: The primary clone.
        base: The remote default branch, such as ``origin/main``.
    """
    default = base.split("/", 1)[1]
    head = git(["symbolic-ref", "--quiet", "--short", "HEAD"], primary, check=False)
    branch = head.stdout.strip()
    status = git(
        ["status", "--porcelain", "--untracked-files=no"], primary, check=False
    )
    counts = git(
        ["rev-list", "--left-right", "--count", f"HEAD...{base}"], primary, check=False
    )
    ahead, behind = (counts.stdout.split() + ["?", "?"])[:2]
    if branch != default:
        state = f"on {branch or 'a detached HEAD'}, not {default}"
    elif status.stdout.strip():
        state = "dirty"
    elif ahead != "0":
        state = f"{ahead} ahead of and {behind} behind {base}"
    elif behind == "0":
        return
    elif git(["merge", "--ff-only", "--quiet", base], primary, check=False).returncode:
        state = "fast-forward failed"
    else:
        say(f"primary {primary}: fast-forwarded {behind} commit(s) to {base}")
        return
    say(f"primary {primary}: {state}; not fast-forwarded")


def how(primary, name, base, path):
    """Return the ``git worktree add`` arguments for ``name`` (WT3 step 6).

    Args:
        primary: The primary clone.
        name: The worktree name.
        base: The remote default branch.
        path: Where the worktree goes.

    Returns:
        Arguments that check out an ``l5y-`` branch, existing or new, or a
        detached HEAD for any other name, so subagents leave no branch behind.
    """
    if not name.startswith("l5y-"):
        return ["--detach", path, base]
    local = git(
        ["rev-parse", "--verify", "--quiet", f"refs/heads/{name}"], primary, check=False
    )
    remote = git(
        ["for-each-ref", "--format=%(refname)", f"refs/remotes/*/{name}"], primary
    ).stdout.split()
    if local.returncode == 0 or len(remote) == 1:
        # git checks out the local branch, or makes one tracking the remote one.
        return [path, name]
    return ["--no-track", "-b", name, path, base]


def create(event):
    """Make the worktree a ``WorktreeCreate`` event asks for (WT3).

    Args:
        event: The decoded hook input.

    Returns:
        The worktree's path.

    Raises:
        Refusal: When any step fails; nothing is left behind.
    """
    primary, org, repo = primary_of(event.get("cwd") or os.getcwd())
    name = name_of(event)
    path = os.path.join(os.path.realpath(ROOT), org, repo, name)
    # An existing worktree opens before any fetch, so it works offline.
    if os.path.realpath(path) in worktrees(primary):
        say(f"reusing {path}")
        return path
    if os.path.lexists(path):
        raise Refusal(f"{path} exists and is not a worktree of {primary}")
    with locked(primary):
        fetch = git(
            ["fetch", "--quiet", "origin"],
            primary,
            check=False,
            echo=True,
            env=network_env(primary),
        )
        if fetch.returncode:
            raise Refusal(f"git fetch origin failed in {primary}; no worktree is made")
        base = base_of(primary)
        tend(primary, base)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        git(["worktree", "add", *how(primary, name, base, path)], primary, echo=True)
        if os.path.exists(os.path.join(path, ".gitmodules")):
            update = git(
                ["submodule", "update", "--init", "--recursive"],
                path,
                check=False,
                echo=True,
                env=network_env(primary),
            )
            if update.returncode:
                git(["worktree", "remove", "--force", path], primary, check=False)
                raise Refusal(
                    f"git submodule update failed in {path}; removed it again"
                )
    return path


def ancestors():
    """Return this process and every ancestor, read from ``/proc``.

    Returns:
        A set of PIDs, from ``os.getpid()`` up to, not including, PID 1.
    """
    pids, pid = set(), os.getpid()
    while pid > 1 and pid not in pids:
        pids.add(pid)
        try:
            with open(f"/proc/{pid}/stat") as stat:
                pid = int(stat.read().rsplit(")", 1)[1].split()[1])
        except (OSError, IndexError, ValueError):
            break
    return pids


def users(path, exclude=frozenset()):
    """Return the PIDs whose working directory is ``path`` or inside it.

    A ``claude -w`` session's own process runs with its worktree as working
    directory, so this is what keeps one session's ``sweep`` from removing
    another session's clean worktree.

    Args:
        path: The real path of a worktree.
        exclude: PIDs to leave out.

    Returns:
        Sorted PIDs; empty where ``/proc`` is unreadable.
    """
    found = []
    try:
        entries = os.listdir("/proc")
    except OSError:
        return found
    for entry in entries:
        if not entry.isdigit() or int(entry) in exclude:
            continue
        try:
            cwd = os.readlink(f"/proc/{entry}/cwd")
        except OSError:
            continue
        if cwd == path or cwd.startswith(path + os.sep):
            found.append(int(entry))
    return sorted(found)


def holds_work(path, exclude):
    """Return why a worktree must stay, or an empty string when it may go (WT4).

    ``--ignore-submodules=dirty`` leaves a submodule's own changes to the
    second check and still reports a submodule moved to another commit.

    Args:
        path: The real path of a worktree.
        exclude: PIDs that do not count as users, see ``users``.

    Returns:
        The reason, or ``""``.
    """
    pids = users(path, exclude)
    if pids:
        return "in use by pid " + ", ".join(map(str, pids))
    status = git(
        ["status", "--porcelain", "--ignore-submodules=dirty"], path, check=False
    )
    if status.returncode:
        return "git status failed"
    if status.stdout.strip():
        return "uncommitted or untracked changes"
    subs = git(
        ["submodule", "foreach", "--quiet", "--recursive", "git status --porcelain"],
        path,
        check=False,
    )
    if subs.returncode or subs.stdout.strip():
        return "changes inside a submodule"
    unique = git(["rev-list", "HEAD", "--not", "--remotes"], path, check=False)
    if unique.returncode or unique.stdout.strip():
        return "commits that exist only here"
    return ""


def retire(path, exclude):
    """Remove one worktree, then its branch, when no work can be lost (WT4).

    ``--force`` is passed because git demands it for any worktree with
    submodules; the checks above stand in for git's own. One ``--force`` does
    not override a lock. The branch goes with ``git branch -d`` only.

    Args:
        path: The real path of a worktree under ``~/.src/.wt``.
        exclude: PIDs that do not count as users, see ``users``.

    Returns:
        ``(True, "")`` when it went, else ``(False, reason)``.
    """
    common = common_dir(path)
    if not common:
        return False, "not a git worktree"
    primary = os.path.dirname(common)
    with locked(primary):
        info = worktrees(primary).get(path)
        if info is None:
            return False, f"not a worktree of {primary}"
        if "locked" in info:
            return False, "locked"
        reason = holds_work(path, exclude)
        if reason:
            return False, reason
        head = git(["symbolic-ref", "--quiet", "--short", "HEAD"], path, check=False)
        removal = git(["worktree", "remove", "--force", path], primary, check=False)
        if removal.returncode:
            return False, "git worktree remove failed"
        branch = head.stdout.strip()
        if branch and git(["branch", "-d", branch], primary, check=False).returncode:
            say(f"kept branch {branch}: git branch -d refused to delete it")
    return True, ""


def remove(event):
    """Remove the worktree a ``WorktreeRemove`` event names, when nothing is lost.

    The session asking for its own removal runs inside the worktree, so this
    process's ancestors do not count as users.

    Args:
        event: The decoded hook input.

    Returns:
        Whether the worktree went.
    """
    path = str(event.get("worktree_path") or event.get("path") or "")
    real = os.path.realpath(path) if path else ""
    if not real.startswith(os.path.realpath(ROOT) + os.sep) or not os.path.isdir(real):
        say(f"kept {path or 'an unnamed path'}: not a worktree under {ROOT}")
        return False
    removed, reason = retire(real, ancestors())
    if not removed:
        say(f"kept {real}: {reason}")
    return removed


def folders(path):
    """Return the sorted names of the directories in ``path``.

    Args:
        path: A directory, which may be missing.

    Returns:
        Directory names; empty when ``path`` is missing.
    """
    if not os.path.isdir(path):
        return []
    return sorted(e for e in os.listdir(path) if os.path.isdir(os.path.join(path, e)))


def sweep():
    """Retire every worktree under ``~/.src/.wt`` and print one line per path (WT4).

    Nothing is excluded from the users check, so the worktree ``sweep`` runs
    from is in use and stays.
    """
    root = os.path.realpath(ROOT)
    for org in folders(root):
        for repo in folders(os.path.join(root, org)):
            folder = os.path.join(root, org, repo)
            for name in folders(folder):
                path = os.path.join(folder, name)
                removed, reason = retire(path, frozenset())
                print(f"removed {path}" if removed else f"kept {path}: {reason}")
            primary = os.path.join(SRC, org, repo)
            if os.path.isdir(primary):
                git(["worktree", "prune"], primary, check=False)
            with contextlib.suppress(OSError):
                os.rmdir(folder)
        with contextlib.suppress(OSError):
            os.rmdir(os.path.join(root, org))


def read_event():
    """Return the hook input from stdin.

    Returns:
        The decoded JSON object.

    Raises:
        Refusal: When stdin holds no JSON object.
    """
    try:
        event = json.load(sys.stdin)
    except ValueError as error:
        raise Refusal(f"unreadable event: {error}") from error
    if not isinstance(event, dict):
        raise Refusal("the event is not a JSON object")
    return event


def main(argv=None):
    """Run ``create``, ``remove`` or ``sweep`` and return the exit status.

    Args:
        argv: The arguments after the script name; ``None`` reads ``sys.argv``.

    Returns:
        0 on success, 1 on a refusal or a kept worktree.
    """
    verb = (sys.argv[1:] if argv is None else argv)[:1]
    try:
        if verb == ["create"]:
            print(create(read_event()))
            return 0
        if verb == ["remove"]:
            return 0 if remove(read_event()) else 1
        if verb == ["sweep"]:
            sweep()
            return 0
        raise Refusal("usage: worktree.py create|remove|sweep")
    except Refusal as error:
        say(str(error))
        return 1


if __name__ == "__main__":
    sys.exit(main())
