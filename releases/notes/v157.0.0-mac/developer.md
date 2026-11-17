## For developers

- Base: Momiji `v157.0-mj`, commit `189d295392c5` (github.com/aobaharuki2005/firefox). Route A: Momiji plus our Mac series, 16 patches (`patches-mac.tar.xz`, sha256 pinned in `macos-legacy/patches-mac.sha256`, gorilla-firefox PR 25). New since the earlier Mac release: `Mac: no Mozilla in the app's identity` (owner decision 2026-10-23).
- Built on Linux with `macos-legacy/recreate-mac.sh all` (Apple SDK pinned by Mozilla, Mozilla's toolchain, Sandy Bridge, no `-march=native`). `fieldkit macair preflight`: `VERDICT READY TO BUILD` (every Mac decision in the source). The script's own check: `PASS: every Mach-O is x86_64 with minimum macOS <= 10.13`, `VERDICT READY`.
- Not run for this build: `fieldkit macair install` and `fieldkit macair verify` on the Air (the stroke and LCD-colour measurement), heat runs.
- Build it yourself: `bash macos-legacy/recreate-mac.sh` on a 64-bit Linux PC.
