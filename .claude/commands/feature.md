I am adding $ARGUMENTS.

## Phase 0: Load the existing structure

Do not write code, prose, or questions yet. First read `CLAUDE.md`, `SPEC.md`, `ACCEPTANCE.md`, the installed skills, and the hooks/guardrails. Tell me back, in a few lines:

- Which existing SPEC decisions this feature is most likely to touch or strain
- Which existing acceptance criteria could regress
- Which modules or files the feature will integrate with

If you cannot find one of these files, stop and say so rather than guessing.

## Phase 1: Scoped spec (interview, then conflict check)

Interview me one question at a time to find the real goal of this feature and the core decision it drives. Keep it compartmentalized; resist scope creep into a second feature.

Then run a conflict check. For each existing SPEC decision the feature touches, state whether the feature is consistent with it, extends it, or contradicts it. A contradiction is a stop: name it and make me choose to amend the original decision or change the feature. Do not silently override anything.

When settled, append a `## Feature: <name>` section to `SPEC.md` with the new decisions numbered. I confirm each explicitly before you proceed.

## Phase 2: Acceptance (amend, do not replace)

Append the feature's acceptance criteria to `ACCEPTANCE.md` under the same heading. Write them so a reviewer with zero context from this session can judge the feature against the file alone, matching the format of the existing criteria.

Add one explicit regression line: the existing acceptance criteria must still pass after this feature lands. Name any that are at risk.

## Phase 3: Environment delta

Do not re-audit the whole project. Report only what this feature changes:

- Any new risky action it introduces (new network egress, new credentials, new destructive path, new dependency or publish step) and whether an existing hook already covers it
- For each gap, give the file, the problem, and the exact fix (full text or diff)

Apply nothing until I approve.

## Phase 4: Build in buckets

Break the feature into small agile buckets. One at a time:

1. Present a plan for the bucket
2. Build it
3. Checkpoint: show the output, restate which SPEC decisions (old and new) it touched
4. Wait for my sign-off before the next bucket

## Phase 5: Independent review

When the feature is done, have a fresh instance review against the amended `ACCEPTANCE.md` (subagent or `claude -p "Review this repo strictly against ACCEPTANCE.md, including the new feature section AND the prior criteria. List every failure."`). It must confirm both the new criteria and no regression in the old ones. Report failures verbatim, fix, re-run until clean. Only then is the feature done.

