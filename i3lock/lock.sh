#!/bin/bash

setxkbmap -layout us -option compose:ralt
PICTURE=$HOME/.config/i3lock/i3lock.png
scrot $PICTURE
convert $PICTURE -blur "5x4" $PICTURE
i3lock -i $PICTURE
rm $PICTURE
sleep 1
