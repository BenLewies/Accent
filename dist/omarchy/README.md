# Accent bar controls

The plugin's manifest is at the repository root. Install the complete repository,
not this subdirectory. See ../../README.md for installation and removal instructions.

Left-click **Á** opens settings (starting the daemon if paused). Right-click offers
pause/start, restart and automatic-startup controls. Theme and font come from the
Omarchy shell. Python 3 and a working Accent user service are required. The controller
uses a fixed action allowlist, bounded subprocess calls and no shell interpolation.
It does not install the daemon automatically. Missing-daemon errors point to setup.
