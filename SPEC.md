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

## Non-goals

Authoring stash content; symlink/stow deployment; bootstrap changes beyond `install.sh`
+ docs; tracking `plugins/` bodies (only their enablement in `settings.json`).
