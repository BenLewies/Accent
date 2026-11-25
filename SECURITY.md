# Security and privacy

Accent processes keyboard input locally and can inject characters. On supported
Omarchy installations it uses compositor input-method/virtual-keyboard protocols,
without physical device access or administrator privileges. The bar runs inside
Omarchy’s unsandboxed shell and starts its bundled native program. No executable
is downloaded or built on enablement. No telemetry or typed-text logging is
implemented, and this backend does not use the clipboard. Another active input
method is left in place; Accent reports the conflict rather than replacing it.
The inherited explicit `--evdev` backend still requires device permissions.

Only the current Accent source is maintained here; inherited QuickAccent tags are not
Accent releases. Marketplace listing and static checks are not security certification.

For a suspected vulnerability, use GitHub private vulnerability reporting if the
repository exposes it. Otherwise open an issue containing only a request for a private
reporting channel, not exploit details or sensitive input. Never attach tokens, typed
passwords, full memory dumps, or private clipboard contents.

Review source and bundled executables before enabling a plugin. The retained legacy
device-setup helper is a maintenance tool, is not part of standard installation,
and is never invoked by the widget.

## Inherited lru advisory

The local `vendor/lru` patch backports upstream PR #224 for RUSTSEC-2026-0002
(GHSA-rhfx-m35p-ff5j) to lru 0.12.5. See its ACCENT_PATCH.md for exact provenance.
Version-only scanners may still flag 0.12.5; inspect Cargo.lock and the path patch
rather than treating that registry version as patched. The registry release remains
vulnerable. Remove the backport when the rendering dependency can use lru >= 0.16.3.
