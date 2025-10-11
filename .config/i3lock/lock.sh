#!/usr/bin/env bash

setxkbmap -layout us -option compose:ralt

ALPHA='dd'
SELECTION='#44475a'
ORANGE='#ffb86c'
RED='#ff5555'
MAGENTA='#ff79c6'
BLUE='#6272a4'
GREEN='50fa7b'

i3lock \
  --insidever-color=$SELECTION$ALPHA \
  --insidewrong-color=$SELECTION$ALPHA \
  --inside-color=$SELECTION$ALPHA \
  --ringver-color=$GREEN$ALPHA \
  --ringwrong-color=$RED$ALPHA \
  --ring-color=$BLUE$ALPHA \
  --line-uses-ring \
  --keyhl-color=$MAGENTA$ALPHA \
  --bshl-color=$ORANGE$ALPHA \
  --separator-color=$SELECTION$ALPHA \
  --verif-color=$GREEN \
  --wrong-color=$RED \
  --modif-color=$RED \
  --layout-color=$BLUE \
  --date-color=$BLUE \
  --time-color=$BLUE \
  --screen 1 \
  --blur 3 \
  --clock \
  --indicator \
  --time-str="%H:%M:%S" \
  --date-str="%e.%m.%Y" \
  --verif-text="Checking..." \
  --wrong-text="Wrong" \
  --noinput="No input" \
  --lock-text="Locking..." \
  --lockfailed="Lock failed" \
  --radius=120 \
  --ring-width=10 \
  --pass-media-keys \
  --pass-screen-keys \
  --pass-volume-keys

