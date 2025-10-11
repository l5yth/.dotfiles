# start x if not running

if [[ -z $DISPLAY && ${XDG_VTNR:-0} -eq 1 ]]; then
  if command -v startx >/dev/null 2>&1; then
    exec startx
  fi
fi
