# Accent bar controls

The plugin's manifest is at the repository root. Install the complete repository,
not this subdirectory. See ../../README.md for installation and removal instructions.

Left-click **Á** opens settings (starting the daemon if paused). Right-click offers
pause/start, restart and automatic-startup controls. The font follows the Omarchy shell; the icon follows Accent’s chosen theme. Python 3 and a working Accent user service are required. The controller
uses a fixed action allowlist, bounded subprocess calls and no shell interpolation.
The widget does not install the daemon automatically. For the complete supported
path, run `./install.sh` from a reviewed Accent release checkout; this installs the
daemon, dependencies, permissions and bar plugin together. `./install.sh --check`
checks readiness without changing anything. Missing-daemon errors point to setup.


The bar badge follows **Accent Settings → Appearance**. All six bundled SVG
button designs are included in `assets/themes/`. The default is **03 Aurora
glass**. **Match operating system** uses Omarchy's current colours and follows
live theme switches. Keep `Theme.js` and `assets/` beside `BarWidget.qml`.
