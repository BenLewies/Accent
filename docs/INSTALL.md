# Installation and troubleshooting

## Standard Omarchy installation

Accent 1.5.0 supports Omarchy Quattro on Linux x86_64 with Hyprland’s
`zwp_input_method_manager_v2` and `zwp_virtual_keyboard_manager_v1` interfaces.
The integration has been tested on Hyprland 0.56.2.

Review the public repository, then run:

```sh
omarchy plugin add https://github.com/BenLewies/Accent --enable
```

This clones the complete plugin, including `dist/omarchy/runtime/linux-x86_64/accent`,
its build record and dependency notices. The shell owns the process. Nothing is
built or downloaded on enablement. No device access, input-group membership,
administrator authentication, package installation or reboot is needed.
The executable uses libraries already present on the supported Omarchy desktop.
Only the normal per-user Accent preferences are created.

The standard command follows current upstream HEAD. It does not pin a marketplace
reviewed commit. Review the installed source before enabling code you do not trust.
A marketplace listing or baseline is not a security audit.

Click Á to configure languages, triggers and appearance. New installations use
Aurora glass. Right-click for pause/start, restart and startup preferences.
Automatic startup means “start when this enabled bar plugin loads.” Turning it
off keeps the current session running until paused or the plugin unloads.

## Updates and removal

```sh
omarchy plugin update bjl.accent
omarchy plugin disable bjl.accent
omarchy plugin enable bjl.accent
omarchy plugin remove bjl.accent
```

Updates carry the matching native program. Disabling/removing unloads the owned
process and releases its compositor keyboard grab. Preferences survive in
`~/.config/accent/`, respecting `XDG_CONFIG_HOME` on Linux.
`./install.sh` is a compatibility wrapper for these ordinary plugin commands;
`./install.sh --check` reports runtime readiness without changing anything.

## Migration from 1.4.x

A normal plugin update is sufficient. On first enablement, the controller detects
the former `accent.service` only if its executable is `~/.local/bin/accent`, reads
its automatic-startup preference, and disables/stops that user service. The
plugin then starts its bundled program. No administrator access is used. An
unrelated service with the same name is left alone. Typing, theme and bar placement
preferences are retained. This migration is recorded in `accent/bar.json`.

## Compatibility

Hyprland permits one input method per seat. Accent cannot share this interface
with an active Fcitx, IBus or another input-method daemon. It reports that conflict
and releases its connection; it does not replace or stop the other tool. Pause the
other tool only if you intend to switch to Accent. The default Omarchy target has
no other active input method.

The native Wayland backend preserves the existing deferred-letter state machine:
quick typing, rollover, Space/arrows, long press, uppercase latching, navigation,
grid selection and cancellation. A separate same-client virtual keyboard types
Unicode directly, including combining sequences and supplementary-plane scripts.
It does not consume clipboard content or install custom desktop XKB options.
Compositor shortcuts remain owned by Hyprland. Applications that identify a field
as password, PIN, hidden text or sensitive input bypass accent selection.

macOS and other Linux desktops retain their existing backends and are outside
this standard Omarchy installation target. `accent --evdev` explicitly selects the
legacy Linux device backend and still requires separately configured device access.
The old `dist/linux/install.py` and `setup-input.sh` remain legacy maintenance tools;
they are not invoked by the plugin or the supported installation command.

## Troubleshooting

- **No icon:** check `omarchy plugin list --json`; enable `bjl.accent` and choose a bar position.
- **Dim icon:** open the controls for the reported error, then restart Accent.
- **Another input method:** see the compatibility note above; no extra permissions will fix this conflict.
- **Missing bundled program:** update/reinstall the complete root repository, not only `dist/omarchy`.
- **Unsupported architecture:** the included runtime currently targets Linux x86_64.
- **Unexpected stopped process:** use Restart Accent; repeated failures stop automatic retries.
- **Protocol availability:** run `dist/omarchy/runtime/linux-x86_64/accent --wayland-probe`
  from the plugin root. It checks protocol globals without taking keyboard control.

Readiness can also be queried locally:

```sh
python3 dist/omarchy/control.py status
```

It distinguishes a responding process from a working input backend and includes a
specific conflict/error message. Runtime messages go to the shell’s process logs;
Accent does not log typed text. Report a minimal reproduction with application,
keyboard layout, trigger mode and Accent/Hyprland versions, without private input.

## Building the bundled runtime

Developers need Rust, a C toolchain and the development libraries listed in CI.
Build from reviewed source; no build is needed by end users:

```sh
cargo test --all-targets --locked
cargo build --release --locked
python3 scripts/bundle_notices.py --target x86_64-unknown-linux-gnu --output RUST_DEPENDENCY_LICENSES.txt
strip target/release/accent
python3 scripts/bundle_runtime.py --binary target/release/accent --notices RUST_DEPENDENCY_LICENSES.txt
python3 scripts/bundle_runtime.py --check
```

`BUILD.json` records version, target, binary SHA-256 and a deterministic digest of
Cargo inputs, Rust sources, assets and vendored source. CI rejects a stale bundle.
The source digest/checksum documents correspondence; it is not a claim of a
bit-for-bit reproducible or independently attested build. Preserve executable mode
and all licence notices when updating the committed runtime.

## Legacy cleanup

The old program, launcher and disabled service may remain after migration. After
confirming the new plugin works, they can be removed:

```sh
rm -f ~/.local/bin/accent ~/.local/share/applications/accent.desktop
rm -f ~/.config/systemd/user/accent.service
systemctl --user daemon-reload
```

Old icons/notices under `~/.local/share` and backups under
`~/.local/state/accent/install-backups/` are optional retained files. Previous
administrator-owned `/etc/udev/rules.d/60-accent.rules` and
`/etc/modules-load.d/accent.conf` are no longer needed by this backend. Remove them
only after checking other tools do not rely on them. Do not remove shared input-group
membership or other tools’ rules. The new plugin never requires those permissions.
