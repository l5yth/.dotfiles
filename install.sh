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

BACKUP=$(mktemp -d "$HOME/.dotfiles-backup-XXXXXX")
trap 'rmdir "$BACKUP" 2>/dev/null || true' EXIT

rsync -avh \
	--backup --backup-dir="$BACKUP" \
	--exclude='.git/' \
	--exclude='.github/' \
	--exclude='.gitignore' \
	--exclude='.gitmodules' \
	--exclude='README.md' \
	--exclude='LICENSE' \
	--exclude='CLAUDE.md' \
	--exclude='install.sh' \
	"$SRC"/ "$HOME"/

if [ -z "$(ls -A "$BACKUP")" ]; then
	echo "installed, no conflicts"
else
	echo "installed, backup at $BACKUP"
fi
