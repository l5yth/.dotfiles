---
# SPDX-FileCopyrightText: 2026 l5y
# SPDX-License-Identifier: Unlicense
description: Ship a minimal fix fast (failing test, fix, handoff), then run the full bugfix workflow on it once the PR is up.
---
I am hotfixing $ARGUMENTS.

Specs for this repository live in the spec tree at `~/.src/l5yth/spec/$org/$repo/`, not at
the project root (global standards, §Specifications and agent instructions). Every
`CLAUDE.md`, `SPEC.md` and `ACCEPTANCE.md` named below means the copy there. Block A reads
them there and writes none of them; block B reads and writes them there, and creates the
entry if this repository has none. Fall back to the project's own files only if it keeps
them at its root instead.

Every stop below that waits for me (a question, a confirmation, an approval, a sign-off, a choice) reaches me through the question dialog (`AskUserQuestion`), one decision per question.

The goal is a minimal working fix, shipped as fast as possible. Block A (Phases 0 to 3) fixes and hands off without review. Block B (Phases 4 to 9) runs the full bugfix workflow on the shipped fix once the PR is up.

## Block A: Fix and close

## Phase 0: No spec writes

Do not write any `CLAUDE.md`, `SPEC.md` or `ACCEPTANCE.md`, and nothing else in the spec tree, before block B; the `pull --ff-only` before reading still runs. This is the one exception to the global rule to amend the entry as work proceeds: the amendments wait for block B, and until then the commit message and the PR carry the record.

Read `CLAUDE.md` and the guardrails in full, and only the `SPEC.md` and `ACCEPTANCE.md` sections that cover the code the fix touches. Phase 5 reads them in full.

## Phase 1: Failing test

Write a test that minimally reproduces the issue. It must fail now, against the unfixed code, for the right reason. Show me that it fails. If you cannot write a failing test, stop and tell me what you need; do not patch a bug you cannot trigger.

## Phase 2: Minimal fix

Make the smallest change that makes the Phase 1 test pass. No refactors, no unrelated cleanup. A fix at the symptom is allowed here; Phase 5 looks for the root cause.

Flag any new risky action the fix introduces and whether an existing deny rule covers it. Apply nothing destructive until I approve.

Done when the Phase 1 test passes and the existing tests still pass.

## Phase 3: Ship without review

Print the suggested commit message now, with the worktree path next to it (the clone's path when there is no worktree). Do not commit and do not push: I commit, push and open the PR. No review runs in block A.

## Block B: Full workflow after the fix

## Phase 4: Hard check-in

Ask me whether block A is done and the PR is up. Start block B only on a yes. Any other answer: stop and wait.

## Phase 5: Reproduce, root cause, classify

Read `CLAUDE.md`, `SPEC.md`, `ACCEPTANCE.md`, and the guardrails in full. Then reproduce the bug deterministically on the code before the Phase 2 fix, for example in a scratch clone at the PR's base commit. The Phase 1 test is the minimal reproduction; also give me the exact command, input, or steps that trigger the bug in use, and the observed versus expected behavior.

State which existing SPEC decision or acceptance criterion the buggy behavior violates. If none covers it, say so: the bug exists because the contract was silent there.

Diagnose to the root cause, not the symptom. State the cause in plain terms and show the evidence. Name the blast radius of the Phase 2 fix: every other caller, module, or behavior that touches the code it changed. Say whether the Phase 1 test and the Phase 2 fix reach the root cause.

Classify the bug, because the two kinds are fixed differently:

- Implementation defect: the code is wrong, the spec is right. Proceed.
- Spec defect: the code does what `SPEC.md` says, but the spec is wrong or ambiguous. This is a stop. Amending the contract is my decision, not yours. Present the options and let me choose before any code changes.

I confirm the diagnosis explicitly before you touch code.

## Phase 6: Regression guard

If Phase 5 shows that the Phase 1 test or the Phase 2 fix falls short of the root cause:

1. Write the check that captures the root cause: a test, an assertion, or an acceptance criterion. It must fail now, against the hotfixed code, for the right reason. Show me that it fails.
2. Make the smallest root-cause fix under the Phase 2 rules, and name its blast radius.

Either way, append the regression line to `ACCEPTANCE.md`, matching the existing format, so this exact defect is covered from now on and cannot quietly return. It names the Phase 1 test, and the check above if there is one.

## Phase 7: Prove no regression

Two conditions, both required:

1. The regression check passes: the Phase 1 test, and the Phase 6 check if there is one.
2. Every prior acceptance criterion still passes. Run them. The point of a bugfix is that the system is strictly better afterward, never a trade of one defect for another.

## Phase 8: Commit message

If block B changed the repository, print the suggested commit message now, before the review, with the worktree path next to it (the clone's path when there is no worktree). Do not commit and do not push. The message covers block B's changes, so they can go up on the PR and Phase 9 can run against them in parallel. If block B changed only the spec tree, say so and print no message.

If the review then finds failures, fix them and print an amended message.

## Phase 9: Independent review

Have a fresh instance review against the amended spec-tree `ACCEPTANCE.md`. A failure is a criterion the change breaks or a claim it makes that is false; a finding beyond what the change claims is a low finding. Report failures verbatim, fix, and re-run. Each round's verdict comes to me before the next round starts. After two failing rounds, stop and give me the failures with three options: narrow the claim, ship as is, or continue. A clean round, or my choice, closes the bug. Use a subagent, or this read-only command (a fresh instance does not see the spec-tree note above, so the path is explicit):

    claude -p "Review this repository strictly against ~/.src/l5yth/spec/$org/$repo/ACCEPTANCE.md, including the new regression line AND all prior criteria. Confirm the bug is fixed and nothing else regressed. List every failure." \
      --permission-mode default \
      --allowedTools "Read" "Grep" "Glob" "Bash(git ls-files:*)" "Bash(git branch:*)" "Bash(grep:*)" "Bash(wc:*)" "Bash(ls:*)" "Bash(test:*)" "Bash(npm run:*)" "Bash(npm test:*)" "Bash(node --test:*)" \
      --disallowedTools "Edit" "Write" "NotebookEdit"

