#!/usr/bin/env bash
set -euo pipefail

DEFAULT_FONT="pango:DejaVu Sans Mono 12"
SMALL_FONT="pango:DejaVu Sans Mono 10"

# Allow overriding via arguments from the i3 config.
if [[ "${1-}" != "" ]]; then
    DEFAULT_FONT=$1
fi
if [[ "${2-}" != "" ]]; then
    SMALL_FONT=$2
fi

max_height=0
if command -v xrandr >/dev/null 2>&1; then
    # shellcheck disable=SC2016
    max_height=$(xrandr --current | awk '
        / connected/ {connected = ($2 == "connected")}
        connected && $1 ~ /^[0-9]+x[0-9]+/ {
            split($1, res, "x")
            if (res[2] > max) {
                max = res[2]
            }
        }
        END { print max }
    ')
fi

if [[ "$max_height" =~ ^[0-9]+$ ]] && (( max_height > 0 && max_height < 1080 )); then
    i3-msg "font $SMALL_FONT" >/dev/null
else
    i3-msg "font $DEFAULT_FONT" >/dev/null
fi
