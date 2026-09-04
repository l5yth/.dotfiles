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
if ! command -v git >/dev/null; then
	if [ -d "$SRC/.git" ]; then
		echo "install.sh: git required (this is a clone; submodules and hooks need it)" >&2
		exit 1
	fi
	echo "install.sh: git not found, skipping spec clone" >&2
fi

if [ -d "$SRC/.git" ]; then
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
rsync -avh \
	--backup --backup-dir="$BACKUP" \
	--exclude='.git/' \
	--exclude='.github/' \
	--exclude='.githooks/' \
	--exclude='.gitignore' \
	--exclude='.gitmodules' \
	--exclude='/CLAUDE.md' \
	--exclude='LICENSE' \
	--exclude='README.md' \
	--exclude='SPEC.md' \
	--exclude='ACCEPTANCE.md' \
	--exclude='install.sh' \
	--exclude='.claude/settings.local.json' \
	--exclude='.claude/.credentials.json' \
	--exclude='.claude/history.jsonl' \
	--exclude='.claude/projects/' \
	--exclude='.claude/sessions/' \
	"$SRC"/ "$HOME"/

if [ -z "$(ls -A "$BACKUP")" ]; then
	echo "installed, no conflicts"
else
	echo "installed, backup at $BACKUP"
	echo
	echo "== local modifications replaced (was in \$HOME -> repo) =="
	(cd "$BACKUP" && find . -type f -print) | while IFS= read -r rel; do
		rel="${rel#./}"
		if [ -f "$SRC/$rel" ]; then
			diff -u --label "home/$rel" --label "repo/$rel" "$BACKUP/$rel" "$SRC/$rel" || true
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
