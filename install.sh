#!/usr/bin/env bash
set -euo pipefail

command -v rsync >/dev/null || { echo "install.sh: rsync required" >&2; exit 1; }

SRC="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"

if [ "$SRC" = "$HOME" ]; then
	echo "install.sh: refusing to run with repo at \$HOME ($HOME)" >&2
	exit 1
fi

if [ -d "$SRC/.git" ]; then
	git -C "$SRC" submodule update --init --recursive
fi

for prior in "$HOME"/.dotfiles-backup-*; do
	[ -d "$prior" ] || continue
	rmdir "$prior" 2>/dev/null || true
done

BACKUP=$(mktemp -d "$HOME/.dotfiles-backup-XXXXXX")
trap 'rmdir "$BACKUP" 2>/dev/null || true' EXIT

rsync -avh \
	--backup --backup-dir="$BACKUP" \
	--exclude='.claude/' \
	--exclude='.git/' \
	--exclude='.github/' \
	--exclude='.gitignore' \
	--exclude='.gitmodules' \
	--exclude='CLAUDE.md' \
	--exclude='LICENSE' \
	--exclude='README.md' \
	--exclude='install.sh' \
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
