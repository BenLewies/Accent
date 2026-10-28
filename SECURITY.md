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
