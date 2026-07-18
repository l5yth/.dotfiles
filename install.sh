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
	# Git hooks in .git/hooks/ aren't version-controlled; point at the tracked guard.
	git -C "$SRC" config core.hooksPath .githooks
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

# .claude/ now ships as a $HOME overlay (see CLAUDE.md). Excludes keep repo metadata,
# process docs, and any machine-local/state/secret .claude paths out of $HOME; .gitignore
# is the primary guard against committing them — these are deploy-time defense-in-depth.
# The repo-root project file is anchored as '/CLAUDE.md': an unanchored pattern would also
# match the shipped .claude/CLAUDE.md overlay (rsync matches a bare basename at any depth)
# and silently block it from deploying. Full rationale in CLAUDE.md §"Claude Code config".
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
