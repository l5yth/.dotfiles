# Dracula-inspired tmux status theme inspired by vim-airline

set -g status on
set -g status-left-length 100
set -g status-right-length 100
set -g status-bg colour236
set -g pane-active-border-fg colour61
set -g pane-border-fg colour236
set -g message-bg colour236
set -g message-fg colour255
set -g message-command-bg colour236
set -g message-command-fg colour255
set -g status-left ' #I #[fg=colour236,reverse] '
set -g status-left-style 'fg=colour255,bg=colour61,bold'
set -g status-right '#[bg=colour16,reverse] %Y-%m-%d %H:%M '
set -g status-right-style 'fg=colour141,bg=colour236'
setw -g window-status-activity-style 'fg=colour255,bg=colour236'
setw -g window-status-separator ''
setw -g window-status-format ' #I #W '
setw -g window-status-style 'fg=colour215,bg=colour236'
setw -g window-status-current-format '#[fg=colour16] #I  #W #[fg=colour236,reverse]'
setw -g window-status-current-style 'fg=colour236,bg=colour141'
