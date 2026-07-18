#!/usr/bin/env bash
# Dracula tmux status theme — vendored, self-contained, no plugin manager.
#
# This is the sei40kr/tmux-airline-dracula theme, inlined here as plain tmux
# directives after that repo was archived (read-only) in 2018; .tmux.conf runs
# it via run-shell. There is no TPM plugin or external clone to break.
#
# The pane/message/window segments below use the modern tmux >= 2.9 `-style`
# form. Do NOT reintroduce the pre-2.9 split options (pane-border-fg,
# message-bg, message-command-fg, window-status-*-attr, …): tmux removed them
# in 2.9 and they now error as "invalid option" on current tmux. A 2018-era
# reset did exactly that and broke the bar (af2b0b7, see #49). `status-bg`
# below is intentional — a still-valid compatibility alias, not a removed one.

main() {

  ## Colors
  black='colour16'
  white='colour255'
  gray='colour236'
  dark_gray='colour236'
  yellow='colour215'
  light_purple='colour141'
  dark_purple='colour61'

  ## Icons
  left_sep=''
  right_sep=''
  right_alt_sep=''

  tmux set-option -g status on
  tmux set-option -g status-left-length 100
  tmux set-option -g status-right-length 100
  tmux set-option -g status-bg "${dark_gray}"
  tmux set-option -g pane-active-border-style "fg=${dark_purple}"
  tmux set-option -g pane-border-style "fg=${gray}"
  tmux set-option -g message-style "fg=${white},bg=${gray}"
  tmux set-option -g message-command-style "fg=${white},bg=${gray}"
  tmux set-option -g status-left " #I #[fg=${dark_gray},reverse]${right_sep} "
  tmux set-option -g status-left-style "fg=${white},bg=${dark_purple},bold"
  tmux set-option -g status-right "${left_sep}#[bg=${black},reverse] %Y-%m-%d %H:%M "
  tmux set-option -g status-right-style "fg=${light_purple},bg=${dark_gray}"
  tmux set-window-option -g window-status-activity-style "fg=${white},bg=${gray}"
  tmux set-window-option -g window-status-separator ''
  tmux set-window-option -g window-status-format ' #I #W '
  tmux set-window-option -g window-status-style "fg=${yellow},bg=${dark_gray}"
  tmux set-window-option -g window-status-current-format \
    "${right_sep}#[fg=${black}] #I ${right_alt_sep} #W #[fg=${dark_gray},reverse]${right_sep}"
  tmux set-window-option -g window-status-current-style "fg=${dark_gray},bg=${light_purple}"
}

main
