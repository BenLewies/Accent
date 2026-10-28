# Contributing

Small, focused pull requests are welcome after publication. Explain the user-visible
problem and include reproduction steps. Run `cargo test --all-targets --locked`,
`python3 -m unittest discover -s tests`, and `python3 scripts/check_distribution.py`.
Manual checks: quiet service startup, explicit settings launch, keyboard release and
cancellation, desktop theme changes, and plugin pause/start. Do not capture real typing
in logs. Preserve upstream attribution and third-party notices in source and packages.
Contributions are accepted under the repository's MIT license. Do not add telemetry,
unrequested privileged actions, or dependency downloads to the bar plugin.
