# Release and marketplace readiness

## Prepared in source

- One root `manifest.json`; permanent ID `bjl.accent`, outside the reserved namespace.
- Root README covers installation, removal, dependencies, permissions, limits and support.
- An original settings screenshot in root `preview.png`; no listing/verification badges.
- Searchable settings sections and explicit quiet service mode.
- MIT copyright/permission text unchanged; attribution in NOTICE.md and About.
- Microsoft, Unicode and vendored rdev notices preserved; notices included in Linux
  release archives, macOS bundles, and source installations.
- Pinned workflow actions, bounded job timeouts, read-only CI permissions and explicit
  release publication; Rust tests, controller tests and distribution checks in CI.
- Per-target dependency-notice generation reads registry notices and recovers missing
  texts from recorded source commits. Where upstream supplies no notice file, the
  bundle labels canonical SPDX text separately and preserves package author metadata;
  unresolved license declarations stop packaging. Review these exceptions before release.
- Reviewable listing draft in MARKETPLACE_SUBMISSION.md; no submission has been sent.

## Must complete before publishing

1. Owner approves making `BenLewies/Accent` public; it remains private for now.
2. Owner reviews attribution, preview ownership, permissions and every submission checkbox.
3. CI must pass on the final commit on Linux and macOS. Local Linux results do not
   establish macOS support. Inspect Actions logs and fix failures before tagging.
4. Create/test the first Accent release (planned 1.4.0); inherited QuickAccent tags
   are not Accent binary releases. Verify checksums, notices, startup and an install
   in a fresh user environment. Do not advertise an AUR listing: none exists for Accent.
5. Arch/brew recipes are inherited packaging references, not published distribution
   channels. Refresh Arch's source version and checksum against a verified Accent
   release before promoting that recipe; never substitute SKIP.
6. Re-check global plugin-ID availability immediately before submission. The registry
   contained no `bjl.accent` when locally checked on 2026-10-28; this is not a reservation.
7. Submit the owner-approved issue using the official format. Marketplace validation,
   a fresh exact-commit baseline and an explicit maintainer `approved-and-verified`
   decision are required. A local scan is not a listing guarantee.

The static baseline intentionally requires human review for the installer and service
capabilities. Do not remove truthful permissions documentation to avoid review, and
never add a Verified badge without the marketplace's actual status.

## Reproduce local checks

```sh
cargo test --all-targets --locked
python3 -m unittest discover -s tests
python3 scripts/check_distribution.py
omarchy plugin validate .
bash -n dist/linux/install.sh dist/macos/install.sh
```

Manual checks: service restart opens no settings; a second `accent --daemon` opens
no window; `accent --settings` opens a single window; search filters language sets;
closing settings leaves the daemon active; bar status and settings action work.

References (reviewed 2026-10-28):
- https://github.com/omacom/omarchy-plugin-marketplace/blob/main/SUBMISSION.md
- https://github.com/omacom/omarchy-plugin-marketplace/blob/main/SECURITY.md
- https://opensource.org/license/mit

## Preparation update — 2026-11-02

- GitHub still reports PRIVATE; no Accent GitHub releases exist.
- The existing commit `7ec947098e670de3a86883586d52ba8ca7ca7bc8` passed
  Linux and macOS CI (run 40664406271). The new preparation changes still need CI.
- Live marketplace registry checked: `bjl.accent` does not occur, including in
  retired-ID data. This is not a reservation; check again immediately before submission.
- README benefit-led copy, setup FAQ and original vector banner prepared.
- Release notes no longer advertise the nonexistent Accent AUR package; install
  commands explicitly select the release tag. Generated v1.4.0 notes checked locally.
- Launch copy and GitHub metadata suggestions are in [LAUNCH_KIT.md](LAUNCH_KIT.md).
- Local controller tests (4), distribution checks, Omarchy validation, installer
  shell syntax and whitespace checks passed. No application source changed;
  Rust tests and fresh desktop/manual installation were not rerun for this preparation.
- Current marketplace submission contract re-read; the existing six headings,
  category, tags and checklist text still match. No issue, tag or release created.
