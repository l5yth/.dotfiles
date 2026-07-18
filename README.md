# .dotfiles

Arch Linux dotfiles for a Dracula-themed i3 desktop.

## Base

```bash
sudo pacman -S base base-devel linux linux-firmware dhcpcd iwd curl unzip zsh vim xorg xorg-xinit i3 dex man-pages man-db dmenu polkit xdg-utils rustup python git rsync zoxide fzf tmux zsh-syntax-highlighting openssh keychain pass pinentry ruby btop terminator cronie zsh-autosuggestions nmap ufw zsh-completions
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo systemctl enable --now dhcpcd iwd cronie ufw
git clone --recursive https://github.com/l5yth/.dotfiles.git ~/.dotfiles
~/.dotfiles/install.sh
dotfiles-resolve
chsh -s /usr/bin/zsh
source $HOME/.zshrc
```

CPU microcode: pick one based on your CPU.

```bash
grep -m1 '^vendor_id' /proc/cpuinfo
sudo pacman -S intel-ucode   # Intel only
sudo pacman -S amd-ucode     # AMD only
```

## Extras

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash
nvm install lts/krypton
nvm install-latest-npm
npm install --global yarn serve pm2
sudo pacman -S mtr dysk fastfetch github-cli asciiquarium cmatrix sl nerd-fonts ttf-dejavu ttf-fira-code noto-fonts noto-fonts-emoji
rustup default stable
cd "$(mktemp -d)" && git clone https://aur.archlinux.org/pikaur.git && cd pikaur && makepkg -fsri
pikaur -S pipes.sh lsu-git psn-git pass-secret-service
```

## Sandbox only

```bash
pikaur -S claude-code
```

## Desktop

```bash
sudo pacman -S syncthing hplip cups cups-pdf brightnessctl autorandr bluez bluez-utils pipewire pipewire-alsa pipewire-pulse pipewire-jack wireplumber alsa-utils ranger papirus-icon-theme scrot okular shotwell caja engrampa meld code obsidian signal-desktop element-desktop speedcrunch firefox thunderbird protonmail-bridge protonmail-bridge-core eom libreoffice-fresh vlc pavucontrol pasystray krita xdg-desktop-portal xdg-desktop-portal-gtk mate-utils
sudo systemctl enable --now bluetooth syncthing@$USER
systemctl --user enable --now pipewire wireplumber
pikaur -S i3lock-color xidlehook xrandr-invert-colors brave-bin enpass-bin sublime-text-4 pinta
( crontab -l 2>/dev/null | grep -vF 'wttr-fetch' ; echo "*/15 * * * * $HOME/.config/i3status/wttr-fetch" ) | crontab -
```

## SSH-Keys

```bash
chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
ssh-keygen -t ed25519 -N "" -C "$USER@$HOST-$(date +%F)"
```
<!--
# To drop the passphrase on an existing key instead:
ssh-keygen -p -N "" -f ~/.ssh/id_ed25519
-->

## GPG / Pass / Proton Mail

```bash
mkdir -p ~/.gnupg && chmod -R u=rwX,go= ~/.gnupg
gen_status=$(mktemp)
gpg --batch --generate-key --status-file "$gen_status" <<EOF
%no-protection
Key-Type: EDDSA
Key-Curve: ed25519
Subkey-Type: ECDH
Subkey-Curve: cv25519
Name-Real: pass
Name-Email: pass@$HOST
Expire-Date: 0
%commit
EOF
fpr=$(awk '/^\[GNUPG:\] KEY_CREATED/ {print $4; exit}' "$gen_status")
rm -f "$gen_status"
pass init "$fpr"
systemctl --user restart pass-secret-service

protonmail-bridge-core --cli
# >>> login
# >>> info     # shows IMAP/SMTP host + bridge password for Thunderbird
# >>> exit
systemctl --user enable --now protonmail-bridge
```
