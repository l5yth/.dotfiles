# .dotfiles

Minimal Arch Linux dotfiles.

## Installation

```bash
sudo pacman -S base base-devel linux linux-firmware amd-ucode dhcpcd iwd curl zsh vim xorg xorg-xinit i3 ttf-dejavu man-pages man-db dmenu polkit xdg-utils nodejs npm git rsync fasd fzf tmux zsh-syntax-highlighting openssh keychain ruby btop terminator
sudo systemctl enable --now dhcpcd iwd
sudo npm install --global pure-prompt yarn lerna npm bower serve pm2
git clone --recursive https://github.com/l5yth/.dotfiles.git ~/.dotfiles
rm -rf ~/.dotfiles/.gi* ~/.dotfiles/RE* ~/.dotfiles/LI*
rsync -avh ~/.dotfiles/ $HOME/
rm -rf ~/.dotfiles/
chsh -s /usr/bin/zsh
source $HOME/.zshrc
```

## Extras

```bash
sudo pacman -S syncthing ttf-fira-code noto-fonts noto-fonts-emoji adwaita-icon-theme cups cups-pdf ranger okular shotwell scrot caja meld mtr code obsidian hplip signal-desktop speedcrunch firefox
sudo systemctl enable --now syncthing@"$USER"
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
