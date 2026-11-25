# Accent bar plugin

Install the root repository with Omarchy’s standard command:

```sh
omarchy plugin add https://github.com/BenLewies/Accent --enable
```

The matching Linux x86_64 runtime and dependency notices are included in
`runtime/linux-x86_64/`. The widget owns its native process and releases it on
unload. No system service, build, runtime download or device permission setup is
required. Python 3, busctl and the other desktop libraries are supplied by Omarchy.

Left-click Á for settings. Right-click for pause/start, restart and automatic
startup. All six button themes plus Match operating system are retained; Aurora
glass is the default. Theme and typing preferences remain in the Accent config.

The fixed-action controller uses bounded subprocess calls without shell
interpolation. First startup migrates only the known legacy Accent user service.
Hyprland allows one input method per seat: an active competing tool is reported
and left running. See the root README and docs/INSTALL.md for details.
