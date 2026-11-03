# Prepared marketplace submission

Title: **[Plugin]: Accent**

Draft only. Review the five statements below before submission. The public-repository
and owner-confirmation boxes are deliberately unchecked while the repository is
private and the owner has not approved submission. Use the exact body below only
after all five statements are true. No issue has been submitted.

---

### Repository URL

https://github.com/BenLewies/Accent

### Category

Productivity

### Tags

bar, hyprland, quickshell

### Suggest a missing tag

_No response_

### Maintainer notes

Accent helps users type accented names, multilingual text and symbols without
memorizing compose sequences. Hold a letter, choose a character and keep typing.
Language selection, theme-aware settings and bar controls make it fit Omarchy.

Accent is an independent MIT-licensed derivative of Victor Masson's QuickAccent,
with the original license and attribution preserved. One root manifest exposes
plugin bjl.accent; its QML entry point is dist/omarchy/BarWidget.qml. The preview is
an original screenshot of the Accent settings UI, without third-party window content.

Manual setup is required: the bar controls an Accent user daemon installed separately
from this same repository. The bar neither downloads code nor requests elevation.
The daemon intercepts local keyboard events and injects selected accents through
uinput; installation requests input-group/device-rule setup explicitly. Typing is
not logged or transmitted. Clipboard fallback and keymap-capacity limits are documented.

Local static-policy preflight found no deterministic findings; it requires review of
installer, service-management, privilege and package-manager capabilities. This is
not an official marketplace scan, verification, security audit, or certification.
Please apply the manual-setup designation and review the exact submission commit.

### Submission checklist

- [ ] The repository is public and contains installation and removal instructions.
- [x] I have documented the plugin license and any external dependencies.
- [ ] I confirm that I own or have permission to submit this plugin and its preview assets.
- [x] The plugin does not overwrite user configuration without explicit consent.
- [ ] I understand that approval is for listing and is not a security review.
