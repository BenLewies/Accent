# Security and privacy

Accent intercepts keyboard input locally and can inject characters. The daemon needs
input-device permissions; the bar widget runs within Omarchy's unsandboxed shell and
controls only `accent.service` through the user service manager. Its operations are
fixed allowlisted arguments, not arbitrary shell strings. No telemetry or typed-text
logging is implemented. Clipboard fallback can change clipboard contents.

Only the current Accent source is maintained here; inherited QuickAccent tags are not
Accent releases. Marketplace listing and static checks are not security certification.

For a suspected vulnerability, use GitHub private vulnerability reporting if the
repository exposes it. Otherwise open an issue containing only a request for a private
reporting channel, not exploit details or sensitive input. Never attach tokens, typed
passwords, full memory dumps, or private clipboard contents.

Review installation scripts before running them. Privilege is requested during manual
installation for device rules and group membership, never from a plugin click.

## Inherited lru advisory

The local `vendor/lru` patch backports upstream PR #224 for RUSTSEC-2026-0002
(GHSA-rhfx-m35p-ff5j) to lru 0.12.5. See its ACCENT_PATCH.md for exact provenance.
Version-only scanners may still flag 0.12.5; inspect Cargo.lock and the path patch
rather than treating that registry version as patched. The registry release remains
vulnerable. Remove the backport when the rendering dependency can use lru >= 0.16.3.
