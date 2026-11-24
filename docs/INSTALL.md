# Installation and troubleshooting

## Supported complete installation

Accent 1.4.1 supports Omarchy Quattro on Linux x86_64, from an active local Hyprland
session with a working user service manager and Omarchy shell. Run the installer as
your normal desktop user, never with `sudo`:

```sh
git clone --branch v1.4.1 --depth 1 https://github.com/BenLewies/Accent.git
cd Accent
./install.sh
```

Review the checkout before running it. The summary prompt lists the changes. On a
fresh machine the installer uses `omarchy pkg add` for missing packages and requests
administrator authentication for device access. It never fetches and executes an
installer script. Network downloads are limited to the versioned GitHub release;
the archive checksum, package completeness, build commit and program version must
match before user files are replaced. If an authenticated `gh` client is available,
build-provenance verification must also succeed. A failed release download or check
fails visibly; it does not silently switch to a source build or bypass verification.

The installer writes the program to `~/.local/bin/accent`, installs its user service,
launcher, icons and licence notices, and installs/enables `bjl.accent` in Omarchy.
The plugin checkout's remote points to GitHub, not to a temporary or local clone.
Existing local Git changes block replacement. A legacy non-Git Accent plugin is
backed up before replacement. Settings in `~/.config/accent/config.toml` are preserved.

Before reporting success it checks keyboard/uinput access, the enabled user service,
a responding D-Bus daemon with an initialized virtual keyboard, the enabled bar plugin and matching runtime/plugin versions.
The service uses the software renderer by default to avoid GPU-specific startup errors.
No settings window opens during background service startup.

### Keyboard access

Accent reads keyboard devices to recognize held letters and types chosen characters
through a virtual keyboard. The device setup installs these owned system files:

- `/etc/udev/rules.d/60-accent.rules`
- `/etc/modules-load.d/accent.conf`

The rules use logind's `uaccess` tag for keyboard event devices and `/dev/uinput`.
They grant access to the active local session, including hotplugged keyboards,
without world-writable devices or new `input` group membership. The helper loads
uinput and reapplies the rules immediately; no reboot is normally required. Older
input-group membership and unrelated device rules are left alone. Replaced Accent
rule/module files have dated backups alongside them.

Inactive or remote-only sessions cannot satisfy these readiness checks. If access
is still unavailable after setup, installation fails with a clear message rather
than claiming that typing is ready. Log in locally and rerun the installer.

### Source builds

From a reviewed checkout, run:

```sh
./install.sh --from-source
```

The installer adds the Rust toolchain and native build dependencies using Omarchy's
package manager, builds with `Cargo.lock`, bundles dependency notices, and then uses
the same permissions, installation and readiness checks as the prebuilt path. An
initial build requires internet access. Notice text may be fetched from each crate's
recorded GitHub commit; downloaded notice content is never executed.

When installing the plugin into another directory, the source checkout must be
committed so the cloned bar plugin matches the program being built. Installing from
an existing plugin checkout is also supported. The older
`INSTALL_FROM_SOURCE=1 ./dist/linux/install.sh` entry point remains an alias.

## Updates and repairs

Check out the desired release tag in your original clone and run `./install.sh`
again. This keeps the native program and plugin on the same release. A normal
`omarchy plugin update` updates only the bar checkout, so it is not a complete
runtime upgrade. Re-running the same release repairs an incomplete installation.

The installer records source/version metadata in `~/.local/share/accent/BUILD.json`.
Replaced user files and any replaced plugin checkout are retained under
`~/.local/state/accent/install-backups/`. Each backup has a `files.json` mapping the
numbered backups to their original paths.

If an installation step fails after replacement, the installer restores previous
user files, plugin files and service startup state. System packages and device
rules remain installed; rule backups remain beside their managed files in `/etc`.
A cancelled administrator prompt never counts as successful setup.

## Troubleshooting

```sh
./install.sh --check
systemctl --user status accent
journalctl --user -u accent -n 50
```

`--check` reports JSON with a `ready` value and individual checks. It makes no changes
and returns a nonzero exit code if any check fails.

- Run inside your active local Omarchy session, with at least one keyboard connected.
- If the bar or runtime version differs, rerun the complete release installer.
- If a plugin checkout has local changes, commit/stash them before upgrading.
- If a checksum, source-commit or provenance check fails, do not bypass it. Use an
  unmodified checkout of the matching release tag, or explicitly build reviewed source.
- If a rare symbol fails, reduce enabled sets. Characters beyond the spare-key
  capacity use clipboard paste, which may not work in terminals.
- Stop keyboard interception immediately with `systemctl --user stop accent`.

## Removal

Stop the service, remove the bar plugin with `omarchy plugin remove bjl.accent`,
remove `~/.local/bin/accent`, `~/.local/share/applications/accent.desktop` and
`~/.config/systemd/user/accent.service`, then run `systemctl --user daemon-reload`.

Optional user leftovers are the service override directory, icons named `accent`
beneath `~/.local/share/icons/hicolor`, notices beneath
`~/.local/share/licenses/accent`, the build record under `~/.local/share/accent`,
installation backups under `~/.local/state/accent`, and settings under
`~/.config/accent`. Keep settings if you may reinstall.

If Accent is no longer needed, an administrator can remove its two owned system
files listed under Keyboard access and reload udev rules. Reapply the affected
input/misc devices or log out after removing the rule. Do not remove shared uinput
configuration, shared input-group membership, or another application's rules.
An older installer may also have created `/etc/modules-load.d/uinput.conf`; do not
remove that shared file without checking whether another application uses it.

Accent's generated XKB files are under `~/.config/xkb`; remove only Accent-owned
files if no longer needed. The runtime keyboard option disappears when desktop
settings are reloaded. Other applications' rules and settings must remain intact.
