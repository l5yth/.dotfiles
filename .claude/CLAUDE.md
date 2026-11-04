# l5y standards (all projects)

> These are complementary defaults for every project. A project's own `CLAUDE.md`
> overrides one of these rules only on a direct conflict; where there's no conflict,
> both apply.

## Licensing (REUSE-compliant)
- Source and header files: full license header at top of file.
- Every other file: 2-line SPDX header:
    SPDX-FileCopyrightText: <year> <holder>
    SPDX-License-Identifier: <ID>
- Use each file's native comment syntax.

## Tests
- Unit-test line coverage floor: 100%. The floor, not the target.
- Smoke, integration, and end-to-end tests sit on top of that baseline.
- No new code lands without matching unit tests.

## Documentation
- 100% API-doc coverage in the language standard: rustdoc, Zig doc comments,
  Doxygen (C/C++), pdoc (Python), RDoc (Ruby), JSDoc (JS), dartdoc (Dart).
- JS: Biome has no rule that requires JSDoc. Gate coverage with `jsdoc -X`
  (zero undocumented) plus `tsc --noEmit --checkJs --strict`.
- Docs complete enough to generate full API documentation from source.
- Inline comments wherever the logic is not self-evident.

### User-facing documentation (README, guides, tutorials, CLI help, changelogs)
- No em-dashes.
- No emojis.
- No prose and no reasoning. Steps, facts, and commands only.
- Concise: do X to get Y. Not why, not how it works.
- Why and how go in SPEC documents or API documentation instead.

## Specifications and agent instructions
- A repository's instructions and specifications live in the spec repo, not in the
  repository itself:
    ~/.src/l5yth/spec/$org/$repo/    (or $user in place of $org)
- A task reads and amends its entry in its own spec worktree, a checkout of the whole spec
  repo that the worktree hook makes beside the task worktree;
  `python3 ~/.claude/hooks/worktree.py spec` prints its path and makes a missing one. In a
  task, an entry path `~/.src/l5yth/spec/<org>/<repo>/...` named in a command, a skill or a
  criterion means the same path in that worktree.
- Pull before reading: `git -C ~/.src/l5yth/spec pull --ff-only`, and in a task
  `git -C <spec worktree> pull --ff-only origin main`. The tree is shared across machines,
  so a stale copy means amending a spec that has already moved on.
- Read that directory before starting work. Treat a `CLAUDE.md`, `SPEC.md`, or
  `ACCEPTANCE.md` found there as if it sat at the project root.
- No entry for the repository: fall back to the project's own files.
- Amend the entry as work proceeds. Decisions go in `SPEC.md`, verification criteria in
  `ACCEPTANCE.md`, standing guidance in `CLAUDE.md`. Do not leave them in the conversation.

### Questions to the user
- Ask every question, confirmation, approval, sign-off and choice
  through the question dialog (`AskUserQuestion`), one decision per question.
- Each question reads alone: it names what it decides and the items it covers, and puts
  the recommended option first. A report or diff it needs sits in the message before it
  or in an option's preview.
- A subagent's question reaches the user the same way: the main session asks it in the
  dialog.

## Structure
- Files: 500 to 1000 LOC. Refactor when a file runs well past 1000.
- Modular from the first commit, not as later cleanup.

## Formatting and lint
- Run formatter and linter before work is done:
    Rust: rustfmt + clippy.  Zig: zig fmt.  C/C++: clang-format + clang-tidy.
    Python: black.  Ruby: rufo.  JavaScript: Biome (format + lint).
- Markdown and JSON: the project's own formatter if it has one (for example Prettier);
  none otherwise. Never reformat a file whose exact bytes a SPEC pins.
- Language not listed above: ask before choosing the tool.

## Git workflow
- Before starting, `git fetch` the project repository. A clean `main` that is only behind
  `origin/main` fast-forwards (`git merge --ff-only origin/main`); report it. Diverged or
  dirty: stop and ask.
- Create feature branches. Name them l5y-$area-$scope.
- Never push. Never open pull requests.
- Never commit. On finishing a unit of work, print a suggested commit message unprompted,
  with the worktree path next to it (the clone's path when there is no worktree).
- One exception, in `~/.src/l5yth/spec` and no other repository: at the end of a unit of
  work, commit the spec amendments in the spec worktree of the task and push them to
  `main`. No feature branch, no mid-task pushes.
- Land them in this order, with the spec worktree's absolute path as `<w>`:
  `git -C <w> pull --ff-only origin main`, which carries the edits onto the current `main`
  or refuses and changes nothing; `git -C <w> add -A`; `git -C <w> commit -m "<message>"`;
  `git -C <w> merge origin/main`; `git -C <w> push origin HEAD:main`. A rejected push:
  `git -C <w> fetch origin`, merge and push again. A merge conflict: keep the decisions of
  both sides, and ask only when they contradict.

### Worktrees
- One task, one branch, one worktree, one session: start it from the primary clone
  `~/.src/$org/$repo` with `claude -w <branch>`. The worktree hook puts it at
  `~/.src/.wt/$org/$repo/<branch>`, branched from the remote default branch, and the spec
  worktree of the task at `~/.src/.spec/$org/$repo/<branch>`, detached at the spec repo's
  `main`.
- The fetch and fast-forward rule above runs against the primary clone, not the worktree.
  Its state is reported and never blocks a worktree session. Do no task work in the
  primary clone.
- Pick the spec entry `$org/$repo` from the primary clone's path below `~/.src`,
  never from the current directory.
- Inside a worktree, a criterion that names `~/.src/$org/$repo` means the worktree root.
- Inside a worktree, send plain, separate commands, and write files and scripts with the
  Write tool: the isolation guard refuses heredocs, loops and `cd` chains. Give `git -C` an
  absolute path: the guard refuses `~` there.
- Reviewers run inside the task worktree, never with `isolation: worktree`: those
  worktrees start from the remote default branch and hold none of the uncommitted work.
- No `git stash`: every worktree of a repository shares one stash.
- Finished worktrees: `python3 ~/.claude/hooks/worktree.py sweep` removes each one that
  is clean and fully pushed, and keeps the rest with the reason; a spec worktree goes only
  after its task worktree.
