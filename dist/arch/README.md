# Accent on Arch / Omarchy (AUR)

`accent-bin` packages the prebuilt tarball of a tagged release. The
tarball is pinned by sha256 in the PKGBUILD, and every release asset carries
a Sigstore build-provenance attestation you can check independently:

```bash
gh attestation verify accent-linux-x86_64.tar.gz --repo BenLewies/Accent
```

## Install

```bash
yay -S accent-bin           # or: omarchy pkg add accent-bin
sudo usermod -aG input "$USER"   # then reboot once
systemctl --user enable --now accent
```

## Remove

```bash
systemctl --user disable --now accent
sudo pacman -Rns accent-bin
sudo gpasswd -d "$USER" input    # optional
```

## Publishing a new version (maintainer)

After `git tag vX.Y.Z && git push origin vX.Y.Z` has produced the release:

```bash
cd dist/arch
sed -i "s/^pkgver=.*/pkgver=X.Y.Z/; s/^pkgrel=.*/pkgrel=1/" PKGBUILD
updpkgsums                          # pacman-contrib: pins the tarball sha256
makepkg --printsrcinfo > .SRCINFO
namcap PKGBUILD && makepkg -sfi     # build + install locally to test
```

Then push `PKGBUILD`, `accent.install` and `.SRCINFO` to the AUR
repository (`ssh://aur@aur.archlinux.org/accent-bin.git`).
