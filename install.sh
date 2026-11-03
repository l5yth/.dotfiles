#!/usr/bin/env bash
set -euo pipefail

command -v rsync >/dev/null || { echo "install.sh: rsync required" >&2; exit 1; }

SRC="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"

if [ "$SRC" = "$HOME" ]; then
	echo "install.sh: refusing to run with repo at \$HOME ($HOME)" >&2
	exit 1
fi

# Whether git is required depends on how this tree got here. For a real clone the
# submodule checkout and hooksPath wiring below both need it, so bail with a clear message
# rather than dying at the first git call. For a tarball copy (no $SRC/.git) it is optional
# and its only use is the best-effort spec clone (SPEC SR4), which warns and continues.
# Both tests use -e: in a worktree .git is a pointer file, not a folder, and -d took a
# worktree for a tarball, skipping its submodules and hooks (SPEC IW2).
if ! command -v git >/dev/null; then
	if [ -e "$SRC/.git" ]; then
		echo "install.sh: git required (this is a clone; submodules and hooks need it)" >&2
		exit 1
	fi
	echo "install.sh: git not found, skipping spec clone" >&2
fi

if [ -e "$SRC/.git" ]; then
	git -C "$SRC" submodule update --init --recursive
	# Git hooks in .git/hooks/ aren't version-controlled; point at the tracked guard.
	git -C "$SRC" config core.hooksPath .githooks
fi

# Agent instructions and code specs live in a separate repo (SPEC SR1), one entry per
# repository under spec/$org/$repo. The deployed ~/.claude/CLAUDE.md points every project
# at this clone, so the path must exist even when the clone itself doesn't.
# Best-effort by design (SR4): the repo is private, so it needs an SSH key that README
# §Base does not have yet when install.sh first runs, and CI has none at all. A hard
# failure would break bootstrap, so record it and warn at the end instead.
SPEC_REPO="git@github.com:l5yth/spec.git"
SPEC_DIR="$HOME/.src/l5yth/spec"
SPEC_FAILED=0
mkdir -p "$(dirname "$SPEC_DIR")"
# BatchMode=yes turns every interactive ssh prompt into an immediate failure. Without it
# a fresh machine hangs forever on GitHub's host-key verification question instead of
# falling through to the warning below, which is the whole point of a best-effort step.
export GIT_TERMINAL_PROMPT=0
export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -o BatchMode=yes}"
if ! command -v git >/dev/null; then
	SPEC_FAILED=1
elif [ -d "$SPEC_DIR/.git" ]; then
	# --ff-only: never invent a merge over spec edits that aren't pushed yet.
	git -C "$SPEC_DIR" pull --ff-only --quiet || SPEC_FAILED=1
else
	git clone --quiet "$SPEC_REPO" "$SPEC_DIR" || SPEC_FAILED=1
fi

for prior in "$HOME"/.dotfiles-backup-*; do
	[ -d "$prior" ] || continue
	rmdir "$prior" 2>/dev/null || true
done

BACKUP=$(mktemp -d "$HOME/.dotfiles-backup-XXXXXX")
trap 'rmdir "$BACKUP" 2>/dev/null || true' EXIT

# $HOME's own mode, read before the first rsync changes it and put back after both passes.
# -L reads the directory a symlinked $HOME points at: chmod follows the link, so the link's
# own 777 would otherwise be written onto that directory.
HOME_MODE=$(stat -L -c %a "$HOME")

# One-time migration (#49): the vendored Dracula vim theme (dracula/vim) moved all
# per-language highlight links into colors/dracula_base.vim and dropped its
# after/syntax/*.vim + after/plugin/dracula.vim overrides, which called the
# now-removed dracula#should_abort(). The rsync below is additive (no --delete),
# so stale copies of those files would linger in $HOME and throw E117 on every
# code file opened. Remove the obsolete set explicitly (rm -f/rmdir no-op when
# absent; rmdir only clears the dirs if empty, so any user-added after/ files stay).
rm -f "$HOME"/.vim/after/plugin/dracula.vim \
	"$HOME"/.vim/after/syntax/{css,gitcommit,html,javascript,javascriptreact,json,lua,markdown,ocaml,perl,php,plantuml,purescript,python,rst,ruby,rust,sass,sh,tex,typescript,typescriptreact,vim,xml,yaml}.vim 2>/dev/null || true
rmdir "$HOME"/.vim/after/syntax "$HOME"/.vim/after/plugin "$HOME"/.vim/after 2>/dev/null || true

# .claude/ ships as a $HOME overlay (see spec/l5yth/.dotfiles/CLAUDE.md §"Claude Code
# config"). Excludes keep repo metadata, process docs, and any machine-local/state/secret
# .claude paths out of $HOME; .gitignore is the primary guard against committing them —
# these are deploy-time defense-in-depth.
# SPEC.md, ACCEPTANCE.md and the repo-root CLAUDE.md moved to the spec repo (SPEC SR2), so
# those three excludes match nothing today. They are kept deliberately (SR9) as guards
# against a re-add, and '/CLAUDE.md' must keep its leading slash: an unanchored pattern
# also matches the shipped .claude/CLAUDE.md overlay (rsync matches a bare basename at any
# depth) and would silently block it from deploying.
# '/LICENSE' is anchored for the same reason and it is not hypothetical: the vendored
# i-have-adhd plugin ships upstream's MIT LICENSE at .claude/skills/i-have-adhd/LICENSE
# (AD8), and the unanchored form silently swallowed it — caught by ACCEPTANCE L7, which
# diffs the deployed tree against the repo. Any future root-file exclude whose basename
# also appears under .claude/ needs the same leading slash; README.md is the next
# candidate and is left unanchored only because nothing collides with it yet.
# .reticulum/ ships exactly one tracked file, the config. rnsd's own state sits beside it in
# ~/.reticulum/storage/ (transport_identity, ratchets) and ~/.reticulum/interfaces/, and the
# .gitignore whitelist hides an accidental copy of those from `git status` — so an untracked
# copy in the working tree would rsync over a machine's live identity with no trace of it.
# These two excludes are the deploy-time half of that guard; .gitignore is the commit-time
# half. Anchored for the reason given above.
# '.git' has no trailing slash: with one, rsync matches only a folder, and the .git of a
# worktree root and of every submodule (.zsh/pure/.git) is a pointer file, so both deployed.
# A worktree's pointer holds an absolute path, which made git take all of $HOME for a
# checkout of that branch. Unanchored, so the nested submodule pointer matches too (SPEC IW1).
# --checksum, on both passes: by default rsync compares size and mtime, git stores no mtimes,
# and so every file of a fresh worktree or clone looked changed and --backup kept an identical
# copy of each. Compared by content, only a file that differs is replaced and backed up; an
# identical one just gets its mtime and mode set in place (SPEC IW3).
rsync -avh \
	--checksum \
	--backup --backup-dir="$BACKUP" \
	--exclude='.git' \
	--exclude='.github/' \
	--exclude='.githooks/' \
	--exclude='.gitignore' \
	--exclude='.gitmodules' \
	--exclude='/CLAUDE.md' \
	--exclude='/LICENSE' \
	--exclude='README.md' \
	--exclude='SAILFISH.md' \
	--exclude='SPEC.md' \
	--exclude='ACCEPTANCE.md' \
	--exclude='install.sh' \
	--exclude='.claude/settings.local.json' \
	--exclude='.claude/.credentials.json' \
	--exclude='.claude/history.jsonl' \
	--exclude='.claude/projects/' \
	--exclude='.claude/sessions/' \
	--exclude='/.reticulum/storage/' \
	--exclude='/.reticulum/interfaces/' \
	--exclude='/hosts/' \
	"$SRC"/ "$HOME"/

# Per-host overlay: hosts/<uname -n>/ is a second $HOME overlay, mirroring the repo
# root's layout, applied *after* the common tree so a machine-specific file wins over
# its shared counterpart. It exists for config that cannot guard itself at runtime —
# an i3 keybinding is global whether or not the hardware behind it is present, unlike
# a wireplumber device rule, which simply never matches on a machine without the
# device and so belongs in the common tree.
#
# The exclude above is anchored ('/hosts/'): unanchored, rsync matches a bare basename
# at any depth and would also swallow a legitimate ~/hosts path elsewhere in the tree.
# Same failure class as the '/CLAUDE.md' and '/LICENSE' anchors documented above.
#
# Absent directory is the normal case: most machines have no overlay, and adding one is
# `mkdir hosts/$(uname -n)`. No hostname list is kept anywhere; the directory *is* the
# registration.
HOST_DIR="$SRC/hosts/$(uname -n)"
if [ -d "$HOST_DIR" ]; then
	echo
	echo "== host overlay: hosts/$(uname -n) =="
	# --checksum for the reason given at the first pass.
	rsync -avh \
		--checksum \
		--backup --backup-dir="$BACKUP" \
		"$HOST_DIR"/ "$HOME"/
fi

# The overlay ships one file each into ~/.gnupg and ~/.ssh, and rsync -a gives every file and
# folder it writes the mode it has in the clone. Git records no folder modes and only the
# executable bit, so the clone holds 755 folders and 644 files, and every run reopened what
# README §SSH-Keys and §Proton Mail close; gpg then warns about an unsafe homedir. This runs
# after the host pass, which is a second rsync and would reopen them again.
chmod 700 "$HOME/.gnupg" "$HOME/.ssh"
chmod 600 "$HOME/.gnupg/gpg-agent.conf" "$HOME/.ssh/authorized_keys"
# rsync -a also gives $HOME itself the mode of the clone root, so every run reset it: a 700
# home became 755, and a clone made under umask 002 (Sailfish's default) left it 775, which
# sshd refuses for authorized_keys. Put back the mode read before the first pass.
chmod "$HOME_MODE" "$HOME"

# Retired Bash guard files (spec/l5yth/.dotfiles SPEC NG3). The rsync is additive, so a file
# the repo stops shipping stays in $HOME on every machine that once installed it. These are
# deleted by exact path: guard-bash.py and test_guard_bash.py shipped until da56a58, and
# deny-risky.rb was never tracked here but turned up on a machine all the same. This runs
# after both passes, so an untracked copy left in a clone cannot come back with them.
rm -f "$HOME/.claude/hooks/guard-bash.py" "$HOME/.claude/hooks/test_guard_bash.py" \
	"$HOME/.claude/hooks/deny-risky.rb"

# buero, the letter and invoice tool of byz-f/typst-templates (SPEC BU1 to BU3): clone the
# checkout or fast-forward it, rebuild the binary only when the checkout moved since the last
# good build, then `buero setup` (links the templates, fetches the jars) and `buero doctor`.
# Best effort like the spec clone (SR4): the repository is private, and a machine may have no
# SSH key, toolchain, typst or Java yet (README §Base runs this script first), so every failure
# becomes a warning after the summary and the install still exits 0. It runs after the overlay,
# which ships buero's config. BUERO_REPO only lets the acceptance criteria point the clone at a
# local stand-in (SPEC BU6).
BUERO_REPO="${BUERO_REPO:-git@github.com:byz-f/typst-templates.git}"
BUERO_DIR="$HOME/.src/byz-f/typst-templates"
BUERO_BIN="${CARGO_HOME:-$HOME/.cargo}/bin/buero"
# The commit of the last build whose setup succeeded. A failed build or setup leaves it as it
# was, so the next run tries again; an unchanged checkout skips the minutes a release build
# takes (SPEC BU2, BU3).
BUERO_STAMP="$HOME/.local/state/dotfiles/buero-commit"
BUERO_WARN=()
if ! command -v git >/dev/null; then
	BUERO_WARN+=("warning: buero: could not clone or update $BUERO_REPO into $BUERO_DIR")
elif [ -d "$BUERO_DIR/.git" ]; then
	# --ff-only: never invent a merge over commits that are not pushed yet.
	git -C "$BUERO_DIR" pull --ff-only --quiet ||
		BUERO_WARN+=("warning: buero: could not clone or update $BUERO_REPO into $BUERO_DIR")
else
	git clone --quiet "$BUERO_REPO" "$BUERO_DIR" ||
		BUERO_WARN+=("warning: buero: could not clone or update $BUERO_REPO into $BUERO_DIR")
fi
if [ -d "$BUERO_DIR/.git" ]; then
	buero_head=$(git -C "$BUERO_DIR" rev-parse HEAD 2>/dev/null) || buero_head=""
	if [ -n "$buero_head" ] &&
		{ [ "$buero_head" != "$(cat "$BUERO_STAMP" 2>/dev/null)" ] || [ ! -x "$BUERO_BIN" ]; }; then
		buero_missing=()
		for cmd in cargo typst java; do
			command -v "$cmd" >/dev/null || buero_missing+=("$cmd")
		done
		if [ "${#buero_missing[@]}" -gt 0 ]; then
			BUERO_WARN+=("warning: buero: not built, missing: ${buero_missing[*]}")
		# --force: cargo skips a path install whose crate version is unchanged, so a new commit
		# without a version bump would leave the old binary. --locked: build what Cargo.lock pins.
		elif cargo install --locked --force --path "$BUERO_DIR"; then
			# setup takes the working directory as the checkout to link.
			if (cd "$BUERO_DIR" && "$BUERO_BIN" setup); then
				mkdir -p "$(dirname "$BUERO_STAMP")"
				printf '%s\n' "$buero_head" >"$BUERO_STAMP"
			else
				BUERO_WARN+=("warning: buero: buero setup failed; the next install.sh run retries it")
			fi
			# doctor prints one `ok <what>` or `FAIL <what>: <why>` line per check and exits
			# non-zero when one fails; only the FAIL lines need the reader's attention.
			while IFS= read -r buero_line; do
				BUERO_WARN+=("warning: buero doctor: $buero_line")
			done < <(cd "$BUERO_DIR" && "$BUERO_BIN" doctor 2>&1 | grep '^FAIL' || true)
		else
			BUERO_WARN+=("warning: buero: cargo install failed; the next install.sh run retries it")
		fi
	fi
fi

if [ -z "$(ls -A "$BACKUP")" ]; then
	echo "installed, no conflicts"
else
	echo "installed, backup at $BACKUP"
	echo
	echo "== local modifications replaced (was in \$HOME -> repo) =="
	(cd "$BACKUP" && find . -type f -print) | while IFS= read -r rel; do
		rel="${rel#./}"
		# A replaced file may have come from either overlay. Check the host dir too,
		# otherwise anything the overlay installs reports as "not a regular file in
		# repo" and the diff — the whole point of the backup report — is lost.
		if [ -f "$SRC/$rel" ]; then
			diff -u --label "home/$rel" --label "repo/$rel" "$BACKUP/$rel" "$SRC/$rel" || true
		elif [ -f "$HOST_DIR/$rel" ]; then
			diff -u --label "home/$rel" --label "repo/${HOST_DIR#"$SRC"/}/$rel" "$BACKUP/$rel" "$HOST_DIR/$rel" || true
		else
			echo "# $rel: replaced in \$HOME (not a regular file in repo)"
		fi
	done
fi

if [ "$SPEC_FAILED" = 1 ]; then
	echo
	echo "warning: could not clone/update $SPEC_REPO into $SPEC_DIR"
	echo "it is private, so this needs an SSH key with access (README §SSH-Keys)."
	echo "re-run install.sh once the key is in place; nothing else was affected."
fi

if [ "${#BUERO_WARN[@]}" -gt 0 ]; then
	echo
	printf '%s\n' "${BUERO_WARN[@]}"
fi

stale=()
for prior in "$HOME"/.dotfiles-backup-*; do
	[ -d "$prior" ] || continue
	[ "$prior" = "$BACKUP" ] && continue
	stale+=("$prior")
done
if [ "${#stale[@]}" -gt 0 ]; then
	echo
	echo "warning: ${#stale[@]} older backup dir(s) still hold unresolved content:"
	printf '  %s\n' "${stale[@]}"
	echo "run 'dotfiles-resolve <dir>' on each, or delete if obsolete."
fi
