#!/usr/bin/env bash
# Install Accent.app from GitHub Releases (universal binary).
set -euo pipefail

REPO="${GITHUB_REPO:-BenLewies/Accent}"
ASSET="Accent-macos-universal.tar.gz"
SUMS="SHA256SUMS"
APP_DIR="${PREFIX:-$HOME/Applications}"
# Run from a checkout (./dist/macos/install.sh). Without a source tree the
# release asset carries everything.
if [[ -n "${BASH_SOURCE[0]:-}" ]]; then
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd 2>/dev/null || true)"
else
  ROOT=""
fi

# Release to install. Default: the version of the checkout you run this from;
# `latest` = newest stable, `continuous` = rolling build, or a tag such as v1.2.0.
if [[ -n "${ACCENT_VERSION:-}" ]]; then
  RELEASE_TAG="$ACCENT_VERSION"
elif [[ -n "$ROOT" && -f "$ROOT/Cargo.toml" ]]; then
  RELEASE_TAG="v$(sed -n 's/^version = "\(.*\)"/\1/p' "$ROOT/Cargo.toml" | head -1)"
else
  RELEASE_TAG="latest"
fi

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "error: this installer is for macOS" >&2
  exit 1
fi

tmpdir="$(mktemp -d)"
cleanup() { rm -rf "$tmpdir"; }
trap cleanup EXIT

release_url() {
  if [[ "$RELEASE_TAG" == "latest" ]]; then
    echo "https://github.com/${REPO}/releases/latest/download/$1"
  else
    echo "https://github.com/${REPO}/releases/download/${RELEASE_TAG}/$1"
  fi
}

# The archive is only extracted after its sha256 matches the SHA256SUMS file
# published with the release. ACCENT_SKIP_VERIFY=1 bypasses this for
# releases older than v1.2.0, which shipped no checksum file.
verify_release() {
  if [[ "${ACCENT_SKIP_VERIFY:-0}" == "1" ]]; then
    echo "warning: ACCENT_SKIP_VERIFY=1, checksum not verified" >&2
    return 0
  fi
  if ! curl -fsSL "$(release_url "$SUMS")" -o "$tmpdir/$SUMS"; then
    echo "error: $SUMS not found for $RELEASE_TAG; refusing to install an unverified asset." >&2
    echo "       (ACCENT_SKIP_VERIFY=1 to override for pre-1.2.0 releases)" >&2
    exit 1
  fi
  echo "==> Verify sha256"
  local expected actual
  expected="$(grep " $ASSET\$" "$tmpdir/$SUMS" | awk '{print $1}')"
  actual="$(shasum -a 256 "$tmpdir/$ASSET" | awk '{print $1}')"
  [[ -n "$expected" && "$expected" == "$actual" ]] \
    || { echo "error: sha256 mismatch for $ASSET" >&2; exit 1; }
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    echo "==> Verify build provenance"
    gh attestation verify "$tmpdir/$ASSET" --repo "$REPO" \
      || { echo "error: build provenance verification failed" >&2; exit 1; }
  else
    echo "    (install + login to gh to also verify the Sigstore attestation)"
  fi
}

fetch_release() {
  echo "==> Download $(release_url "$ASSET")"
  curl -fsSL "$(release_url "$ASSET")" -o "$tmpdir/$ASSET" || return 1
  verify_release
}

build_from_source() {
  echo "==> Build from source"
  if [[ -z "${ROOT:-}" || ! -f "$ROOT/Cargo.toml" ]]; then
    echo "error: source tree not found; clone the repo or set ROOT." >&2
    exit 1
  fi
  command -v cargo >/dev/null || { echo "error: install Rust (https://rustup.rs/)" >&2; exit 1; }
  (cd "$ROOT" && cargo build --release --locked)
  APP="$tmpdir/Accent.app"
  mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
  (cd "$ROOT" && python3 scripts/bundle_notices.py --target "$(rustc -vV | sed -n 's/^host: //p')" --output "$APP/Contents/Resources/RUST_DEPENDENCY_LICENSES.txt")
  cp "$ROOT/target/release/accent" "$APP/Contents/MacOS/accent"
  cp "$ROOT/LICENSE" "$ROOT/NOTICE.md" "$ROOT/THIRD_PARTY_NOTICES.md" "$APP/Contents/Resources/"
  chmod +x "$APP/Contents/MacOS/accent"
  if [[ -f "$ROOT/dist/macos/Accent.app/Contents/Info.plist" ]]; then
    cp "$ROOT/dist/macos/Accent.app/Contents/Info.plist" "$APP/Contents/Info.plist"
  fi
  if [[ -f "$ROOT/dist/macos/AppIcon.icns" ]]; then
    cp "$ROOT/dist/macos/AppIcon.icns" "$APP/Contents/Resources/AppIcon.icns"
  fi
}

if [[ "${INSTALL_FROM_SOURCE:-0}" == "1" ]]; then
  build_from_source
  APP_SRC="$tmpdir/Accent.app"
else
  if fetch_release; then
    tar -xzf "$tmpdir/$ASSET" -C "$tmpdir"
    APP_SRC="$(find "$tmpdir" -maxdepth 2 -type d -name 'Accent.app' | head -1)"
    [[ -n "$APP_SRC" ]] || { echo "error: Accent.app missing from archive" >&2; exit 1; }
  else
    echo "warning: download failed; falling back to source build" >&2
    build_from_source
    APP_SRC="$tmpdir/Accent.app"
  fi
fi

echo "==> Install to $APP_DIR"
mkdir -p "$APP_DIR"
rm -rf "$APP_DIR/Accent.app"
cp -R "$APP_SRC" "$APP_DIR/Accent.app"

# TCC binds the Accessibility grant to the bundle's code signature. An
# unsigned bundle (older releases, source builds) has no stable requirement,
# so the toggle silently never applies. Ad-hoc sign unless already valid.
if ! codesign --verify --strict "$APP_DIR/Accent.app" 2>/dev/null; then
  echo "==> Ad-hoc sign $APP_DIR/Accent.app"
  codesign --force --sign - "$APP_DIR/Accent.app"
fi

echo
echo "Installed $APP_DIR/Accent.app"
echo "  • Grant Accessibility: System Settings → Privacy & Security → Accessibility"
echo "    (if a stale Accent entry is listed, remove it and add this one)"
echo "  • Launch: open \"$APP_DIR/Accent.app\""
echo "    Always start it through Launch Services (open / Finder / a LaunchAgent"
echo "    running open); exec'ing Contents/MacOS/accent directly makes TCC"
echo "    ignore the Accessibility grant."
echo "  • Start at login: see dist/macos/README.md"
echo "  • Or brew from source: brew install --HEAD ./dist/brew/Formula/accent.rb"
