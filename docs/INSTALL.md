# Installation and troubleshooting

## Source build on Arch / Omarchy

Review the checkout before building. Install the Rust toolchain and native build
dependencies through your normal package-management workflow. Typical Arch packages:
`base-devel rust pkgconf libxkbcommon libxkbcommon-x11 libevdev wayland fontconfig
alsa-lib libx11 libxi libxtst libxcursor libxrandr libxinerama mesa`.
Use `omarchy pkg add` for system packages. Building needs internet access to fetch
Cargo.lock dependencies on its first run. Python 3 is also required to bundle
dependency notices; missing registry notices are retrieved as text from the crate’s
recorded GitHub commit before packaging. No downloaded license content is executed.

From the repository:

```sh
cargo test --all-targets --locked
INSTALL_FROM_SOURCE=1 ./dist/linux/install.sh
```

Installation writes `~/.local/bin/accent`, a user service, launcher, icons and license
notices. It configures udev/uinput and `input` group membership using explicit sudo
prompts. It does not install the bar plugin automatically. Use the README plugin
command or, for a local checkout, copy the complete repository under
`~/.config/omarchy/plugins/bjl.accent`, validate it and enable that ID.

The service uses `--daemon`, which suppresses development demo windows and prevents
background launches from bringing up settings. The desktop launcher uses `--settings`.

## Troubleshooting

- Check `systemctl --user status accent` and `journalctl --user -u accent -n 50`.
- Verify group membership with `id`; restart the login session after permissions change.
- If settings crash with a GPU device-loss error, create a service override via
  `systemctl --user edit accent` containing `[Service]` and
  `Environment=ICED_BACKEND=tiny-skia`, then restart Accent.
- If the bar says the daemon is missing, install it; the bar never installs code automatically.
- If a rare symbol fails, reduce enabled sets. Only a limited set of characters fits
  the spare-key mapping; overflow uses clipboard paste and may fail in terminals.
- To stop keyboard interception immediately: `systemctl --user stop accent`.

## Removal

First follow the README removal commands. Optional leftovers are the renderer override
under `~/.config/systemd/user/accent.service.d`, icons named `accent` beneath
`~/.local/share/icons/hicolor`, notices beneath `~/.local/share/licenses/accent`, and
configuration beneath `~/.config/accent`. Preserve configuration if you may reinstall.

The installer owns `/etc/udev/rules.d/60-accent.rules`. Remove it with administrator
approval if no longer needed, then reload udev rules. Do not remove shared input-group
membership, `/dev/uinput`, or shared uinput module configuration blindly. Accent's
runtime `accent:accents` keyboard option disappears when desktop settings are reloaded;
remove only Accent-generated XKB files if you no longer need them. Other apps' rules,
services, and settings must remain untouched.
