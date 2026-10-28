class Quickaccent < Formula
  desc "Cross-platform accent character picker (macOS menu bar)"
  homepage "https://github.com/BenLewies/Accent"
  license "MIT"

  # Prebuilt universal binary (no Rust): dist/macos/install.sh
  # https://github.com/BenLewies/Accent/releases/tag/continuous

  head "https://github.com/BenLewies/Accent.git", branch: "master"

  # Local source build (no network)
  # head "file:///Users/aclydes/Coding/Accent", using: :git

  depends_on "rust" => :build
  depends_on :macos

  def install
    system "cargo", "build", "--release"

    # Install as macOS .app bundle (LSUIElement=true → no Dock icon)
    app = prefix/"Accent.app"
    (app/"Contents/MacOS").mkpath
    (app/"Contents/Resources").mkpath
    cp "target/release/accent", app/"Contents/MacOS/accent"
    cp "dist/macos/AppIcon.icns", app/"Contents/Resources/AppIcon.icns"

    # Write minimal Info.plist (agent app, no Dock icon)
    (app/"Contents/Info.plist").write <<~PLIST
      <?xml version="1.0" encoding="UTF-8"?>
      <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
      <plist version="1.0">
      <dict>
        <key>CFBundleExecutable</key>
        <string>accent</string>
        <key>CFBundleIdentifier</key>
        <string>com.accent.app</string>
        <key>CFBundleName</key>
        <string>Accent</string>
        <key>CFBundleIconFile</key>
        <string>AppIcon</string>
        <key>CFBundlePackageType</key>
        <string>APPL</string>
        <key>CFBundleVersion</key>
        <string>1.3.0</string>
        <key>CFBundleShortVersionString</key>
        <string>1.3.0</string>
        <key>LSUIElement</key>
        <true/>
        <key>LSMinimumSystemVersion</key>
        <string>11.0</string>
      </dict>
      </plist>
    PLIST

    # Ad-hoc sign the bundle so TCC can bind the Accessibility grant to it.
    system "codesign", "--force", "--sign", "-", app
  end

  # Launch via `open` (Launch Services). When launchd execs the binary
  # directly, TCC ignores the Accessibility grant and the event tap fails.
  # `open` returns immediately, so no keep_alive.
  service do
    run ["/usr/bin/open", "--stdout", "/tmp/accent.log",
         "--stderr", "/tmp/accent.err",
         "-a", opt_prefix/"Accent.app"]
    run_at_load true
  end

  def caveats
    <<~EOS
      IMPORTANT: Grant Accessibility permission:
        System Settings → Privacy & Security → Accessibility → add
        #{opt_prefix}/Accent.app
        (remove any stale Accent entry from a previous install first).

      Prebuilt (no Rust) alternative, from a clone at a release tag:
        ./dist/macos/install.sh   (verifies the asset against SHA256SUMS)

      To start now and at login:
        brew services start accent

      To stop:
        brew services stop accent

      Logs: /tmp/accent.log and /tmp/accent.err
    EOS
  end

  test do
    assert_match "Accent", shell_output("#{bin}/accent --help 2>&1 || true")
  end
end
