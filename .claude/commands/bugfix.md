I am fixing $ARGUMENTS.

## Phase 0: Reproduce and locate

Do not fix anything yet. First read `CLAUDE.md`, `SPEC.md`, `ACCEPTANCE.md`, and the guardrails. Then reproduce the bug deterministically: give me the exact command, input, or steps that trigger it, and the observed versus expected behavior. If you cannot reproduce it, stop and tell me what you need; do not patch a bug you cannot trigger.

State which existing SPEC decision or acceptance criterion the buggy behavior violates. If none covers it, say so: the bug exists because the contract was silent there.

## Phase 1: Root cause (diagnose, then classify)

Diagnose to the root cause, not the symptom. State the cause in plain terms and show the evidence. Resist patching the surface; if you are tempted to add a guard around a symptom, that is the signal you have not found the cause.

Classify the bug, because the two kinds are fixed differently:

- Implementation defect: the code is wrong, the spec is right. Proceed.
- Spec defect: the code does what `SPEC.md` says, but the spec is wrong or ambiguous. This is a stop. Amending the contract is my decision, not yours. Present the options and let me choose before any code changes.

I confirm the diagnosis explicitly before you touch code.

## Phase 2: Capture the bug first (regression guard)

Before writing the fix, write the check that captures the bug: a test, an assertion, or an acceptance criterion. It must fail now, against the unfixed code, for the right reason. Show me that it fails.

Append this as a regression line to `ACCEPTANCE.md`, matching the existing format, so this exact defect is covered from now on and cannot quietly return.

## Phase 3: Minimal fix

Make the smallest change that addresses the root cause. No opportunistic refactors, no unrelated cleanup; those drift the change and widen the regression surface.

Name the blast radius: every other caller, module, or behavior that touches the code you are changing. Flag any new risky action the fix introduces and whether an existing hook covers it. Apply nothing destructive until I approve.

## Phase 4: Prove no regression

Two conditions, both required:

1. The check from Phase 2 now passes.
2. Every prior acceptance criterion still passes. Run them. The point of a bugfix is that the system is strictly better afterward, never a trade of one defect for another.

Then have a fresh instance review against the amended `ACCEPTANCE.md` (subagent or `claude -p "Review this repo strictly against ACCEPTANCE.md, including the new regression line AND all prior criteria. Confirm the bug is fixed and nothing else regressed. List every failure."`). Report failures verbatim, fix, re-run until clean. Only then is the bug closed.

