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
