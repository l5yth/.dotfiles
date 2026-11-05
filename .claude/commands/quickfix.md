---
# SPDX-FileCopyrightText: 2026 l5y
# SPDX-License-Identifier: Unlicense
description: Ship a small fix, such as a nit or a typo, fast (failing test, fix, handoff), with no spec record and no review.
---
I am quickfixing $ARGUMENTS.

Specs for this repository live in the spec tree at `~/.src/l5yth/spec/$org/$repo/`, not at
the project root (global standards, §Specifications and agent instructions). Every
`CLAUDE.md`, `SPEC.md` and `ACCEPTANCE.md` named below means the copy there. This command
reads them there, in this task's spec worktree (`python3 ~/.claude/hooks/worktree.py spec`
prints its path), writes none of them, and creates no entry if this repository has none.
Fall back to the project's own files only if it keeps them at its root instead.

Every stop below that waits for me (a question, a confirmation, an approval, a sign-off, a choice) reaches me through the question dialog (`AskUserQuestion`), one decision per question.

The goal is a small fix, such as a nit or a typo, shipped fast without the full workflow. Phases 0 to 3 fix it and hand it off without review; no spec record and no review follow. If the fix turns out bigger, at any phase, stop and name `/hotfix` or `/bugfix` (Phase 2 sets the bar).

## Phase 0: No spec writes

Do not write any `CLAUDE.md`, `SPEC.md` or `ACCEPTANCE.md`, and nothing else in the spec tree; the `pull --ff-only` before reading still runs. This command makes one exception to the global rule to amend the entry as work proceeds: a quickfix gets no amendment, now or later, and the commit message and the PR carry the record.

Read `CLAUDE.md` and the guardrails in full, and only the `SPEC.md` and `ACCEPTANCE.md` sections that cover the code the fix touches.

## Phase 1: Failing test

Write a test that minimally reproduces the issue. It must fail now, against the unfixed code, for the right reason. Show me that it fails. If you cannot write a failing test, stop and tell me what you need; do not patch a bug you cannot trigger.

The test lands with the fix, in the repository's test suite. If the repository has none, the test is a check command, and the commit message carries it.

## Phase 2: Minimal fix

Make the smallest change that makes the Phase 1 test pass. No refactors, no unrelated cleanup.

Name the blast radius: every other caller, module, or behavior that touches the code you are changing. Flag any new risky action the fix introduces and whether an existing deny rule covers it. Apply nothing destructive until I approve.

If the fix changes behavior beyond the reported issue, or breaks an acceptance criterion or contradicts a SPEC decision of the sections Phase 0 read, stop and name `/hotfix` or `/bugfix` instead of handing off: this command cannot amend them.

Done when the Phase 1 test passes, the existing tests still pass, and the acceptance criteria of the sections Phase 0 read still pass.

## Phase 3: Ship without review

Print the suggested commit message now, with the worktree path next to it (the clone's path when there is no worktree). The message is the only record: it names the issue, the fix, and the Phase 1 test or its check command. Do not commit and do not push: I commit, push and open the PR. No review runs; this closes the quickfix.
