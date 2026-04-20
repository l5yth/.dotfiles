#!/usr/bin/env bash
set -euo pipefail

SRC="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"

if [ "$SRC" = "$HOME" ]; then
	echo "install.sh: refusing to run with repo at \$HOME ($HOME)" >&2
	exit 1
fi

if [ -d "$SRC/.git" ]; then
	git -C "$SRC" submodule update --init --recursive
fi

BACKUP=$(mktemp -d "$HOME/.dotfiles-backup-$(date +%Y%m%d-%H%M%S)-XXXX")

rsync -avh \
	--backup --backup-dir="$BACKUP" \
	--exclude='.git/' \
	--exclude='.gitignore' \
	--exclude='.gitmodules' \
	--exclude='README.md' \
	--exclude='LICENSE' \
	--exclude='install.sh' \
	"$SRC"/ "$HOME"/

rmdir "$BACKUP" 2>/dev/null || true
if [ -d "$BACKUP" ]; then
	echo "installed, backup at $BACKUP"
else
	echo "installed, no conflicts"
fi
