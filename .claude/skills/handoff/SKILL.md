---
# SPDX-FileCopyrightText: 2026 Matt Pocock
# SPDX-FileCopyrightText: 2026 l5y
# SPDX-License-Identifier: MIT
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
---

Specs for this repository live in the spec tree at `~/.src/l5yth/spec/$org/$repo/`, not at the project root. Every `CLAUDE.md`, `SPEC.md` and `ACCEPTANCE.md` named below means the copy there: read it there, write it there, and create the entry if this repository has none. Fall back to the project's own files only if it keeps them at its root instead.

Write a handoff document summarising the current conversation so a fresh agent can continue the work.

1. Record first. Every decision still open in the conversation goes into the entry before the handoff is written: decisions in `SPEC.md`, verification criteria in `ACCEPTANCE.md`, standing guidance in `CLAUDE.md`. The handoff then points at the entry instead of restating it.
2. Save the document to the session scratchpad directory when the harness names one, else `$TMPDIR`, else `/tmp` - not the current workspace. Print its absolute path.
3. State where the work stands: the worktree path, the branch, what is uncommitted, and the suggested commit message if one was printed.
4. Include a "Suggested skills" section in the document, naming the skills the next session should use: the Skill tool for a model-invoked skill, the slash command the user types for a user-invoked one.

Do not duplicate content already captured in other artifacts (the spec-tree entry, plans, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.
