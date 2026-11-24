#!/usr/bin/env bash
# Explicitly invoked by the installer after the user approves device access.
set -euo pipefail
(( EUID == 0 )) || { echo 'Administrator access is required.' >&2; exit 1; }
[[ $# == 0 ]] || { echo 'This helper takes no arguments.' >&2; exit 1; }
install -d -m 755 /etc/udev/rules.d /etc/modules-load.d
for managed in /etc/udev/rules.d/60-accent.rules /etc/modules-load.d/accent.conf; do
    if [[ -e $managed ]]; then
        cp -p -- "$managed" "$managed.accent-backup-$(date +%Y%m%d%H%M%S)"
    fi
done
# logind gives only the active local session access, including after hotplug.
# Do not add every user to the input group or make devices world-writable.
cat > /etc/udev/rules.d/60-accent.rules <<'RULES'
# Managed by Accent. Grant the active local session keyboard and uinput access.
# This file precedes 60-input-id.rules, so identify new event devices first.
SUBSYSTEM=="input", KERNEL=="event*", ENV{ID_INPUT}=="", IMPORT{builtin}="input_id"
SUBSYSTEM=="input", KERNEL=="event*", ENV{ID_INPUT_KEYBOARD}=="1", TAG+="uaccess"
SUBSYSTEM=="misc", KERNEL=="uinput", OPTIONS+="static_node=uinput", TAG+="uaccess"
RULES
printf 'uinput\n' > /etc/modules-load.d/accent.conf
chmod 644 /etc/udev/rules.d/60-accent.rules /etc/modules-load.d/accent.conf
modprobe uinput
udevadm control --reload-rules
udevadm trigger --action=change --subsystem-match=input
udevadm trigger --action=change --subsystem-match=misc --sysname-match=uinput
udevadm settle --timeout=15
