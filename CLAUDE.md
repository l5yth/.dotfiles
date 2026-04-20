# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Layout

The repo root is a direct overlay of `$HOME`. A file at `./.zshrc` installs to `$HOME/.zshrc`; `./.config/i3/config` to `$HOME/.config/i3/config`; etc. Adding a new top-level entry means it will ship to every installed machine unless explicitly excluded in `install.sh`.

Metadata that must NOT land in `$HOME`: `.git/`, `.gitignore`, `.gitmodules`, `README.md`, `LICENSE`, `install.sh`, `CLAUDE.md`, `.github/`. The exclude list in `install.sh` enforces this — update it when adding new metadata.

## Install flow

`install.sh` copies (via `rsync`) the repo tree into `$HOME`. It resolves its own location, so the clone can live anywhere (README uses `~/.dotfiles`); the clone is kept in place so `git pull && ~/.dotfiles/install.sh` updates in place.

Conflict handling: rsync's `--backup --backup-dir` moves any file it would overwrite into `$(mktemp -d "$HOME/.dotfiles-backup-XXXXXX")`. A trap removes the backup dir if empty (both on success and on rsync failure). `.bin/dotfiles-resolve` walks a backup dir interactively (keep / restore / merge / skip) — use it to clean up after updates.

Symlinks inside `.zsh/pure/` (`async -> async.zsh`, `prompt_pure_setup -> pure.zsh`) are preserved by `rsync -a` and must stay intact; do not flatten or dereference that directory.

## README ↔ CI coupling

`.github/workflows/ci.yml` walks the README section-by-section (Base / Extras / Desktop / SSH-Keys / Proton Mail) to verify the bootstrap still works end-to-end on a clean Arch container. **When editing `README.md` — in particular the `pacman`, `pikaur`, `npm`, `nvm`, or `ssh-keygen` command blocks — update the matching step in `ci.yml` in the same commit.** Package names, install order, and flags must stay in sync; drift is what CI exists to catch.

Intentional CI divergences from the README (documented inline in the workflow):

- `systemctl enable --now …` lines are dropped — the Arch container has no systemd.
- `chsh -s` becomes `usermod -s` (runs as root).
- `source $HOME/.zshrc` is deferred to the final step, because `.zshrc` runs `nvm use lts/krypton` unconditionally and would fail before Extras installs nvm.
- `protonmail-bridge-core --cli` login is skipped (interactive); only the `pass init` prerequisite is exercised with a headless GPG key.
- `$GITHUB_WORKSPACE` is passed to sudo'd shells as a positional arg, not via env (sudo strips env and the inner `bash -eu` would die on unbound expansion).

## Validation commands

- `bash -n install.sh` — syntax check before committing script edits.
- `HOME=$(mktemp -d) ./install.sh` — exercise the full copy + backup flow against a scratch `$HOME`.
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` — quick YAML parse check for workflow edits.

There is no test suite. CI is the integration test.
