# Accent on macOS

## Install (prebuilt, no Rust)

Clone the release tag and run the installer from it. It downloads the asset
for that same tag, verifies it against `SHA256SUMS` (and the Sigstore
attestation when `gh` is logged in), and stops on any mismatch:

```bash
git clone --branch v1.3.0 --depth 1 https://github.com/BenLewies/Accent
Accent/dist/macos/install.sh
open ~/Applications/Accent.app
```

Grant **Accessibility** (System Settings → Privacy & Security → Accessibility).
If a stale Accent entry is already listed (an older install), remove it
and add the new one — the grant is bound to the bundle's code signature.

Always launch through Launch Services (`open`, Finder, or a LaunchAgent that
runs `open`). If launchd execs `Contents/MacOS/accent` directly, macOS
ignores the Accessibility grant and the app logs `Failed to create CGEventTap`.

Downloads `Accent-macos-universal.tar.gz` from the rolling [`continuous`](https://github.com/BenLewies/Accent/releases/tag/continuous) release (arm64 + x86_64).

| Env | Default |
|-----|---------|
| `GITHUB_REPO` | `BenLewies/Accent` |
| `ACCENT_VERSION` | `continuous` |
| `PREFIX` | `~/Applications` |
| `INSTALL_FROM_SOURCE` | `0` |

## Start at login

```bash
cp dist/macos/com.accent.app.plist ~/Library/LaunchAgents/
# edit the app path inside if you installed to ~/Applications
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.accent.app.plist
```

Logs go to `/tmp/accent.log` / `/tmp/accent.err`. Stop with
`launchctl bootout gui/$(id -u)/com.accent.app`.

## Homebrew (from source)

```bash
brew install --HEAD ./dist/brew/Formula/accent.rb
```

## From source

```bash
INSTALL_FROM_SOURCE=1 ./dist/macos/install.sh
# or
cargo build --release
```
