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
  ``delete``, ``update-ref -d`` and ``gc --prune``.

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
    if DEPLOY.search(command):
        deny("Deploy scripts publish the site and are denied. CI deploys main.")


if __name__ == "__main__":
    main()
