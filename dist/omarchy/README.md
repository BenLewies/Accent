# Accent bar plugin

Install this directory as `~/.config/omarchy/plugins/bjl.accent`, then run:

```sh
omarchy plugin validate ~/.config/omarchy/plugins/bjl.accent
omarchy plugin enable bjl.accent --section right
```

Requires Accent installed as `~/.local/bin/accent` with the `accent.service`
user unit. Left-click **Á** to open settings (starting Accent if paused).
Right-click for pause/start, restart, and automatic startup controls.
The widget and menu use the desktop theme and font. Errors appear in the
menu and tooltip; pausing dims the bar icon. Python 3 and systemd are required.
