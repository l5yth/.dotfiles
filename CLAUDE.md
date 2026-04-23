# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Layout

The repo root is a direct overlay of `$HOME`. A file at `./.zshrc` installs to `$HOME/.zshrc`; `./.config/i3/config` to `$HOME/.config/i3/config`; etc. Adding a new top-level entry means it will ship to every installed machine unless explicitly excluded in `install.sh`.

Metadata that must NOT land in `$HOME`: `.git/`, `.gitignore`, `.gitmodules`, `README.md`, `LICENSE`, `install.sh`, `CLAUDE.md`, `.github/`, `.claude/`. The exclude list in `install.sh` enforces this — update it when adding new metadata.

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
- The CPU microcode block (`intel-ucode` / `amd-ucode`) is skipped — the container has no bootloader to consume the microcode blobs, and the choice is vendor-specific per machine rather than a portable default. Keep the README note; don't add the packages to `ci.yml`.

## Inline documentation in configs

The shipped configs are the documentation. For non-obvious lines in `.zshrc`, `.xinitrc`, `.config/i3/**`, `.bin/**`, systemd units, and autostart `*.desktop` files, leave a short (1–4 line) comment above the line explaining *why* it's there — the failure mode it prevents, the race it closes, the upstream bug it works around, the ordering constraint from systemd/X/dbus. Don't restate what the command does; explain what breaks if the line is removed.

This inverts the usual "default to no comments" rule — only for dotfiles configs, and only for non-obvious lines. Skip aliases, plain env exports, and wizard-default keybindings. Bar: *would a reader be surprised or confused by this line six months from now?* Link commits, PRs, or READMEs when the rationale lives elsewhere (e.g., the `88a56cf` reference above the `xidlehook` exec in `.config/i3/config`).

## Secret-service / pinentry invariant

Signal, Element, and other Chromium/Electron apps keep their SQLCipher key at rest in `~/.config/<app>/config.json` (`encryptedKey`), symmetrically encrypted by a 16-byte secret fetched from `pass-secret-service` via libsecret. That secret is stored as a gpg-encrypted file under `~/.password-store/secret-service/Default/*.gpg`, so every read requires `gpg-agent` + `pinentry`.

If pinentry can't prompt when Chromium calls `secret_item_get_secret()`, `KeyStorageLibsecret::GetKeyImpl()` does not distinguish "item missing" from "item unreadable" — it silently generates a new random 16-byte key and writes it back, overwriting the old `*.gpg` value. The app's on-disk `encryptedKey` is still encrypted with the old key, so the next launch fails SQLCipher's page-1 HMAC check (`SQLITE_NOTADB: file is not a database`). The old key is unrecoverable; only `rm -rf ~/.config/<app>` + relink restores the app.

The guardrail is `exec_always --no-startup-id gpg-connect-agent updatestartuptty /bye` in `.config/i3/config`, ordered before `dex --autostart`. It plumbs the X session's `DISPLAY`/`GPG_TTY` into the systemd-started gpg-agent so pinentry-gtk has a display to draw on. **Do not remove or reorder this past `dex` unless every Chromium/Electron autostart is also gone** — leaving it off turns every boot into a dice roll on whether your Signal DB survives.

Diagnostic signature when this fails: `journalctl --user -u gpg-agent` shows `command 'PKDECRYPT' failed: Inappropriate ioctl for device <Pinentry>` within a second of the app's `Database startup error: sqlite error(SQLITE_NOTADB)`. Separate failure mode from the DH-padding bug patched in the README Extras / CI `pass-secret-service-git` build block — always check `gpg-agent` logs before suspecting the transport patch.

## Validation commands

- `bash -n install.sh` — syntax check before committing script edits.
- `HOME=$(mktemp -d) ./install.sh` — exercise the full copy + backup flow against a scratch `$HOME`.
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` — quick YAML parse check for workflow edits.
- `i3 -C -c .config/i3/config` — validate the i3 config before reload.
- `bash -n .zshrc` — syntax check zsh rc edits (zsh itself has no `-n`-equivalent for interactive rc files; bash is close enough for the subset we use).

There is no test suite. CI is the integration test.
