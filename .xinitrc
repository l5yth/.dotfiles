#!/bin/sh

export XDG_CURRENT_DESKTOP=GNOME
export XDG_SESSION_TYPE=x11

dbus-update-activation-environment --systemd --all

exec /usr/bin/i3

