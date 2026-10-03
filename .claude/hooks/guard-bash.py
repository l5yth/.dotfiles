#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Afri Blank (@l5yth)
# SPDX-License-Identifier: Unlicense
#
# This is free and unencumbered software released into the public domain.
# For more information, please refer to <https://unlicense.org>
"""PreToolUse guard for the Bash tool.

Denies, whatever wrapper or flag carries them:

- ``git commit``, ``git push`` and ``git tag`` outside ``~/.src/l5yth/spec``
  (the global rules allow commits and pushes only there), and any forced push;
- deploy scripts that publish a site: ``npm run deploy``, ``yarn deploy``,
  ``gh-pages``;
- the destructive git commands of the deny list, which match literal prefixes
  only and so miss ``git -C <dir>`` and wrapped forms: ``reset --hard``,
  ``clean``, ``restore``, ``checkout`` with ``--``, ``.`` or ``-f``, ``switch``
  with ``-f`` or ``--discard-changes``, ``branch -D``, ``stash drop`` and
  ``clear``, ``filter-branch``, ``filter-repo``, ``reflog expire`` and
  ``delete``, ``update-ref -d`` and ``gc --prune``;
- the three the worktree workflow adds (SPEC WT5): ``git worktree remove`` with
  ``-f`` or ``--force``, which deletes uncommitted and untracked work; a force
  delete of a branch spelled other than ``-D`` (``--delete --force``, ``-d -f``,
  ``-df``), which is ``-D`` by another name; and ``git stash`` with any
  subcommand but ``list`` and ``show``, because every worktree of a repository
  shares one stash;
- publishing a package: ``rake release``, which reaches RubyGems through a
  subprocess no hook sees, and ``gem push``, ``yank``, ``owner``, ``signin``
  and ``signout``, which the deny list catches only as literal prefixes;
- recursive removal, which deletes trees no git history restores: ``rm`` with a
  recursive flag anywhere in the command, before or after the operand, and
  ``find`` with ``-delete`` or ``-exec rm``. Plain ``rm -f`` is left alone:
  ``make clean`` needs it and git restores what it drops;
- an HTTP upload, which sends file contents to a third party. The sending flags
  are read per tool because they collide: for ``curl`` ``-d``, ``-F``, ``-T``,
  ``--data*``, ``--form*``, ``--json``, ``--upload-file`` and ``-X``/
  ``--request`` with a writing method, including clustered short flags such as
  ``-fsSLd``; for ``wget`` ``--post-*``, ``--body-*`` and ``--method``, because
  wget's own ``-d``, ``-F`` and ``-T`` mean debug, force-html and timeout; for
  ``http``/``https`` (HTTPie) a leading method word. Downloads are untouched,
  and loopback is not egress.

Everything else falls through to the normal permission rules. The hook reads
the PreToolUse JSON on stdin and answers with a ``permissionDecision``.
"""

import json
import os
import re
import sys

SPEC = os.path.realpath(os.path.expanduser("~/.src/l5yth/spec"))

# Where a command can start: line start, after ; & | ( ` or $(, inside
# `sh -c '...'` or `eval '...'`, or after a wrapper such as env, xargs, nohup,
# time, timeout N, nice or a VAR=value assignment. Quoted text elsewhere, as in
# `grep "git push" file`, is not a command start.
START = (
    r"(?:^|[;&|(`\n]|\$\()\s*"
    r"(?:(?:sh|bash|zsh|dash|ksh)\s+(?:-[A-Za-z]+\s+)*-c\s+['\"]\s*|eval\s+['\"]?\s*)?"
    r"(?:(?:env|command|builtin|exec|nohup|time|sudo|doas|xargs|stdbuf|nice)"
    r"(?:\s+-\S+)*\s+|timeout\s+\S+\s+|\w+=\S*\s+)*"
)
# `git`, optionally as a path, then its global options (group 1).
GIT_CALL = (
    START + r"\\?[\"']?(?:[\w./~-]*/)?git[\"']?"
    r"((?:\s+(?:-C\s+\S+|-c\s+\S+"
    r"|--(?:git-dir|work-tree|namespace|super-prefix|exec-path|config-env)\s+\S+"
    r"|--[\w-]+(?:=\S+)?|-[A-Za-z]+))*)"
)
# The subcommand (group 2) and the rest of that command (group 3).
GIT = re.compile(GIT_CALL + r"\s+(commit|push|tag)\b([^;&|\n]*)")
# Destructive subcommands. `[^;&|\n]*` keeps a flag inside the same command.
DESTRUCTIVE = re.compile(
    GIT_CALL + r"\s+(?:reset\b[^;&|\n]*\s--hard\b|clean\b|restore\b"
    r"|checkout\b[^;&|\n]*\s(?:--|\.|-f|--force)(?=\s|$)"
    r"|switch\b[^;&|\n]*\s(?:-f|--force|--discard-changes)(?=\s|$)"
    r"|branch\b[^;&|\n]*\s-D\b|stash\s+(?:drop|clear)\b|filter-(?:branch|repo)\b"
    r"|reflog\s+(?:expire|delete)\b|update-ref\b[^;&|\n]*\s-d\b"
    r"|gc\b[^;&|\n]*\s--prune\b)"
)
# A flag ends where a word character or a hyphen does not follow, so `-f;` and
# `-f` at the end of the line count while `--forced` and `--format` do not.
FLAG_END = r"(?![\w-])"
# A forced `worktree remove` deletes the uncommitted and untracked work a plain
# one refuses to touch (SPEC WT5). The flag may follow the operand.
WORKTREE_FORCE = re.compile(
    GIT_CALL
    + r"\s+worktree\s+remove\b[^;&|\n]*\s(?:--force|-[a-zA-Z]*f[a-zA-Z]*)"
    + FLAG_END
)
# A delete flag and a force flag anywhere in one `git branch` call, in either
# order or clustered (`-df`, `-fd`), is `branch -D` by another name.
BRANCH_FORCE_DELETE = re.compile(
    GIT_CALL
    + r"\s+branch\b(?=[^;&|\n]*\s(?:--delete|-[a-zA-Z]*d[a-zA-Z]*)"
    + FLAG_END
    + r")(?=[^;&|\n]*\s(?:--force|-[a-zA-Z]*f[a-zA-Z]*)"
    + FLAG_END
    + r")"
)
# Every worktree of a repository shares one stash, so `pop` in one session can
# land another session's entry; `list` and `show` only read it. The lookahead
# takes spaces and tabs only: a newline must not pass for the subcommand.
STASH = re.compile(GIT_CALL + r"\s+stash\b(?![ \t]+(?:list|show)" + FLAG_END + r")")
# A command name as GIT_CALL writes it: optionally backslash-escaped, quoted or
# written as a path. The 2026-09-27 probe found `\git` and `"git"` escaping the
# git rules; any rule that omits this prefix is escaped the same way.
NAME = r"\\?[\"']?(?:[\w./~-]*/)?"
# The body of one command: a line continuation is part of it, `; & |` are not.
BODY = r"(?:[^;&|\n]|\\\n)*"
# A word ends where a shell metacharacter or a quote does, not only at
# whitespace: `rake release;` and `bash -c 'rake release'` are the same call.
END = r"(?![\w:-])"
# Publishing a package is irreversible and public. The deny list matches a
# literal prefix, so it misses ``bundle exec gem push``, a doubled space and a
# path; and ``rake release`` reaches RubyGems through a subprocess no hook sees.
PUBLISH = re.compile(
    START
    + r"(?:bundler?\s+exec\s+)?"
    + NAME
    + r"(?:rake[\"']?"
    + BODY
    + r"\s[\"']?release(?::\w+)?[\"']?"
    + END
    + r"|gem[\"']?\s+(?:push|yank|signin|signout|owner)\b)"
)
# Recursive removal deletes trees git cannot restore. The flag may follow the
# operand (GNU `rm` permutes), so the whole command body is searched. A bare
# ``-f`` is not matched: ``make clean`` needs it and git restores what it drops.
RECURSIVE_RM = re.compile(
    START
    + NAME
    + r"rm[\"']?"
    + BODY
    + r"\s(?:--recursive\b|-[a-zA-Z]*[rR][a-zA-Z]*(?=\s|$))"
)
# `find` reaches the same destruction without naming `rm` at a command start.
FIND_DELETE = re.compile(
    START + NAME + r"find\b" + BODY + r"\s(?:-delete\b|-exec\s+" + NAME + r"rm\b)"
)
# An HTTP upload publishes file contents to a third party. The sending flags are
# per tool, because they collide: ``-T``, ``-d`` and ``-F`` upload for curl but
# mean timeout, debug and force-html for wget. Downloads stay untouched.
CURL_SEND = (
    r"(?:-[a-zA-Z]*[dFT](?=[\s=]|$)|--(?:data(?:-[a-z]+)?|form(?:-string)?"
    r"|upload-file|json)\b|(?:-X|--request)\s*[\"']?(?:POST|PUT|PATCH|DELETE)\b)"
)
WGET_SEND = (
    r"(?:--(?:post|body)-(?:data|file)\b"
    r"|--method[=\s]\s*[\"']?(?:POST|PUT|PATCH|DELETE)\b)"
)
EGRESS = re.compile(
    START
    + NAME
    + r"(?:(?:curl|httpie)[\"']?"
    + BODY
    + r"\s"
    + CURL_SEND
    + r"|wget[\"']?"
    + BODY
    + r"\s"
    + WGET_SEND
    + r"|(?:https?|httpie)[\"']?\s+[\"']?(?:POST|PUT|PATCH|DELETE)\b)"
)
# Loopback is not egress: nothing leaves the machine, and ACCEPTANCE files in
# the spec tree probe local servers with `-X POST`.
LOOPBACK = re.compile(r"127\.0\.0\.1|\blocalhost\b|\[::1\]|0\.0\.0\.0")
DEPLOY = re.compile(
    START + r"(?:npm\s+(?:run|run-script)\s+deploy|(?:yarn|pnpm)\s+(?:run\s+)?deploy"
    r"|(?:npx\s+(?:-\S+\s+)*)?(?:[\w./~-]*/)?gh-pages)\b"
)


def target_repo(opts: str, cwd: str) -> str:
    """Return the real path of the repository a git call acts on.

    Args:
        opts: The global options between ``git`` and the subcommand.
        cwd: The working directory of the Bash call.

    Returns:
        The ``-C`` directory resolved against ``cwd``, or ``cwd`` itself.
    """
    path = cwd
    for directory in re.findall(r"-C\s+(\S+)", opts):
        directory = os.path.expanduser(directory.strip("'\""))
        path = os.path.join(path, directory)
    return os.path.realpath(path)


def deny(reason: str) -> None:
    """Print a PreToolUse deny decision and exit.

    Args:
        reason: Shown to the model and the user.
    """
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    sys.exit(0)


def main() -> None:
    """Read the tool call from stdin and deny it when a rule matches."""
    event = json.load(sys.stdin)
    if event.get("tool_name") != "Bash":
        return
    command = event.get("tool_input", {}).get("command", "")
    cwd = event.get("cwd") or os.getcwd()
    # `cd DIR && git ...`: the last cd before the git call sets its directory.
    for match in GIT.finditer(command):
        before = command[: match.start()]
        cds = re.findall(r"\bcd\s+([^\s;&|]+)", before)
        base = os.path.join(cwd, os.path.expanduser(cds[-1])) if cds else cwd
        repo = target_repo(match.group(1), base)
        sub, rest = match.group(2), match.group(3)
        if re.search(r"--git-dir|--work-tree|GIT_DIR=|GIT_WORK_TREE=", match.group(0)):
            deny(
                f"git {sub} with --git-dir, --work-tree, GIT_DIR or GIT_WORK_TREE is denied."
            )
        if sub == "tag":
            deny("git tag is denied: tags publish releases.")
        if sub == "push" and re.search(
            r"(?:^|\s)(?:-f|--force(?:-with-lease)?)\b|\s\+\S", rest
        ):
            deny("Forced pushes are denied everywhere.")
        if repo != SPEC and not repo.startswith(SPEC + os.sep):
            deny(
                f"git {sub} is denied outside {SPEC}: print a suggested commit message instead."
            )
    if DESTRUCTIVE.search(command):
        deny(
            "Destructive git commands are denied in every form: they discard work or history."
        )
    if WORKTREE_FORCE.search(command):
        deny(
            "git worktree remove --force is denied: it deletes uncommitted and untracked "
            "work. Check git status there and run it yourself."
        )
    if BRANCH_FORCE_DELETE.search(command):
        deny(
            "Force-deleting a branch is denied in every spelling: it is git branch -D."
        )
    if STASH.search(command):
        deny(
            "git stash is denied except list and show: every worktree of a repository "
            "shares one stash."
        )
    if PUBLISH.search(command):
        deny(
            "Publishing is denied: rake release, gem push, gem yank and gem owner "
            "change a public package irreversibly."
        )
    if RECURSIVE_RM.search(command) or FIND_DELETE.search(command):
        deny("Recursive delete is denied: it removes trees no git history restores.")
    if EGRESS.search(command) and not LOOPBACK.search(command):
        deny("HTTP upload is denied: it sends file contents to a third party.")
    if DEPLOY.search(command):
        deny("Deploy scripts publish the site and are denied. CI deploys main.")


if __name__ == "__main__":
    main()
