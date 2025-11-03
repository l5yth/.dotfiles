# .dotfiles

Minimal Arch Linux dotfiles for a Dracula-themed i3 desktop.

## Contents

- `.bin/` – helper scripts for storage checks, scratch directories, and chat launchers.
- `.config/` – i3 window manager, i3status bar, terminal, and editor preferences.
- `.tmux.conf`, `.tmux/` – tmux configuration and Dracula status line theme.
- `.vimrc`, `.vim/` – Vim defaults with Dracula colors and airline.
- `.zsh*` – Zsh prompt, history, and plugin setup (Pure, fasd, autosuggestions, syntax highlighting).

## Installation

```bash
sudo pacman -S base base-devel linux linux-firmware amd-ucode dhcpcd iwd curl zsh vim xorg xorg-xinit i3 ttf-dejavu man-pages man-db dmenu polkit xdg-utils nodejs npm git rsync fasd fzf tmux zsh-syntax-highlighting openssh keychain ruby btop terminator cronie zsh-autosuggestions
sudo systemctl enable --now dhcpcd iwd cronie
git clone --recursive https://github.com/l5yth/.dotfiles.git ~/.dotfiles
rm -rf ~/.dotfiles/.gi* ~/.dotfiles/RE* ~/.dotfiles/LI*
rsync -avh ~/.dotfiles/ $HOME/
rm -rf ~/.dotfiles/
chsh -s /usr/bin/zsh
source $HOME/.zshrc
```

## Extras

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
nvm install lts/krypton
npm install --global pure-prompt yarn lerna npm bower serve pm2 @github/copilot @openai/codex
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
sudo pacman -S syncthing ttf-fira-code noto-fonts noto-fonts-emoji adwaita-icon-theme cups cups-pdf brightnessctl bluez bluez-utils pipewire pipewire-alsa pipewire-pulse pipewire-jack wireplumber alsa-utils ranger okular shotwell scrot caja meld mtr code obsidian hplip signal-desktop speedcrunch firefox thunderbird eom dysk
systemctl --user enable --now pipewire wireplumber syncthing@"$USER"
sudo systemctl enable --now bluetooth
git clone https://aur.archlinux.org/pikaur.git && cd pikaur && makepkg -fsri
pikaur -S i3lock-color brave-bin enpass-bin sublime-text-4 neofetch pinta
```

## Credits

- pure prompt: https://github.com/sindresorhus/pure
- fasd: https://github.com/clvv/fasd
- fzf: https://github.com/junegunn/fzf
- dracula: https://github.com/dracula/vim
- vim-airline: https://github.com/vim-airline/vim-airline
- tmux-airline-dracula: https://github.com/sei40kr/tmux-airline-dracula
- zsh-syntax-highlighting: https://github.com/zsh-users/zsh-syntax-highlighting
