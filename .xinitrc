#!/bin/sh

# Required under bare startx (no display manager): propagate DISPLAY,
# XAUTHORITY, and XDG_CURRENT_DESKTOP to the systemd user manager and
# D-Bus session bus, so xdg-desktop-portal-gtk can start. Without this,
# file open/save dialogs break in Thunderbird, Chrome, ProtonMail Bridge.
export XDG_CURRENT_DESKTOP=GNOME
export XDG_SESSION_TYPE=x11
dbus-update-activation-environment --systemd --all

exec /usr/bin/i3

