# Release and marketplace readiness

1. Run Rust tests, Python controller/legacy maintenance tests, bar theme checks,
   distribution checks and `omarchy plugin validate .`.
2. Build and strip the Linux x86_64 runtime. Generate dependency notices, then
   `scripts/bundle_runtime.py --binary … --notices …`. Commit the executable,
   complete notices and BUILD.json. `--check` must pass after all source changes.
3. Test in an isolated Hyprland desktop with `/dev/input` and `/dev/uinput` absent:
   quick typing/rollover, Space/arrows, long press, Shift, grid/cancel, Unicode,
   hot reload, competing input method and immediate input recovery on termination.
4. Test the root plugin on a clean profile with no Accent binary, service, config,
   build toolchain, root helper or keyboard-device permissions. Enable, open settings,
   type, pause/resume, disable, re-enable and remove. Test migration separately.
5. Verify both Wayland and XWayland text entry, including a terminal.
6. Confirm themes and existing preferences survive normal plugin updates; new
   profiles use Aurora glass. Verify process ownership on reload and multiple bars.
7. Push only after local checks pass. Require Linux/macOS CI on the final commit.
   Local Linux testing does not establish macOS runtime compatibility.
8. Publish the versioned release with checksums and source/build records. Keep
   all inherited and dependency copyright/licence notices intact.
9. Prepare exact-commit installation evidence for marketplace review. The curated
   Manual Setup override remains until the maintainers approve its removal. Do not
   describe the ordinary mutable-upstream command as installing a reviewed SHA.

The standard plugin includes a native executable and handles keyboard input. Those
capabilities require truthful documentation and may require marketplace maintainer
review. A baseline/approval is not a security audit or future-code guarantee.
