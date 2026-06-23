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
