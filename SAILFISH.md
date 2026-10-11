# Sailfish OS

Sailfish OS 5.2 setup for the Jolla Phone (2026), on top of these dotfiles.

Run one line at a time.

## Developer mode

1. Settings > Device lock: set a security code.
2. Settings > Developer tools > Developer mode: enable, enter the security code, Accept.

Needs no network and no Jolla account.

## SSH

1. Settings > Developer tools > Remote connection: enable.
2. Set password for SSH and root access: type or generate one, Save.

The password serves both `ssh` and `devel-su`. The phone must be on and unlocked.
While Remote connection is on, sshd accepts logins over USB and WLAN.

```bash
ssh defaultuser@192.168.2.15   # USB: choose "Developer mode" on the phone
ssh defaultuser@<wlan-ip>      # WLAN: address shown under Settings > Developer tools
```

## Terminal

The Terminal app sits at the end of the app grid once Developer mode is on.
`devel-su` opens a root shell, `devel-su <command>` runs one command as root.

```bash
devel-su pkcon refresh
devel-su pkcon install zypper
```

## Dotfiles

```bash
devel-su zypper in -y git rsync gnu-bash vim-enhanced -busybox-symlinks-bash
mkdir -p ~/.src/l5yth
git clone --recursive https://github.com/l5yth/.dotfiles.git ~/.src/l5yth/.dotfiles
~/.src/l5yth/.dotfiles/install.sh
~/.bin/dotfiles-resolve   # only if install.sh reports a backup
```

`install.sh` deploys `~/.ssh/authorized_keys`. Key login works from here on; `devel-su` still takes the password.

## Repositories

```bash
ssu re   # 5.2.x
cd "$(mktemp -d)"
curl -fLO https://repo.sailfishos.org/obs/sailfishos:/chum/5.2_aarch64/noarch/sailfishos-chum-repo-config-0.6.9-1.5.1.bso.noarch.rpm
devel-su pkcon install-local "$PWD"/sailfishos-chum-repo-config-*.rpm
devel-su zypper ref
ssu lr
```

The RPM name changes with rebuilds. List the directory when the download fails.

## Packages

```bash
devel-su zypper in -y zsh gnu-coreutils tmux mce-tools -busybox-symlinks-coreutils harbour-ownkeepass
zypper se zsh                                         # search
```

`zsh`, `tmux` and `harbour-ownkeepass` come from Chum, the others from Jolla.

## Shell

`chsh` is not shipped. `~/.profile` hands over to zsh.

```bash
grep -qs 'exec zsh' ~/.profile || echo 'case $- in *i*) command -v zsh >/dev/null && exec zsh -l ;; esac' >> ~/.profile
grep -qsF '$HOME/.bin' ~/.zshenv || echo 'export PATH="$PATH:$HOME/.bin"' >> ~/.zshenv
grep -qs 'zsh-completions' ~/.zshenv || echo 'fpath=(/usr/share/zsh/plugins/zsh-completions/src $fpath)' >> ~/.zshenv
```
<!--
# To change the login shell instead of the ~/.profile handover:
devel-su usermod -s "$(command -v zsh)" defaultuser
-->

`~/.profile` and `~/.zshenv` are local to the phone. `install.sh` leaves them alone.

## Extras

The dotfiles expect the Arch package paths `/usr/share/fzf` and `/usr/share/zsh/plugins`.

Paste this block whole.

```bash
mkdir -p ~/.bin && cd "$(mktemp -d)"
curl -fLO https://github.com/junegunn/fzf/releases/download/v0.74.4/fzf-0.74.4-linux_arm64.tar.gz
curl -fLO https://github.com/ajeetdsouza/zoxide/releases/download/v0.10.0/zoxide-0.10.0-aarch64-unknown-linux-musl.tar.gz
sha256sum -c - <<'EOF' &&
5d673b849f494f0d64ec471d8640b153ca8849e3846a31da17abdcfce8df6b46  fzf-0.74.4-linux_arm64.tar.gz
f1f16c5d6298d63dee467eedea1cdcd8490e43e493bea43acd416dc9033ef641  zoxide-0.10.0-aarch64-unknown-linux-musl.tar.gz
EOF
for f in *.tar.gz; do tar -xzf "$f"; done &&
install -m755 fzf zoxide ~/.bin/ &&
./fzf --zsh > key-bindings.zsh &&
devel-su install -Dm644 "$PWD/key-bindings.zsh" /usr/share/fzf/key-bindings.zsh
```

```bash
devel-su
umask 022
mkdir -p /usr/share/zsh/plugins && cd /usr/share/zsh/plugins
git clone --depth=1 --branch 0.8.0  https://github.com/zsh-users/zsh-syntax-highlighting
git clone --depth=1 --branch v0.7.1 https://github.com/zsh-users/zsh-autosuggestions
git clone --depth=1 --branch 0.36.0 https://github.com/zsh-users/zsh-completions
exit
```

```bash
git clone --depth=1 --branch v0.40.6 https://github.com/nvm-sh/nvm.git ~/.nvm
rm -f ~/.zcompdump; exec zsh -l
```

```bash
nvm install lts/krypton
node -v
```

nvm needs GNU `ls` from `gnu-coreutils`. Official Node builds need glibc >= 2.28 and libstdc++ >= 6.0.28.

```bash
devel-su zypper in -y gcc gcc-c++
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path
rustc -V && cargo -V
```

```bash
devel-su zypper in -y python3-base
python3 -m venv ~/.venv
source ~/.venv/bin/activate
pip install -U pip cbor2 black pytest meshtastic meshcore-cli rns nomadnet
```

`python` is Python 2.7. Use `python3`.

```bash
devel-su ssu ar openrepos-jimknopfiot https://sailfish.openrepos.net/JimKnopfIoT/personal/main
devel-su ssu ur
devel-su zypper ref
devel-su zypper in -y harbour-xmatic
```

`harbour-xmatic` is a Matrix client. The homeserver needs simplified sliding sync (MSC4186).

## SSH-Keys

Optional. Same as README.md, plus `keychain` from Chum.

```bash
devel-su zypper in keychain
ssh-keygen -t ed25519 -N "" -C "$USER@$HOST-$(date +%F)"
```

## Syncthing

```bash
cd ~/Downloads
curl -fLO https://openrepos.net/sites/default/files/packages/3068/harbour-syncthing-0.1.3-1.aarch64.rpm
rpm -qpl harbour-syncthing-0.1.3-1.aarch64.rpm
rpm -qp --scripts harbour-syncthing-0.1.3-1.aarch64.rpm
devel-su pkcon install-local ~/Downloads/harbour-syncthing-0.1.3-1.aarch64.rpm
systemctl --user enable --now syncthing                     # as defaultuser, not root
/usr/sbin/mcetool --set-suspend-policy=disable_on_charger   # revert: --set-suspend-policy=enabled
```
<!--
# OpenRepos publisher repository instead of the single RPM:
devel-su ssu ar openrepos-ilpianista https://sailfish.openrepos.net/ilpianista/personal/main
devel-su ssu ur
devel-su zypper ref
devel-su zypper in harbour-syncthing
-->

Only while charging, optional. Paste this block whole.

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.bin/syncthing-charger <<'EOF'
#!/bin/sh
apply() {
	case "$1" in
	*"'on'"*) systemctl --user start syncthing ;;
	*) systemctl --user stop syncthing ;;
	esac
}
apply "$(gdbus call --system --dest com.nokia.mce --object-path /com/nokia/mce/request --method com.nokia.mce.request.get_charger_state)"
gdbus monitor --system --dest com.nokia.mce --object-path /com/nokia/mce/signal |
	while read -r line; do
		case "$line" in *charger_state_ind*) apply "$line" ;; esac
	done
EOF
cat > ~/.config/systemd/user/syncthing-charger.service <<'EOF'
[Unit]
Description=Syncthing only while a charger is connected

[Service]
ExecStart=%h/.bin/syncthing-charger
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF
chmod 755 ~/.bin/syncthing-charger
```

```bash
systemctl --user daemon-reload
systemctl --user disable syncthing
systemctl --user enable --now syncthing-charger
systemctl --user is-active syncthing   # charging: active, unplugged: inactive
```

`~/.bin/syncthing-charger` and its unit are local to the phone. `install.sh` leaves them alone.

On the workstation:

```bash
ssh -L 8385:127.0.0.1:8384 defaultuser@192.168.2.15   # then open http://127.0.0.1:8385
```

- Web GUI on the phone: `http://127.0.0.1:8384`.
- Folders: `~/Pictures`, `~/Videos`, `~/Documents`, `~/android_storage`.
- Config: `~/.config/dev.scarpino/harbour-syncthing/syncthing`.
- Android apps keep their files under `~/android_storage`. The Android Syncthing app cannot reach the rest of the home.

## File Browser

From OpenRepos instead of the Jolla Store.

```bash
devel-su zypper rm harbour-file-browser   # only if the Store version is installed
devel-su ssu ar openrepos-ichthyosaurus https://sailfish.openrepos.net/ichthyosaurus/personal/main
devel-su ssu ur
devel-su zypper ref
devel-su zypper in -y harbour-file-browser
```

## Screenshots

Hold Volume Up and Volume Down together for about two seconds. Files land in `~/Pictures/Screenshots`.

## Developer mode off

Keep the Terminal app before switching Developer mode off.

```bash
devel-su zypper in -f fingerterm
zypper se -i fingerterm   # i+ means it stays
```

Settings > Developer tools > Developer mode: off. The Terminal stays; `devel-su` and SSH go.

## Updates

Needs Developer mode for `devel-su`.

```bash
devel-su zypper ref
devel-su zypper up
git -C ~/.src/l5yth/.dotfiles pull --ff-only
~/.src/l5yth/.dotfiles/install.sh
rustup update
~/.venv/bin/pip install -U pip cbor2 black pytest meshtastic meshcore-cli rns nomadnet
nvm install lts/krypton
```

Sailfish OS releases: Settings > Sailfish OS updates.

zypper tracks none of these. Bump versions, tags and hashes above, then rerun the block.

- fzf 0.74.4, zoxide 0.10.0
- zsh-syntax-highlighting 0.8.0, zsh-autosuggestions v0.7.1, zsh-completions 0.36.0: remove the directory, clone the new tag
- nvm v0.40.6
- harbour-syncthing 0.1.3

Pinned on 2026-10-09.
