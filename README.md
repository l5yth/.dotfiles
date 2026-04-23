# .dotfiles

Arch Linux dotfiles for a Dracula-themed i3 desktop.

## Base

```bash
sudo pacman -S base base-devel linux linux-firmware dhcpcd iwd curl unzip zsh vim xorg xorg-xinit i3 dex ttf-dejavu man-pages man-db dmenu polkit xdg-utils nodejs npm rustup python git rsync fasd fzf tmux zsh-syntax-highlighting openssh keychain pass pinentry ruby btop terminator cronie zsh-autosuggestions nmap ufw zsh-completions
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo systemctl enable --now dhcpcd iwd cronie ufw
git clone --recursive https://github.com/l5yth/.dotfiles.git ~/.dotfiles
~/.dotfiles/install.sh
dotfiles-resolve
chsh -s /usr/bin/zsh
( crontab -l 2>/dev/null | grep -vF 'wttr-fetch' ; echo "*/15 * * * * $HOME/.config/i3status/wttr-fetch" ) | crontab -
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
npm install --global yarn lerna npm serve pm2
sudo pacman -S mtr dysk fastfetch github-cli asciiquarium cmatrix sl
rustup default stable
cd "$(mktemp -d)" && git clone https://aur.archlinux.org/pikaur.git && cd pikaur && makepkg -fsri
pikaur -S claude-code pipes.sh lsu-git psn-git
```

<!--
Temporary: patched `pass-secret-service-git` build carrying
https://github.com/grimsteel/pass-secret-service/pull/24. Delete this block
and move `pass-secret-service-git` onto the pikaur line above once the PR
merges and the AUR package rebuilds against a grimsteel/main that contains
the fix.
-->

```bash
sudo pacman -Rdd --noconfirm pass-secret-service 2>/dev/null || true
cd "$(mktemp -d)" && git clone https://aur.archlinux.org/pass-secret-service-git.git && cd pass-secret-service-git
curl -fsSLo pr24.patch https://patch-diff.githubusercontent.com/raw/grimsteel/pass-secret-service/pull/24.patch
cat >>PKGBUILD <<'EOF'

# Temporary override to apply grimsteel/pass-secret-service#24 before build.
# Bash keeps the last definition of prepare(); this replaces the upstream one.
prepare() {
  export CARGO_HOME="${srcdir}/.cargo"
  cd "${srcdir}/${_pkgname}"
  patch -p1 < "${startdir}/pr24.patch"
  cargo fetch
  git log > "${srcdir}/git.log"
}
EOF
makepkg -si --noconfirm
```

## Desktop

```bash
sudo pacman -S syncthing hplip cups cups-pdf brightnessctl bluez bluez-utils pipewire pipewire-alsa pipewire-pulse pipewire-jack wireplumber alsa-utils ranger ttf-fira-code noto-fonts noto-fonts-emoji papirus-icon-theme scrot okular shotwell caja engrampa meld code obsidian signal-desktop element-desktop speedcrunch firefox thunderbird protonmail-bridge eom libreoffice-fresh vlc pavucontrol pasystray krita xdg-desktop-portal xdg-desktop-portal-gtk
sudo systemctl enable --now bluetooth
systemctl --user enable --now syncthing pipewire wireplumber
pikaur -S i3lock-color xidlehook xrandr-invert-colors brave-bin enpass-bin sublime-text-4 pinta
```

## SSH-Keys

```bash
chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
ssh-keygen -t ed25519 -C "$USER@$HOST-$(date +%F)"
```

## GPG / Pass / Proton Mail

```bash
mkdir -p ~/.gnupg && chmod 700 ~/.gnupg
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
