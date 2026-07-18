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

---

## Feature: Persist global Claude standards (`.claude/CLAUDE.md`)

**Goal.** Persist a personal, machine-wide set of engineering standards as Claude Code's
global user instructions (`~/.claude/CLAUDE.md`), deployed through the dotfiles flow so
every machine and every project picks them up — instead of re-stating the same licensing,
testing, documentation, structure, formatting, and git-workflow rules per project.

**Core decision driven.** *Where* the standards live and *how universally* they apply: a
single tracked `.claude/CLAUDE.md` that `install.sh` deploys to `~/.claude/CLAUDE.md`,
applied to every project as a complementary default layered under each project's own
`CLAUDE.md`.

All six decisions below — referenced as GS1–GS6 in `ACCEPTANCE.md` — were confirmed
2026-06-29. Per the discipline in §Key decisions above, re-verify them at each checkpoint
so the build doesn't drift.

1. **[confirmed] GS1 Location / mechanism.** Track `.claude/CLAUDE.md`; `install.sh`
   deploys it to `~/.claude/CLAUDE.md`, Claude Code's user-level (global) instructions
   loaded for every project on the machine alongside each project's own `./CLAUDE.md`.
   This realizes the `.claude/CLAUDE.md` slot reserved in D4 but left empty since the
   fold-in. *Extends D1/D4; uses the existing overlay + deploy machinery unchanged except
   for GS4.*

2. **[confirmed] GS2 Precedence model.** The standards are complementary defaults that
   apply to every project at once. A project's own `CLAUDE.md` overrides one of these
   rules **only on a direct conflict** (e.g. this repo's "There is no test suite" vs. the
   global "100% line-coverage floor"); with no conflict, both files' rules apply together.
   This is Claude Code's native `CLAUDE.md` layering — the feature relies on it and states
   it in a short preamble at the top of the file. *Adds no new machinery.*

3. **[confirmed] GS3 Content fidelity.** Store the standards **verbatim** — the exact
   section headings and wording supplied — prepended with the one-/two-line precedence
   preamble from GS2. Keep the SPDX `<year>`/`<holder>`/`<ID>` placeholders unresolved: a
   global file spans projects with different licenses and years, so each project fills them
   in, not this file. Fix only obvious typos; no rewording or restructuring.

4. **[confirmed] GS4 Extends D7 (install.sh).** `install.sh` excludes the repo-root project
   file with an unanchored `--exclude='CLAUDE.md'`, which rsync matches at any depth and
   which therefore would also block `.claude/CLAUDE.md` from deploying (verified empirically
   2026-06-29: with the unanchored rule the overlay file does not land; with
   `--exclude='/CLAUDE.md'` it does, and the root file stays excluded). Anchor that one line
   to `--exclude='/CLAUDE.md'`. The sibling root-file excludes (`LICENSE`, `README.md`,
   `SPEC.md`, `ACCEPTANCE.md`, `install.sh`) are left unanchored — no `.claude/` counterpart
   exists to collide with them today. *Amends D7's concrete exclude list; preserves both of
   D7's intents (exclude the root project file; deploy the tracked `.claude/` set).*

5. **[confirmed] GS5 Extends D8 (doc sync).** Update repo-root `CLAUDE.md` §"Claude Code
   config": note that `.claude/CLAUDE.md` now ships as global user instructions, and record
   the non-obvious rationale — once a `.claude/CLAUDE.md` exists, the root exclude must stay
   anchored (`/CLAUDE.md`) or the overlay file silently stops deploying. Per the §Inline
   documentation discipline this "why" lives in `CLAUDE.md` because a one-word rsync pattern
   can't host the explanation. *Extends D8.*

6. **[confirmed] GS6 Reaffirms D5/D9/E2 (no ignore/guard/scope change).** `.gitignore`
   already whitelists `!/.claude/CLAUDE.md` (D5), so no ignore change. The pre-commit
   secrets guard (D9) is unaffected — a global instructions file is curated config, not
   credentials/state. `.claude/CLAUDE.md` is not a command/agent/skill, so the E2
   command-set boundary (`bugfix`/`feature`/`kickoff`, no agents/skills) is untouched. No
   change to `.gitignore`, `.githooks/pre-commit`, or the tracked command set.

---

## Feature: Replace fasd with zoxide

**Goal.** Replace the abandoned `fasd` directory-frecency tool with the actively maintained
`zoxide` (Rust) as the shell's jump command, deployed through the same dotfiles flow, while
preserving the existing `j` muscle memory — instead of carrying a dead dependency and a
95-line checked-in init cache (`.fasd-init-zsh`).

**Core decision driven.** The *usage surface* of the replacement: which command name(s) the
jump verb is exposed under, whether the default action is a straight jump or an interactive
picker, and what happens to fasd's file-frecency commands that zoxide has no equivalent for.

All six decisions below — referenced as ZX1–ZX6 in `ACCEPTANCE.md` — were confirmed
2026-07-18. Per the discipline in §Key decisions above, re-verify them at each checkpoint so
the build doesn't drift.

1. **[confirmed] ZX1 Mechanism.** Replace `fasd` with `zoxide` as the frecency directory
   jumper. `zoxide` is in Arch's official `extra` repo, so it stays in the plain `pacman -S`
   list — no AUR/`pikaur`. The package name is swapped in **both** the README `pacman` block
   (`README.md`) and the mirrored CI package list (`.github/workflows/ci.yml`) in the same
   commit, per the README↔CI coupling (`CLAUDE.md` §"README ↔ CI coupling"). *New domain
   (shell tooling); no prior SPEC decision governs it.*

2. **[confirmed] ZX2 Command surface (`--cmd j`).** Initialize with
   `zoxide init zsh --cmd j`, exposing `j <query>` (jump to the top frecency match,
   non-interactive) and `ji <query>` (fzf picker among matches). This preserves the existing
   `alias j` muscle memory; jumping is fast-by-default and interactive only on `ji` (the heir
   of the old always-interactive `j = fasd_cd -i`). fasd's `z`/`zz`/`d` directory aliases are
   **not** recreated — `j`/`ji` subsume them. *The core decision; interactively confirmed over
   stock `z`/`zi` and over a `z` + `alias j=zi` hybrid.*

3. **[confirmed] ZX3 Drop file-frecency commands.** fasd's file/any-type commands — `f`, `a`,
   `s`, `sf`, `sd` — have no zoxide equivalent (zoxide indexes directories only) and are
   removed with fasd. Feature scope is directory-jumping only. Ad-hoc file and history finding
   is already served by the fzf keybindings sourced from `~/.fzf.zsh` (Ctrl-T files, Ctrl-R
   history, Alt-C cd), so no shell shims are added.

4. **[confirmed] ZX4 Inline init; retire the cached-init file.** Replace the `.zshrc` fasd
   bootstrap (which cached `fasd --init` output to `~/.fasd-init-zsh`, regenerating when the
   binary out-dated the cache) with a single guarded `eval "$(zoxide init zsh --cmd j)"`.
   zoxide's init is a fast single-binary call, so the cache mechanism is unnecessary. Delete
   the tracked `.fasd-init-zsh`. Because `install.sh` rsync is additive (no `--delete`;
   D7/C3), the stale `~/.fasd-init-zsh` and `~/.fasd` persist in `$HOME` on already-installed
   machines — they are inert once the `.zshrc` block is gone, and cleanup is a documented
   manual `rm`, not repo machinery. *Consistent with and relies on D7/C3.*

5. **[confirmed] ZX5 No frecency migration (start fresh).** The accumulated `~/.fasd`
   database is machine-local runtime state (gitignored) and is not migrated; zoxide rebuilds
   ranks from `cd` activity going forward. The z-format import escape hatch
   (`zoxide import --from=z ~/.fasd`, valid because fasd's DB is z-format-compatible) is noted
   only in the final report for anyone who wants it — it is a per-machine runtime step and is
   **not** added to any tracked file.

6. **[confirmed] ZX6 Ignore + doc footprint.** Remove the `.fasd` line from `.gitignore` (its
   DB no longer exists; zoxide's DB lives under `~/.local/share/zoxide/`, which is not part of
   the `$HOME` overlay — `.local/` is untracked — so no replacement ignore entry is needed).
   The default-deny `.claude/*` whitelist (D5) is left untouched. Add the inline *why* comment
   to the new `.zshrc` zoxide line per `CLAUDE.md` §"Inline documentation in configs" (the
   non-obvious `--cmd j` choice and the dirs-only successor note). No `CLAUDE.md` change is
   required — it never referenced fasd. *Consistent with D5; touches only the unrelated
   `.fasd` ignore line.*
