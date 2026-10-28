# Accent backport

Base: crates.io lru 0.12.5, with its original LICENSE preserved.
Fix: https://github.com/jeromefroe/lru-rs/pull/224
Upstream merge: 62be24c96137fcf5c6323607ff15ed878b157ee2
Advisory: RUSTSEC-2026-0002 / GHSA-rhfx-m35p-ff5j.

Both IterMut directions now create a shared key reference via as_ptr(), rather
than a temporary exclusive key reference that invalidates the map's shared pointer.
Value references remain mutable. Added forward/reverse lookup regression coverage.
This is a local backport, not a claim that registry lru 0.12.5 is fixed. Remove it
when iced's dependency graph can use upstream lru >= 0.16.3. Ordinary unit tests
exercise behavior; they are not a substitute for the upstream Stacked Borrows analysis.
