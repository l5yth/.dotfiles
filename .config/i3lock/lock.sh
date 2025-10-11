#!/bin/bash

# This script customizes the lock screen colors. It prefers i3lock-color for
# advanced styling, but gracefully falls back to vanilla i3lock with reduced
# options when i3lock-color is unavailable.

set -euo pipefail

setxkbmap -layout us -option compose:ralt

ALPHA='dd'
SELECTION='#44475a'
ORANGE='#ffb86c'
RED='#ff5555'
MAGENTA='#ff79c6'
BLUE='#6272a4'
GREEN='50fa7b'

LOCK_ARGS=()

if command -v i3lock-color >/dev/null 2>&1; then
  LOCK_BIN="$(command -v i3lock-color)"
  LOCK_ARGS=(
    "--insidever-color=${SELECTION}${ALPHA}"
    "--insidewrong-color=${SELECTION}${ALPHA}"
    "--inside-color=${SELECTION}${ALPHA}"
    "--ringver-color=${GREEN}${ALPHA}"
    "--ringwrong-color=${RED}${ALPHA}"
    "--ring-color=${BLUE}${ALPHA}"
    "--line-uses-ring"
    "--keyhl-color=${MAGENTA}${ALPHA}"
    "--bshl-color=${ORANGE}${ALPHA}"
    "--separator-color=${SELECTION}${ALPHA}"
    "--verif-color=${GREEN}"
    "--wrong-color=${RED}"
    "--modif-color=${RED}"
    "--layout-color=${BLUE}"
    "--date-color=${BLUE}"
    "--time-color=${BLUE}"
    "--screen"
    "1"
    "--blur"
    "3"
    "--clock"
    "--indicator"
    "--time-str=%H:%M:%S"
    "--date-str=%e.%m.%Y"
    "--verif-text=Checking..."
    "--wrong-text=Wrong"
    "--noinput=No input"
    "--lock-text=Locking..."
    "--lockfailed=Lock failed"
    "--radius=120"
    "--ring-width=10"
    "--pass-media-keys"
    "--pass-screen-keys"
    "--pass-volume-keys"
  )
elif command -v i3lock >/dev/null 2>&1; then
  LOCK_BIN="$(command -v i3lock)"
  LOCK_ARGS=(
    "-c"
    "${SELECTION#'#'}"
  )
else
  echo "Neither i3lock-color nor i3lock was found in PATH." >&2
  exit 127
fi

exec "$LOCK_BIN" "${LOCK_ARGS[@]}"
