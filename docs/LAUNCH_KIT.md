# Accent launch kit

Prepared 2026-11-02. Copy is ready for review; publish only after the repository
and tested release are publicly available. No announcement has been sent.

## Positioning

**Give every word its accent.**

Accent helps Omarchy users type accented names, multilingual text and symbols
without memorizing compose sequences. Hold a letter, choose a character, and keep
typing. Its picker and settings follow the desktop theme, with service controls
in the bar.

Primary audience: Omarchy and Hyprland users who regularly type names or words
in more than one language. Lead with the typing benefit, then show customization.

## GitHub About

Description: Accents and symbols without breaking your flow. A character picker
with theme-aware settings and bar controls for Omarchy and Hyprland.

Suggested topics: omarchy, hyprland, wayland, linux, accents, unicode,
keyboard, productivity, rust, quickshell.

Use `assets/accent-banner.svg` for README branding and the supplied 1280 × 640
PNG for GitHub's social preview. Keep root `preview.png` as the actual settings
screenshot for the marketplace. The banner is an illustration, not an app screenshot.

## Marketplace

Name: Accent
Category: Productivity
Tags: bar, hyprland, quickshell
Permanent ID: bjl.accent

Short description: Type accents and symbols without breaking your flow. Hold a
letter, choose a character, and keep typing on Omarchy.

Use the exact submission body in MARKETPLACE_SUBMISSION.md. Omaplug is the
plugin manager; discovery/listing is through the Omarchy plugin marketplace.
Request manual-setup classification because the daemon is installed separately.

## Launch announcement

Give every word its accent.

Accent brings a character picker to Omarchy: hold a letter, choose its accent,
and keep typing. Write café, señor and über with your existing keyboard.

Choose the language sets you use, match your desktop colors, and pause or restart
Accent from the bar. Processing stays local, with no account or analytics.

The bar plugin requires a separate Accent daemon installation and keyboard-device
permissions. Setup, source and known limitations:
https://github.com/BenLewies/Accent

Independent MIT-licensed derivative of Victor Masson's QuickAccent.

Do not add “available in Omaplug” or “verified” until the marketplace actually lists
and approves the relevant snapshot.

## Suggested demo sequence

Record a clean editor containing only demonstration text. Show a held e and the
picker, insert é to finish café, then show language selection and desktop colors.
Finish on the bar's pause/start controls. Record actual behavior; do not simulate
latency or app compatibility. This shot list is a plan, not a completed recording.

## Release sequence

1. Review this change set and the submission checklist with the owner.
2. Commit/push the final source and run CI on that commit. Previous green CI is
   evidence for its own commit only.
3. Run the documented manual typing checks and test installation in a fresh user
   environment. Create and inspect v1.4.0 packages, notices and checksums.
4. Make the repository public with owner authorization. Confirm anonymous access
   to source and assets; update README publication status to match reality.
5. Recheck ID availability, then submit the approved body. Wait for marketplace
   validation and maintainer approval; retain manual-setup disclosure.
6. Announce the public release using the copy above. Update listing/verification
   language only after confirming the live marketplace state.
