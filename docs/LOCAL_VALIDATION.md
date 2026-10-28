# Local validation — 2026-10-28

- Rust: 127 passed, 4 ignored, 0 failed on Linux x86_64.
- Python bar controller: 4 passed, including action rejection and missing-service state.
- Omarchy root plugin-manifest validation: passed.
- Distribution structure/attribution and shell syntax checks: passed.
- Installed app: service start and repeated --daemon launch leave settings closed;
  explicit --settings opens a mapped Accent window; service remains active.
- Settings screenshot reviewed; captured only Accent, no other application content.
- Linux dependency notices: 345 dependency packages bundled; canonical-text fallbacks
  are labeled with their declarations/authors when upstream omits a notice file.
- Upstream LICENSE and its Victor Masson copyright remain unchanged.

## Marketplace policy preflight

Engine repository: https://github.com/omacom/omarchy-plugin-marketplace
Engine commit: `ab9cc55ed21a4a561ef56f9052fa6a750e95ca5d`
Policy version: 3
Local outcome: **review-required**
Deterministic findings: **0**
Capabilities: service-management, privilege, installer, package-manager.

This was a local working-tree policy preflight, not the official remote snapshot
resolver, full marketplace validation, or an exact-commit approval. It conveys no
Verified status. The official scan and maintainer decision remain required.

## Remaining external gates

Repository visibility is still private. No marketplace submission has been sent.
Fresh public validation, owner approval of the submission checklist, a reviewed
binary release and green cross-platform CI remain publication gates. macOS was not
run locally. Adoption and marketplace acceptance cannot be guaranteed.
