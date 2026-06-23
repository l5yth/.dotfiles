# SPEC — Fold `.claude` config into `.dotfiles`

**Goal.** Manage the personal `~/.claude` configuration (commands, skills, agents,
hooks) as part of the existing `.dotfiles` repo, so it deploys and updates across
machines through the same `install.sh` flow as everything else. The stash today is a
single file (`commands/kickoff.md`); this project builds the *management system*, not
new content.

**Core decision driven.** How `.claude` config is version-controlled and deployed —
the repo boundary, the direction truth flows, and the ignore/secrets policy that keeps
runtime state and credentials out of git.

## Context

- `.dotfiles` (`git@github.com:l5yth/.dotfiles.git`) is a `$HOME` overlay deployed by
  `install.sh`: `rsync --backup` from repo → `$HOME`, timestamped conflict backups,
  `.bin/dotfiles-resolve` to clean up. See `CLAUDE.md` §Layout, §Install flow.
- Today `.claude/` is in the `install.sh` exclude list **and** gitignored — deliberately
  carved out (`CLAUDE.md` §Layout lists it under "must NOT land in `$HOME`"). This
  project reverses that, because `.claude/` maps directly onto `~/.claude/`.
- Live `~/.claude/` mixes curated config (`commands/kickoff.md`) with runtime state
  (`projects/`, `sessions/`, `shell-snapshots/`, `cache/`, `file-history/`, `backups/`,
  `plugins/`, …) and secrets (`.credentials.json`, `history.jsonl`). **Only the curated
  part may ever be tracked.**

## Scope

- **In:** gitignore policy, `install.sh` deploy wiring, doc sync (`CLAUDE.md` / README),
  a secrets guard, and seeding the one existing command.
- **Out:** authoring new agents/skills/commands; symlink/stow approaches; changing the
  bootstrap beyond `install.sh` + docs; vendoring `plugins/` bodies.

## Key decisions

All ten decisions below were confirmed in the kickoff interview (2026-06-12). Per
`CLAUDE.md` discipline, re-verify them at each checkpoint so the build doesn't drift.

1. **[confirmed] Integration model.** Track a curated subset of `.claude` inside
   `.dotfiles/.claude/`; reverse the current `.claude/` exclusion so it deploys to
   `~/.claude/`.
2. **[confirmed] Truth flow.** Canonical copy lives in `.dotfiles/.claude/`. You edit
   there, commit, and `install.sh` rsyncs into `~/.claude/` (additive, with backups) —
   exactly like `.zshrc`. Do **not** edit live `~/.claude/` for tracked items; install
   would overwrite them (backups protect you if you forget).
3. **[confirmed] Work + docs location.** All work happens in `.dotfiles`. `SPEC.md` /
   `ACCEPTANCE.md` live at the repo root and are excluded from deploy. The now-redundant
   `~/.src/l5yth/.claude` repo will be removed (only with your explicit confirmation).
4. **[confirmed] Tracked set.** `.claude/commands/`, `.claude/skills/`, `.claude/agents/`,
   `.claude/hooks/`, `.claude/CLAUDE.md`. Directories are created as they gain content;
   only `commands/kickoff.md` exists today.
5. **[confirmed] Ignore policy = default-deny whitelist.** `.gitignore` ignores
   *everything* under `.claude/` except the tracked set (D4) plus `settings.json` (D6).
   This guarantees `.credentials.json`, `history.jsonl`, `projects/`, `sessions/`,
   `shell-snapshots/`, `cache/`, `plugins/`, `backups/`, `file-history/`, `debug/`,
   `session-env/`, `tasks/`, `plans/`, `paste-cache/`, `mcp-needs-auth-cache.json` can
   never be committed — even if they appear in the working tree.
6. **[confirmed] settings split.** Track a shared `.claude/settings.json` (theme, enabled
   plugins). Keep `.claude/settings.local.json` gitignored **and** rsync-excluded — it
   holds machine-local permission allowlists with absolute `/home/user/...` paths.
   *Alternative:* don't track `settings.json` at all and manage it per machine.
7. **[confirmed] `install.sh` changes.** Drop `--exclude='.claude/'`; add
   `--exclude='SPEC.md'`, `--exclude='ACCEPTANCE.md'`,
   `--exclude='.claude/settings.local.json'`, plus defense-in-depth excludes for
   `.claude/` runtime/state paths. Keep rsync additive (no `--delete`) so live state in
   `~/.claude/` survives. Comment the *why* per `CLAUDE.md` §Inline documentation.
8. **[confirmed] Doc sync.** Update `CLAUDE.md`: remove `.claude/` from the "must NOT land
   in `$HOME`" list (§Layout) and add a short section describing the `.claude` overlay +
   the `settings.local`/secrets invariant. README: minimal or no change — avoid adding
   command blocks that the CI README-walk (`.github/workflows/ci.yml`) would have to
   mirror.
9. **[confirmed] Secrets guard.** Add a `.dotfiles` pre-commit guard that blocks
   committing Claude secrets/state (`.credentials.json`, `*credential*`, `history.jsonl`,
   `.claude/projects/`, `.claude/sessions/`, …) — belt-and-suspenders beyond the
   whitelist gitignore. Detailed and applied in Phase 2 after your approval.
10. **[confirmed] Seed + scope boundary.** Copy `~/.claude/commands/kickoff.md` →
    `.dotfiles/.claude/commands/kickoff.md` as the first tracked content. No new
    agents/skills/commands are authored in this project.
    *(Update 2026-06-23: this "no new commands" boundary governed the fold-in project
    only. `bugfix.md` and `feature.md` were later added as deliberate curated content in
    `6f5cd0f`; the tracked-command set is allowed to grow. ACCEPTANCE E2 tracks the
    current set rather than the kickoff-only snapshot.)*

## Non-goals

Authoring stash content; symlink/stow deployment; bootstrap changes beyond `install.sh`
+ docs; tracking `plugins/` bodies (only their enablement in `settings.json`).

---

## Feature: Persist max effort level

**Goal.** Make Claude Code default to `max` reasoning effort on every session and every
installed machine, persisted through the dotfiles deploy — instead of re-setting it by
hand with `/effort` each session.

**Core decision driven.** *How* a default effort level is persisted, given that the
supported persistent key (`effortLevel`) accepts only `low|medium|high|xhigh` and
silently downgrades `max` → `xhigh`. The only mechanism that persists literal `max` is
the `CLAUDE_CODE_EFFORT_LEVEL` environment variable.

All six decisions confirmed 2026-06-23. Per the discipline in §Key decisions above,
re-verify them at each checkpoint so the build doesn't drift.

1. **[confirmed] Mechanism.** Persist effort by setting `CLAUDE_CODE_EFFORT_LEVEL=max`
   in an `"env"` block in the tracked shared `.claude/settings.json`. Do **not** use the
   `effortLevel` key — it rejects `max` and downgrades to `xhigh`. *(Doc-verified against
   the Claude Code settings reference; re-verify against the installed CLI at build.)*
2. **[confirmed] Scope.** Shared across all machines: the env var lives in the tracked
   `settings.json`, not `settings.local.json`. Consequence, accepted as a trade-off: every
   session on every installed machine runs at max effort with no cap on token spend.
3. **[confirmed] Extends D6 (settings split).** The shared `settings.json` may now carry
   an `"env"` block, not only `theme` + `enabledPlugins`. Same principle as D6 — shared,
   non-secret, non-machine-specific config is tracked; machine-local/secret stays in the
   rsync-excluded, gitignored `settings.local.json`. D6's `settings.local.json` policy is
   unchanged.
4. **[confirmed] Extends D8 (doc sync) / §Inline documentation.** Because `settings.json`
   is strict JSON and cannot carry inline comments, the non-obvious rationale — *why the
   env var and not `effortLevel`* — is documented in `CLAUDE.md` §"Claude Code config"
   instead of inline. This is the one config line whose "why" the repo's inline-comment
   discipline cannot host; `CLAUDE.md` carries it.
5. **[confirmed] Reaffirms D2 (truth flow).** The `/effort` command and the CLI write
   effort changes to the *live* `~/.claude/settings.json`; per D2 the repo copy is
   canonical and `install.sh` overwrites the live copy on the next run (backups catch you).
   With repo-side env-max, no live `/effort` is needed to persist, so the canonical copy
   stays authoritative.
6. **[confirmed] Reaffirms D5/D7/D9 (no deploy/ignore/guard change).** `settings.json` is
   already tracked, whitelisted, and deployed, so this feature touches **no** other
   machinery: `install.sh`, `.gitignore`, and `.githooks/pre-commit` are unchanged.
