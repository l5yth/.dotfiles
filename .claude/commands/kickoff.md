# Claude Code Kickoff

I am building $ARGUMENTS.

## Phase 0: Spec (interview first)

Do not write code or prose yet. Interview me, one question at a time, until you have identified the real goal and the core decision this project is intended to drive. Bias toward small, compartmentalized specs over one monolith.

When the interview is done, write `SPEC.md` and list every key decision as a numbered item. I must confirm each item explicitly before you proceed. If I gloss over one, ask again. Re-verify these decisions at every later checkpoint so we do not drift from the original intent.

## Phase 1: Verification criteria (before building)

Define precise, testable criteria for a great result and write them to `ACCEPTANCE.md`. Where past work exists in this repo or my knowledge base, use it as the format to match and cite the file. Write the criteria so that a reviewer with zero context from this session can judge the output against `ACCEPTANCE.md` alone.

## Phase 2: Environment audit

Read `CLAUDE.md`, my knowledge base, my installed skills, and my hooks/guardrails. Report the top 5 gaps. For each gap give exactly three things:

1. The file
2. The problem
3. The exact fix (full text or diff, not a description)

Separately, flag every risky action (destructive git, file deletion, network egress, credentials, package publishing) that needs a deny or confirmation hook so I cannot bypass it by accident. Apply nothing until I approve.

## Phase 3: Build in buckets

Break the project into small agile buckets. One bucket at a time:

1. Present a plan for the bucket
2. Build it
3. Stop at a checkpoint: show the output, restate the Phase 0 decisions it touched
4. Wait for my sign-off before the next bucket

## Phase 4: Independent review

When all buckets are done, have a second, fresh instance review the result against `ACCEPTANCE.md` (subagent or `claude -p "Review this repo strictly against ACCEPTANCE.md. List every failure."`). Report failures verbatim, fix, re-run until clean. Only then declare the project finished.

