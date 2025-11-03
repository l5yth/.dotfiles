#!/usr/bin/env bash
# Pick comfortable i3 fonts based on the tallest connected display.
set -euo pipefail

DEFAULT_FONT="pango:DejaVu Sans Mono 12"
SMALL_FONT="pango:DejaVu Sans Mono 10"
TINY_FONT="pango:DejaVu Sans Mono 7"

# Allow overriding via arguments from the i3 config.
if [[ "${1-}" != "" ]]; then
    DEFAULT_FONT=$1
fi
if [[ "${2-}" != "" ]]; then
    SMALL_FONT=$2
fi
if [[ "${3-}" != "" ]]; then
    TINY_FONT=$3
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

determine_font() {
    # Print the font that should be used based on the maximum detected screen
    # height. We favour the tiniest readable font on very small displays to
    # keep the status bar compact.
    local font="$DEFAULT_FONT"
    if [[ "$max_height" =~ ^[0-9]+$ ]] && (( max_height > 0 )); then
        if (( max_height < 780 )); then
            font="$TINY_FONT"
        elif (( max_height < 1080 )); then
            font="$SMALL_FONT"
        fi
    fi
    printf '%s' "$font"
}

read_bar_ids() {
    # Emit the configured i3 bar identifiers, falling back to an empty list if
    # they cannot be discovered at runtime.
    local config_json config_text
    if ! command -v i3-msg >/dev/null 2>&1; then
        return 1
    fi

    config_json=$(i3-msg -t get_config 2>/dev/null) || return 1
    if [[ -z "$config_json" ]]; then
        return 1
    fi

    if command -v python3 >/dev/null 2>&1; then
        config_text=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["config"])' <<<"$config_json" 2>/dev/null) || return 1
    else
        return 1
    fi

    local in_bar=0 brace_depth=0 current_id
    while IFS= read -r line; do
        if (( !in_bar )) && [[ "$line" =~ ^[[:space:]]*bar[[:space:]]*\{ ]]; then
            in_bar=1
            brace_depth=0
            current_id=""
        fi

        if (( in_bar )); then
            if [[ "$line" =~ ^[[:space:]]*id[[:space:]]+([^[:space:]]+) ]]; then
                current_id="${BASH_REMATCH[1]}"
            fi

            local stripped="${line%%#*}"
            local braces="${stripped//[^{}]/}"
            local opens="${braces//\}/}"
            local closes="${braces//\{/}"

            (( brace_depth += ${#opens} - ${#closes} ))

            if (( brace_depth <= 0 )); then
                in_bar=0
                brace_depth=0
                if [[ -n "$current_id" ]]; then
                    printf '%s\n' "$current_id"
                fi
                current_id=""
            fi
        fi
    done <<<"$config_text"
}

apply_font_to_bars() {
    # Ensure every discovered i3 bar uses the same font as the window chrome so
    # the status bar shrinks together with the rest of the UI on old screens.
    local font="$1" bar_ids=() id

    while IFS= read -r id; do
        bar_ids+=("$id")
    done < <(read_bar_ids || true)

    if (( ${#bar_ids[@]} == 0 )); then
        bar_ids=("bar-0")
    fi

    for id in "${bar_ids[@]}"; do
        i3-msg "bar $id font $font" >/dev/null || true
    done
}

font_to_use=$(determine_font)

i3-msg "font $font_to_use" >/dev/null
apply_font_to_bars "$font_to_use"
