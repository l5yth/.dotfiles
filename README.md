# .dotfiles

Arch Linux dotfiles for a Dracula-themed i3 desktop.

## Base

```bash
sudo pacman -S base base-devel linux linux-firmware dhcpcd iwd curl unzip zsh vim xorg xorg-xinit i3 dex ttf-dejavu man-pages man-db dmenu polkit xdg-utils nodejs npm rustup python git rsync fasd fzf tmux zsh-syntax-highlighting openssh keychain pass pinentry ruby btop terminator cronie zsh-autosuggestions nmap ufw zsh-completions
sudo systemctl enable --now dhcpcd iwd cronie ufw
git clone --recursive https://github.com/l5yth/.dotfiles.git ~/.dotfiles
rm -rf ~/.dotfiles/.gi* ~/.dotfiles/RE* ~/.dotfiles/LI*
rsync -avh ~/.dotfiles/ $HOME/
rm -rf ~/.dotfiles/
chsh -s /usr/bin/zsh
source $HOME/.zshrc
```

## Extras

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash
nvm install lts/krypton
npm install --global pure-prompt yarn lerna npm serve pm2
sudo pacman -S mtr dysk fastfetch github-cli asciiquarium cmatrix sl
git clone https://aur.archlinux.org/pikaur.git && pushd pikaur && makepkg -fsri && popd && rm -rf pikaur/
pikaur -S claude-code pipes.sh lsu-git psn-git pass-secret-service
```

## Desktop

```bash
sudo pacman -S syncthing hplip cups cups-pdf brightnessctl bluez bluez-utils pipewire pipewire-alsa pipewire-pulse pipewire-jack wireplumber alsa-utils ranger ttf-fira-code noto-fonts noto-fonts-emoji papirus-icon-theme scrot okular shotwell caja engrampa meld code obsidian signal-desktop element-desktop speedcrunch firefox thunderbird protonmail-bridge eom libreoffice-fresh vlc pavucontrol pasystray krita
sudo systemctl enable --now bluetooth
systemctl --user enable --now syncthing pipewire wireplumber
pikaur -S i3lock-color xidlehook brave-bin enpass-bin sublime-text-4 pinta
```

## SSH-Keys

```bash
chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
ssh-keygen -t ed25519 -C "$USER@$HOST-$(date +%F)"
```

## Proton Mail

Requires a GPG key; import yours or run `gpg --full-generate-key`.

```bash
pass init <GPG-KEY-ID>
protonmail-bridge-core --cli
# >>> login
# >>> info     # shows IMAP/SMTP host + bridge password for Thunderbird
# >>> exit
systemctl --user enable --now protonmail-bridge
```
