# Accent

A personal accent picker for Linux and macOS, derived from
[QuickAccent by Victor Masson](https://github.com/victormasson/QuickAccent).
The original Git history, MIT license, and third-party notices are preserved.

Hold a letter, choose an accent with Space/arrows, then release to insert.
On Linux, select **Long press, Space and arrows** in Settings to open the
picker automatically after the configured hold delay. Escape cancels.

## Desktop integration

On Omarchy, Accent's picker and settings follow the active desktop palette,
including changes while windows are open. The **Á** bar widget opens settings
on click. Right-click for pause/start, restart, and automatic startup controls.
The plugin source is in `dist/omarchy`.

The executable is `accent`, the user service is `accent.service`, and
configuration lives at `~/.config/accent/config.toml`. Use `accent --settings`
to open settings, or `systemctl --user restart accent` to restart the service.

## Build

Build the personal source rather than installing upstream QuickAccent binaries:

```sh
cargo test --all-targets --locked
cargo build --release --locked
INSTALL_FROM_SOURCE=1 ./dist/linux/install.sh
```

The source installer requires the standard Rust/Linux build dependencies and
keyboard/uinput permissions. It installs the user service and desktop launcher.
For systems with GPU device-loss errors, set `ICED_BACKEND=tiny-skia` in the
Accent service environment to use its built-in software renderer.

See [character mappings](docs/CHARACTERS.md) for available language sets.
