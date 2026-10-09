# Sailfish OS

Sailfish OS 5.2 setup for the Jolla Phone (2026), on top of these dotfiles.

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
devel-su zypper in git rsync gnu-bash vim-enhanced   # accept: deinstall busybox-symlinks-bash
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
devel-su zypper in zsh gnu-coreutils tmux mce-tools   # accept: deinstall busybox-symlinks-coreutils
zypper se zsh                                         # search
```

`zsh` and `tmux` come from Chum, the others from Jolla.

## Shell

`chsh` is not shipped. `~/.profile` hands over to zsh.

```bash
grep -qs 'exec zsh' ~/.profile || echo 'case $- in *i*) command -v zsh >/dev/null && exec zsh -l ;; esac' >> ~/.profile
grep -qs '.local/bin' ~/.zshenv || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshenv
grep -qs 'zsh-completions' ~/.zshenv || echo 'fpath=(/usr/share/zsh/plugins/zsh-completions/src $fpath)' >> ~/.zshenv
```
<!--
# To change the login shell instead of the ~/.profile handover:
devel-su usermod -s "$(command -v zsh)" defaultuser
-->

`~/.profile` and `~/.zshenv` are local to the phone. `install.sh` leaves them alone.

## Extras

The dotfiles expect the Arch package paths `/usr/share/fzf` and `/usr/share/zsh/plugins`.

```bash
mkdir -p ~/.local/bin && cd "$(mktemp -d)"
curl -fLO https://github.com/junegunn/fzf/releases/download/v0.74.4/fzf-0.74.4-linux_arm64.tar.gz
curl -fLO https://github.com/ajeetdsouza/zoxide/releases/download/v0.10.0/zoxide-0.10.0-aarch64-unknown-linux-musl.tar.gz
sha256sum -c - <<'EOF' &&
5d673b849f494f0d64ec471d8640b153ca8849e3846a31da17abdcfce8df6b46  fzf-0.74.4-linux_arm64.tar.gz
f1f16c5d6298d63dee467eedea1cdcd8490e43e493bea43acd416dc9033ef641  zoxide-0.10.0-aarch64-unknown-linux-musl.tar.gz
EOF
for f in *.tar.gz; do tar -xzf "$f"; done &&
install -m755 fzf zoxide ~/.local/bin/ &&
./fzf --zsh > key-bindings.zsh &&
devel-su install -Dm644 "$PWD/key-bindings.zsh" /usr/share/fzf/key-bindings.zsh
```

```bash
devel-su
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

On the workstation:

```bash
ssh -L 8385:127.0.0.1:8384 defaultuser@192.168.2.15   # then open http://127.0.0.1:8385
```

- Web GUI on the phone: `http://127.0.0.1:8384`.
- Folders: `~/Pictures`, `~/Videos`, `~/Documents`, `~/android_storage`.
- Config: `~/.config/dev.scarpino/harbour-syncthing/syncthing`.
- Android apps keep their files under `~/android_storage`. The Android Syncthing app cannot reach the rest of the home.

## Screenshots

Hold Volume Up and Volume Down together for about two seconds. Files land in `~/Pictures/Screenshots`.

## Updates

zypper tracks none of these. Bump versions, tags and hashes above, then rerun the block.

- fzf 0.74.4, zoxide 0.10.0
- zsh-syntax-highlighting 0.8.0, zsh-autosuggestions v0.7.1, zsh-completions 0.36.0: remove the directory, clone the new tag
- nvm v0.40.6
- harbour-syncthing 0.1.3

Pinned on 2026-10-09.
