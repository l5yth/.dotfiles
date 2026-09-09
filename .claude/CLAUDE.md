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
- Pull before reading: `git -C ~/.src/l5yth/spec pull --ff-only`. The tree is shared across
  machines, so a stale clone means amending a spec that has already moved on, and the push
  at the end of the work then lands on a base that no longer exists.
- Read that directory before starting work. Treat a `CLAUDE.md`, `SPEC.md`, or
  `ACCEPTANCE.md` found there as if it sat at the project root.
- No entry for the repository: fall back to the project's own files.
- Amend the entry as work proceeds. Decisions go in `SPEC.md`, verification criteria in
  `ACCEPTANCE.md`, standing guidance in `CLAUDE.md`. Do not leave them in the conversation.

## Structure
- Files: 500 to 1000 LOC. Refactor when a file runs well past 1000.
- Modular from the first commit, not as later cleanup.

## Formatting and lint
- Run formatter and linter before work is done:
    Rust: rustfmt + clippy.  Zig: zig fmt.  C/C++: clang-format + clang-tidy.
    Python: black.  Ruby: rufo.
- Language not listed above: ask before choosing the tool.

## Git workflow
- Create feature branches. Name them l5y-$area-$scope.
- Never push. Never open pull requests.
- Never commit. On finishing a unit of work, print a suggested commit message unprompted.
- One exception, in `~/.src/l5yth/spec` and no other repository: `pull --ff-only` before
  starting (see §Specifications), then at the end of a unit of work commit the spec
  amendments and push them to `main`. Pull `--ff-only` again immediately before that push —
  the remote can move while the work is in progress. No feature branch, no mid-task pushes.
