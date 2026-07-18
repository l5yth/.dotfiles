# ACCEPTANCE — Fold `.claude` config into `.dotfiles`

Verification contract for the work specified in `SPEC.md`. A reviewer with **zero context
from the build session** must be able to judge the result against this file alone.

**Format.** Follows the repo's existing validation idiom (`CLAUDE.md` §Validation
commands): each criterion is a concrete command plus the expected result. Unless noted,
run commands from the repo root (`~/.src/l5yth/.dotfiles`). `$REPO` below means that path.

**Scratch-`HOME` harness** (used by the C-series; from `CLAUDE.md` §Validation):

```bash
TMPHOME=$(mktemp -d)
HOME="$TMPHOME" "$REPO/install.sh"     # deploys the repo tree into the throwaway HOME
```

A great result satisfies **every** criterion below.

---

## A. Repo integration & ignore policy  (SPEC D1, D4, D5)

- **A1 — `.claude/` is no longer ignored wholesale.** `.dotfiles/.gitignore` does **not**
  contain a blanket `.claude/` rule. Instead it uses a default-deny whitelist anchored to
  `.claude/`.
  Verify: `grep -n claude .gitignore` shows a `/.claude/*`-style ignore plus explicit
  `!`-unignores; there is no standalone `.claude/` line.

- **A2 — Curated config is tracked, nothing else.** `git ls-files .claude/` lists **only**
  files under `commands/`, `skills/`, `agents/`, `hooks/`, the file `.claude/CLAUDE.md`,
  and `.claude/settings.json` — and no others.
  Verify: `git ls-files .claude/` — every line is under one of those paths. There is no
  `.credentials.json`, `history.jsonl`, `settings.local.json`, `projects/`, `sessions/`,
  `shell-snapshots/`, `cache/`, `plugins/`, `backups/`, `file-history/`, `debug/`,
  `session-env/`, `tasks/`, `plans/`, `paste-cache/`, or `mcp-needs-auth-cache.json`.

- **A3 — Whitelist actually whitelists.** Tracked paths are not ignored; everything else
  under `.claude/` is.
  Verify: `git check-ignore -v .claude/commands/kickoff.md` → **no output** (not ignored).
  `git check-ignore -v .claude/projects/x` and `git check-ignore -v .claude/cache/x` →
  each prints a matching rule (ignored).

## B. Secrets & state safety  (SPEC D5, D9)

- **B1 — Secrets/state are unstageable by normal add.** For each of
  `.claude/.credentials.json`, `.claude/history.jsonl`, `.claude/settings.local.json`,
  `.claude/projects/p`, `.claude/sessions/s`, `.claude/shell-snapshots/x`,
  `.claude/plugins/x`: `git check-ignore <path>` prints the path (i.e. it is ignored).
  Verify: a `git add .claude/` followed by `git status --short` stages none of them.

- **B2 — Pre-commit guard hard-blocks force-added secrets, and survives a fresh clone.**
  The guard is a **tracked** script (e.g. under `.githooks/` or `.bin/`), wired so it is
  active after `install.sh` runs on a fresh clone (e.g. `core.hooksPath`) — **not** a
  one-off in `.git/hooks/` that wouldn't travel.
  Verify (behavioral):
  ```bash
  echo secret > .claude/.credentials.json
  git add -f .claude/.credentials.json
  git commit -m test            # MUST fail, naming the offending path; exit code != 0
  git restore --staged .claude/.credentials.json && rm -f .claude/.credentials.json
  ```
  Repeat with `.claude/history.jsonl` and a path under `.claude/projects/` → both
  rejected. A clean file under `.claude/commands/` must **pass** the guard: stage it and
  run `.githooks/pre-commit; echo $?` → `0` (checking the hook directly avoids coupling to
  commit signing — real commits here are GPG-signed, so an end-to-end sandbox commit needs
  `git -c commit.gpgsign=false`).
  Verify (reproducible): the hook path is tracked (`git ls-files | grep -E 'githooks|pre-commit|guard'` is non-empty) and `install.sh` (or a documented bootstrap step) sets it up.

## C. Deployment via `install.sh`  (SPEC D2, D7, D10)

- **C1 — Script is valid.** `bash -n install.sh` exits 0.  *(`CLAUDE.md` §Validation)*

- **C2 — Curated config deploys to `~/.claude/`.** After the scratch-`HOME` harness:
  `test -f "$TMPHOME/.claude/commands/kickoff.md"` succeeds, and its contents match the
  repo copy (`diff "$REPO/.claude/commands/kickoff.md" "$TMPHOME/.claude/commands/kickoff.md"`
  → no diff).

- **C3 — Deploy is additive; runtime state survives.** Pre-seed the scratch HOME before
  installing, then confirm nothing is deleted:
  ```bash
  TMPHOME=$(mktemp -d)
  mkdir -p "$TMPHOME/.claude/projects/old"; echo k > "$TMPHOME/.claude/.credentials.json"
  HOME="$TMPHOME" "$REPO/install.sh" >/dev/null
  test -d "$TMPHOME/.claude/projects/old" && test -f "$TMPHOME/.claude/.credentials.json"
  ```
  Both must still exist (install uses no `--delete`).

- **C4 — Process docs never deploy.** After the harness, none of these exist:
  `$TMPHOME/SPEC.md`, `$TMPHOME/ACCEPTANCE.md`.

- **C5 — Machine-local settings never deploy.** With `.claude/settings.local.json`
  present in the repo working tree, after the harness `test ! -e
  "$TMPHOME/.claude/settings.local.json"` succeeds (rsync-excluded).

- **C6 — Shared settings deploys.** After the harness, `test -f
  "$TMPHOME/.claude/settings.json"` succeeds and matches the repo copy.

## D. Documentation consistency  (SPEC D7, D8)

- **D1 — `CLAUDE.md` reflects that `.claude/` now ships.** The §Layout "must NOT land in
  `$HOME`" list no longer includes `.claude/`, and it includes the new non-shipping docs
  (`SPEC.md`, `ACCEPTANCE.md`).
  Verify: read `CLAUDE.md` §Layout — `.claude/` absent from the exclude list; `SPEC.md`
  / `ACCEPTANCE.md` present (or explicitly documented as excluded).

- **D2 — Doc ↔ config agree (no drift).** Every path `CLAUDE.md` claims is excluded from
  deploy is actually excluded in `install.sh`, and every `install.sh` exclude that is
  metadata is mentioned in `CLAUDE.md`. The new `.claude` overlay section describes the
  edit-in-repo truth flow and the `settings.local`/secrets invariant.
  Verify: cross-read the `install.sh` `--exclude` list against the `CLAUDE.md` §Layout
  list; they agree.

- **D3 — README ↔ CI coupling respected.** If `README.md` changed, the matching step in
  `.github/workflows/ci.yml` was updated in step (per `CLAUDE.md` §README↔CI). If README
  is unchanged, this is automatically satisfied.
  Verify: `git log -1 --stat` / `git diff` — README and ci.yml either both untouched or
  changed together.

## E. Seed & scope boundary  (SPEC D10)

- **E1 — The one existing command is seeded verbatim.** `.claude/commands/kickoff.md` is
  tracked and byte-identical to the source it was seeded from.
  Verify: `git ls-files .claude/commands/kickoff.md` is non-empty; if the live source
  still exists, `diff ~/.claude/commands/kickoff.md .claude/commands/kickoff.md` → no diff.

- **E2 — Tracked content is the curated command set; no agents/skills.** The tracked
  commands are exactly the curated set `bugfix.md`, `feature.md`, `kickoff.md`
  (`bugfix`/`feature` added in `6f5cd0f`, after the fold-in project — see the SPEC D10
  update note); no agents or skills are tracked. This feature authored no new commands.
  Verify: `git ls-files .claude/commands/` lists exactly those three `.md` files and
  nothing else; `git ls-files .claude/agents/ .claude/skills/` is empty.

## F. No regressions  (SPEC D3, D7)

- **F1 — The rest of the dotfiles still deploy.** After the scratch-`HOME` harness, an
  unrelated tracked file lands, e.g. `test -f "$TMPHOME/.zshrc"`.

- **F2 — CI workflow still parses.**
  `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` exits 0.
  *(`CLAUDE.md` §Validation)*

- **F3 — Submodule symlinks intact.** `.zsh/pure/async` and `.zsh/pure/prompt_pure_setup`
  remain symlinks (`CLAUDE.md` §Install flow invariant).
  Verify: `test -L .zsh/pure/async`.

- **F4 — Redundant repo handled deliberately.** The empty `~/.src/l5yth/.claude` repo is
  either removed (with the user's explicit confirmation) or explicitly left in place by
  user decision — not silently abandoned. Verify: stated in the final report.

---

## Decision traceability  (re-verify at every checkpoint, per `SPEC.md`)

| SPEC decision | Proven by |
|---|---|
| 1 Integration model (fold in) | A1, A2, C2 |
| 2 Truth flow (edit-in-repo → rsync) | C2, C3, D2 |
| 3 Work+docs in `.dotfiles`, excluded | C4, D1 |
| 4 Tracked set | A2, E2 |
| 5 Whitelist ignore | A1, A3, B1 |
| 6 settings split | C5, C6, B1 |
| 7 install.sh changes | C1, C3, C4, C5, D2 |
| 8 Doc sync | D1, D2, D3 |
| 9 Secrets guard | B2 |
| 10 Seed + scope | C2, E1, E2 |

---

## Feature: Persist max effort level  (Feature SPEC FD1–FD6)

Verifies the feature appended to `SPEC.md` under the same heading. Same idiom as A–F:
each criterion is a command plus its expected result; run from `$REPO` unless noted. The
**scratch-`HOME` harness** at the top of this file applies to G3.

- **G1 — `max` is persisted via the env var, not `effortLevel`.** The tracked shared
  `settings.json` sets `env.CLAUDE_CODE_EFFORT_LEVEL` to `max`, and does **not** rely on
  `effortLevel` for max (which would downgrade to `xhigh`).
  Verify: `python3 -c "import json; d=json.load(open('.claude/settings.json')); assert d.get('env',{}).get('CLAUDE_CODE_EFFORT_LEVEL')=='max'; assert d.get('effortLevel')!='max'; print('ok')"`
  → prints `ok` (and exits 0, proving the file is valid JSON). *(FD1, FD2)*

- **G2 — Prior settings keys are preserved.** Adding the `env` block did not drop the
  existing `theme` / `enabledPlugins`.
  Verify: `python3 -c "import json; d=json.load(open('.claude/settings.json')); assert d['theme']=='dark-ansi'; assert d['enabledPlugins']['rust-analyzer-lsp@claude-plugins-official'] is True; print('ok')"`
  → `ok`. *(guards C6/A2)*

- **G3 — The setting deploys to `~/.claude/` unchanged.** After the scratch-`HOME` harness:
  `diff "$REPO/.claude/settings.json" "$TMPHOME/.claude/settings.json"` → no diff, and
  `python3 -c "import json;print(json.load(open('$TMPHOME/.claude/settings.json'))['env']['CLAUDE_CODE_EFFORT_LEVEL'])"`
  → `max`. *(FD2; C6 still holds with the new content)*

- **G4 — `settings.json` stays tracked and whitelisted; no new `.claude/` surface.**
  `git ls-files .claude/settings.json` is non-empty; `git check-ignore -v
  .claude/settings.json` → **no output** (not ignored). `git ls-files .claude/` lists no
  files beyond the curated set already required by A2. *(FD3, FD6)*

- **G5 — Feature is confined to `settings.json` + docs.** No deploy/ignore/guard machinery
  changed.
  Verify: `grep -ni effort install.sh .gitignore .githooks/pre-commit` → **no output**
  (the mechanism lives only in `settings.json`; the rationale only in `CLAUDE.md`). *(FD6)*

- **G6 — `CLAUDE.md` documents the env-var rationale.** §"Claude Code config" names
  `CLAUDE_CODE_EFFORT_LEVEL` and explains *why* the env var is used rather than the
  `effortLevel` key (key cannot persist `max`).
  Verify: `grep -n CLAUDE_CODE_EFFORT_LEVEL CLAUDE.md` is non-empty and the surrounding
  text states the `effortLevel`-downgrades-`max` reason. *(FD4, FD5)*

- **G7 — Mechanism re-verified against the installed CLI (build-time gate).** The doc-only
  assumption behind FD1 was confirmed against the actually-installed Claude Code before the
  feature was declared done — `CLAUDE_CODE_EFFORT_LEVEL=max` is the supported persistence
  path and `effortLevel` does not accept `max`.
  Verify: the final report cites the evidence (CLI help / settings reference / package
  inspection). *(FD1)*

- **G-REG — No regression in A–F.** Every prior criterion A1–F4 still passes after this
  feature lands. Explicitly at risk and re-checked: **C6** (shared settings deploys and
  matches repo — now with the `env` block; covered by G3), and **A2 / B1** (only the
  curated set is tracked, `settings.local.json` excluded — a content-only edit to
  `settings.json` must not introduce new tracked or stageable paths; covered by G4). All
  other criteria are unaffected by editing an already-managed file.

**Feature decision traceability** (re-verify at every checkpoint, per `SPEC.md`)

| Feature SPEC decision | Proven by |
|---|---|
| FD1 Mechanism (env var, not `effortLevel`) | G1, G6, G7 |
| FD2 Scope (shared, all machines) | G1, G3 |
| FD3 Extends D6 (env block in shared settings) | G1, G4 |
| FD4 Extends D8 (rationale in `CLAUDE.md`) | G6 |
| FD5 Reaffirms D2 (truth flow) | G6 |
| FD6 Reaffirms D5/D7/D9 (no machinery change) | G4, G5, G-REG |

---

## Feature: Persist global Claude standards (`.claude/CLAUDE.md`)  (Feature SPEC GS1–GS6)

Verifies the feature appended to `SPEC.md` under the same heading. Same idiom as A–G: each
criterion is a command plus its expected result; run from `$REPO` unless noted. The
**scratch-`HOME` harness** at the top of this file applies to H3/H4.

- **H1 — The global standards file is tracked and whitelisted.** `git ls-files
  .claude/CLAUDE.md` is non-empty, and `git check-ignore -v .claude/CLAUDE.md` → **no
  output** (not ignored, despite the default-deny `/.claude/*` rule).
  Verify: both commands as stated. *(GS1; guards D5)*

- **H2 — Content is the verbatim standards plus a precedence preamble; placeholders kept.**
  `.claude/CLAUDE.md` carries the title `# l5y standards (all projects)`, exactly the six
  section headings (`## Licensing (REUSE-compliant)`, `## Tests`, `## Documentation`,
  `## Structure`, `## Formatting and lint`, `## Git workflow`), a preamble stating a
  project's own `CLAUDE.md` wins only on a direct conflict, and the **unresolved** SPDX
  placeholders.
  Verify: `grep -c '^## ' .claude/CLAUDE.md` → `6`; `grep -qF 'l5y standards (all projects)'
  .claude/CLAUDE.md`; `grep -qi 'conflict' .claude/CLAUDE.md` (the preamble); and both
  `grep -qF 'SPDX-FileCopyrightText: <year> <holder>' .claude/CLAUDE.md` and
  `grep -qF 'SPDX-License-Identifier: <ID>' .claude/CLAUDE.md` succeed (exit 0). *(GS2, GS3)*

- **H3 — The file deploys to `~/.claude/` unchanged.** After the scratch-`HOME` harness:
  `test -f "$TMPHOME/.claude/CLAUDE.md"` and `diff "$REPO/.claude/CLAUDE.md"
  "$TMPHOME/.claude/CLAUDE.md"` → no diff. This proves the GS4 anchor fix actually lets the
  overlay file land. *(GS1, GS4)*

- **H4 — The repo-root project `CLAUDE.md` still does not deploy.** After the harness,
  `test ! -e "$TMPHOME/CLAUDE.md"` succeeds — the anchored exclude still excludes the root
  file while shipping the overlay one. *(GS4; guards the C4-style "repo docs don't ship")*

- **H5 — `install.sh` anchors only the root `CLAUDE.md` exclude.** The exclude list
  contains the anchored rule and not the unanchored one.
  Verify: `grep -qF "exclude='/CLAUDE.md'" install.sh` succeeds; `grep -F
  "exclude='CLAUDE.md'" install.sh` prints **nothing** (exit 1). The sibling root-file
  excludes stay present and unanchored (`grep -qF "exclude='LICENSE'" install.sh`
  succeeds). *(GS4)*

- **H6 — `CLAUDE.md` documents the overlay file and the anchoring rationale.** Repo-root
  `CLAUDE.md` §"Claude Code config" names `.claude/CLAUDE.md` as shipped global instructions
  and explains why the `install.sh` exclude must stay anchored (`/CLAUDE.md`) or the overlay
  file stops deploying.
  Verify: `grep -n '\.claude/CLAUDE\.md' CLAUDE.md` is non-empty, and the surrounding
  §"Claude Code config" text states the anchored-exclude reason (e.g. `grep -ni anchor
  CLAUDE.md` is non-empty). *(GS5)*

- **H-REG — No regression in A–G.** Every prior criterion A1–F4 and G1–G-REG still passes.
  Explicitly at risk and re-checked:
  - **A2 / E2** (only the curated set is tracked; commands are exactly the three, no
    agents/skills): adding `.claude/CLAUDE.md` is permitted by A2's own allowed list and is
    not under `commands/`. Re-verify `git ls-files .claude/` shows nothing outside
    `commands/`, `skills/`, `agents/`, `hooks/`, `.claude/CLAUDE.md`, `.claude/settings.json`;
    `git ls-files .claude/commands/` is exactly `bugfix.md`, `feature.md`, `kickoff.md`; and
    `git ls-files .claude/agents/ .claude/skills/` is empty.
  - **C2 / C6 / F1** (other tracked files still deploy): the anchored exclude must not stop
    `.zshrc`, `.claude/settings.json`, or `.claude/commands/kickoff.md` from landing — re-run
    C2/C6/F1; H3 additionally confirms the new file lands.
  - **C4** (`SPEC.md`/`ACCEPTANCE.md` never deploy): unaffected (separate excludes); H4
    additionally confirms the root `CLAUDE.md` still doesn't ship.
  - **D2** (doc ↔ config agree): the new `install.sh` exclude and the `CLAUDE.md` §Layout /
    §"Claude Code config" text stay consistent — covered by H5 + H6.

**Feature decision traceability** (re-verify at every checkpoint, per `SPEC.md`)

| Feature SPEC decision | Proven by |
|---|---|
| GS1 Location / mechanism | H1, H3 |
| GS2 Precedence model | H2 |
| GS3 Content fidelity (verbatim + preamble, placeholders kept) | H2 |
| GS4 install.sh anchor (`/CLAUDE.md`) | H3, H4, H5 |
| GS5 Doc sync | H6 |
| GS6 No ignore/guard/scope change | H1, H-REG |

---

## Feature: Replace fasd with zoxide  (Feature SPEC ZX1–ZX6)

Verifies the feature appended to `SPEC.md` under the same heading. Same idiom as A–H: each
criterion is a command plus its expected result; run from `$REPO` unless noted. The
**scratch-`HOME` harness** at the top of this file applies to I8.

- **I1 — README swaps the package; no `fasd` left in it.** The README `pacman -S` block
  installs `zoxide` and no longer `fasd`, and `zoxide` stays in the plain `pacman` list (no
  new AUR/`pikaur` block was introduced for it).
  Verify: `grep -F 'pacman -S' README.md | grep -qw zoxide` succeeds; `grep -qw fasd
  README.md` → **exit 1** (nothing). *(ZX1)*

- **I2 — CI package list swaps in lockstep, and the workflow still parses.** The mirrored
  list in `.github/workflows/ci.yml` gains `zoxide` and drops `fasd`, satisfying the
  README↔CI coupling (prior criterion D3).
  Verify: `grep -qw zoxide .github/workflows/ci.yml` succeeds; `grep -qw fasd
  .github/workflows/ci.yml` → **exit 1**;
  `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` exits 0. *(ZX1;
  D3/F2 coupling)*

- **I3 — `.zshrc` init surface is zoxide `--cmd j`, single-eval, commented, no fasd.** The
  fasd bootstrap is gone; the block is one guarded `eval "$(zoxide init zsh --cmd j)"` with a
  short *why* comment, and there is no cache-file dance.
  Verify: `grep -qF 'zoxide init zsh --cmd j' .zshrc` succeeds; no fasd *code* remains —
  `grep -qiE 'fasd_cd|fasd_cache|command -v fasd|fasd --init' .zshrc` → **exit 1** (the
  migration comment may name `fasd` for documentation; only live invocations are forbidden);
  `grep -c 'zoxide init' .zshrc` → `1` (single init, no regen branch); a `#` comment appears
  immediately above the guarded `zoxide init` block (above the `if command -v zoxide` guard,
  per §Inline documentation's "comment above the block" idiom — read it to confirm it explains
  the `--cmd j`/dirs-only rationale). *(ZX2, ZX4, ZX6-comment)*

- **I4 — The cached-init file is deleted; file-frecency commands are gone with it.**
  `.fasd-init-zsh` — the sole definer of `a`/`s`/`sd`/`sf`/`d`/`f` — is removed from the repo.
  Verify: `test ! -e .fasd-init-zsh` succeeds; `git ls-files .fasd-init-zsh` prints
  **nothing**; `git grep -nE "^alias (a|s|sd|sf|d|f)=" -- .zshrc` prints **nothing** (no
  file-command aliases were relocated into `.zshrc`). *(ZX3, ZX4)*

- **I5 — `.gitignore` retires the `.fasd` entry; the `.claude/*` whitelist is intact.** The
  bare `.fasd` line is gone (its DB no longer exists), and no replacement entry was needed
  (zoxide's DB lives under untracked `~/.local/share/zoxide/`). The default-deny `.claude/`
  whitelist is byte-for-byte unchanged.
  Verify: `grep -qxF '.fasd' .gitignore` → **exit 1** (line removed); `grep -qF '/.claude/*'
  .gitignore` and `grep -qF '!/.claude/commands/' .gitignore` both succeed (whitelist
  untouched — guards prior A1/A3). *(ZX6)*

- **I6 — No frecency migration is wired into any shipped/tracked config.** The
  `zoxide import` escape hatch (ZX5) lives only in prose (`SPEC.md`/`ACCEPTANCE.md`), never in
  deployed config.
  Verify: `grep -rn 'zoxide import' .zshrc install.sh README.md .github/workflows/ci.yml`
  prints **nothing**. *(ZX5)*

- **I7 — Behavioral gate: `--cmd j` defines `j` and `ji`, not `z` (cited in final report).**
  On a machine with `zoxide` installed, the emitted init defines both jump commands under the
  `j` name and does **not** define a bare `z`; `.zshrc` stays syntactically valid.
  Verify: `zsh -c 'autoload -Uz add-zsh-hook; eval "$(zoxide init zsh --cmd j)"; whence -w j;
  whence -w ji; whence -w z'` → `j` and `ji` report `function`, `z` reports `none`; and
  `bash -n .zshrc` exits 0. If `zoxide` is not yet installed on the build machine, the final
  report says so and records that the gate was run against the emitted init at first install.
  *(ZX2)*

- **I8 — Deploy lands the new init and is additive over the retired files.** The zoxide line
  deploys, and pre-existing `~/.fasd-init-zsh` / `~/.fasd` are **not** deleted (rsync uses no
  `--delete`; the stale files are inert, per ZX4).
  Verify:
  ```bash
  TMPHOME=$(mktemp -d)
  printf 'x\n' > "$TMPHOME/.fasd-init-zsh"; printf '/tmp|1|1\n' > "$TMPHOME/.fasd"
  HOME="$TMPHOME" "$REPO/install.sh" >/dev/null
  grep -qF 'zoxide init zsh --cmd j' "$TMPHOME/.zshrc"          # new init landed
  test -f "$TMPHOME/.fasd-init-zsh" && test -f "$TMPHOME/.fasd" # stale files survive
  ```
  All three checks pass. *(ZX4; mirrors C3's additive-deploy guarantee)*

- **I-REG — No regression in A–H.** Every prior criterion A1–F4, G1–G-REG, and H1–H-REG still
  passes after this feature lands. Explicitly at risk and re-checked:
  - **D3** (README↔CI coupling): README and `ci.yml` changed together — covered by I1 + I2.
  - **F2** (ci.yml parses): re-checked after the package swap — covered by I2.
  - **F1 / C2** (unrelated tracked files still deploy): `.zshrc` was edited and must still land
    and be valid — covered by I3 (`bash -n` in I7) and I8 (it deploys).
  - **A1 / A3** (default-deny `.claude/` whitelist intact): the `.gitignore` edit touches only
    the unrelated `.fasd` line — covered by I5.
  - **A2 / B1** (only the curated set is tracked; nothing new stageable): this feature *removes*
    a tracked file (`.fasd-init-zsh`) and adds no new tracked paths under `.claude/`; re-run
    A2/B1 to confirm no new tracked or stageable paths appear.
  All other criteria are unaffected (they concern the `.claude/` overlay, which this feature
  does not touch).

**Feature decision traceability** (re-verify at every checkpoint, per `SPEC.md`)

| Feature SPEC decision | Proven by |
|---|---|
| ZX1 Mechanism (pkg swap, README + CI) | I1, I2 |
| ZX2 Command surface (`--cmd j` → `j`/`ji`) | I3, I7 |
| ZX3 Drop file-frecency commands | I4 |
| ZX4 Inline init; retire cached-init file | I3, I4, I8 |
| ZX5 No frecency migration | I6 |
| ZX6 Ignore + doc footprint | I5, I3 |
