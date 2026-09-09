<!--
SPDX-FileCopyrightText: 2026 l5y
SPDX-License-Identifier: Unlicense
-->

# Vendored: i-have-adhd

Upstream: https://github.com/ayghri/i-have-adhd
Pinned commit: `58494af57962b2d7a996b4d419474380a299af5e` (2026-09-01)
Plugin version: 0.2.0
Upstream licence: MIT, Copyright (c) 2026 Ayoub Ghriss (see `LICENSE`)
Vendored: 2026-09-08

## Files from upstream

Byte-identical. Do not edit.

| Vendored path | Upstream path |
| --- | --- |
| `.claude-plugin/plugin.json` | `.claude-plugin/plugin.json` |
| `hooks/hooks.json` | `hooks/hooks.json` |
| `hooks/always-on.mjs` | `hooks/always-on.mjs` |
| `skills/i-have-adhd/SKILL.md` | `skills/i-have-adhd/SKILL.md` |
| `LICENSE` | `LICENSE` |

## Files added here

| Path | Purpose |
| --- | --- |
| `VENDOR.md` | This file. |
| `.i-have-adhd-always` | Empty always-on flag. Read via the `CLAUDE_CONFIG_DIR` redirect in `.claude/settings.json`. |

## Not vendored

Other-runtime manifests (Gemini, Qwen, Kimi, OpenCode, Pi, Codex, Cursor), translations,
`evals/`, `tests/`, `scripts/`.

## Check for drift

```bash
U=$(mktemp -d); git clone -q https://github.com/ayghri/i-have-adhd "$U"
git -C "$U" checkout -q 58494af57962b2d7a996b4d419474380a299af5e
V=~/.src/l5yth/.dotfiles/.claude/skills/i-have-adhd
diff "$U/.claude-plugin/plugin.json"  "$V/.claude-plugin/plugin.json"
diff "$U/hooks/hooks.json"            "$V/hooks/hooks.json"
diff "$U/hooks/always-on.mjs"         "$V/hooks/always-on.mjs"
diff "$U/skills/i-have-adhd/SKILL.md" "$V/skills/i-have-adhd/SKILL.md"
diff "$U/LICENSE"                     "$V/LICENSE"
```

No output means no drift.

## Refresh to a newer upstream

Read the diff before copying. `hooks/always-on.mjs` runs on every session start with your
privileges, and `permissions.defaultMode=bypassPermissions` means nothing prompts you.

```bash
U=$(mktemp -d); git clone -q https://github.com/ayghri/i-have-adhd "$U"
git -C "$U" diff 58494af57962b2d7a996b4d419474380a299af5e..<new-pin> -- \
  .claude-plugin/plugin.json hooks/hooks.json hooks/always-on.mjs \
  skills/i-have-adhd/SKILL.md LICENSE
```

Then, for each of the five files: `cp "$U/<upstream path>" "$V/<vendored path>"`, update
the pin, version and date above, and run the drift check.

Verify the result:

```bash
CFG=$(mktemp -d); mkdir -p "$CFG/skills"
cp -R ~/.src/l5yth/.dotfiles/.claude/skills/i-have-adhd "$CFG/skills/"
CLAUDE_CONFIG_DIR="$CFG" claude plugin list
CLAUDE_CONFIG_DIR="$CFG" claude plugin validate "$CFG/skills/i-have-adhd"
```

Expect `Status: ✔ loaded` and `✔ Validation passed`.

Decision record: `SPEC.md` / `ACCEPTANCE.md` §Feature: i-have-adhd always-on output shaping,
in `~/.src/l5yth/spec/l5yth/.dotfiles/`.
