# Gorilla Unleashed 157.0 (macOS)

### What this is

Gorilla Unleashed for old Intel Macs on macOS 10.13 High Sierra (built for the 2011 MacBook Air, 4 GB, 1366x768). It is based on Momiji 157, a Firefox kept alive for old macOS, with Gorilla's own Mac changes on top.

### Should you download it

Yes, if you used the earlier [MacBook Air build](https://github.com/gorillanobakaa-dot/gorilla-firefox/releases/tag/macbook-air): this one replaces it. On Linux or Windows, take Gorilla Unleashed 160.0 instead.

### Why it matters

The app no longer names Mozilla in its identity: it is Gorilla Unleashed from Gorilla, and the Mozilla updater and DMG helper are no longer listed in it.

| File | Bytes | SHA-256 |
|---|---|---|
| `Gorilla-Unleashed-157.0-mac-x86_64.zip` | 126,924,188 | `513e03e150baee5e795e8fe3d1801dbf3423228e37930a21ffc918748c7bebb5` |
| `patches-mac.tar.xz` | 26,483,176 | `ce242403fa7155a33836456d2d9f5edb0e6dba1f1edfe796b1753b72a44abf8a` |

`SHA256SUMS` lists the same numbers, computed from these exact files.

---
# In plain language: everything in this release

This is the complete explanation, not a summary of one. Nothing below is behind a link.

<!-- plain-language track: in full, on this page -->

### What changed, in plain words

**1. Gorilla's own name inside the app.** macOS now sees the app as Gorilla Unleashed, made by Gorilla (bundle ID `org.gorilla.unleashed`). The earlier build still named Mozilla there, and listed Mozilla's updater and DMG helper. Those are gone.

**2. Everything else is the earlier MacBook Air build.** Same thin, clear text (Segoe UI with greyscale smoothing), pages sized for an 11-inch screen, the same privacy decisions as the Linux and Windows versions.

**Why it is 157 and not 160:** nobody keeps Firefox 160 alive for macOS 10.13 yet. The newest Momiji is a 158 beta. This build stays on Momiji 157 until a newer stable one exists.

#### Will it run on my Mac?

| Your Mac | Runs? |
|---|---|
| MacBook Air 2011, macOS 10.13.6 | The earlier build of the same series was tested there; THIS build is not tested on the Air yet (see below) |
| Intel Mac 2011 or newer, macOS 10.13 or newer | Should, not tested |
| Apple Silicon (M1 and newer) | Only through Rosetta |

#### Install

1. Download `Gorilla-Unleashed-157.0-mac-x86_64.zip` and check it: `shasum -a 256 -c SHA256SUMS`.
2. Unzip, drag **Gorilla Unleashed.app** into **Applications**.
3. First start: the app is not signed by Apple. Right-click, **Open**, **Open**. Newer macOS: System Settings > Privacy & Security > **Open Anyway**.

#### Not checked yet (honest list)

- This exact build has NOT been installed or started on the MacBook Air: the Air was offline when it was published. The checks below ran on the build machine only.

---

# For developers: how it works, and how to check it

Written for someone who will audit, fork or change the code. It covers the same release as the plain-language part above; neither is a summary of the other.

<!-- developer track: in full, on this page -->

### For developers

- Base: Momiji `v157.0-mj`, commit `189d295392c5` (github.com/aobaharuki2005/firefox). Route A: Momiji plus our Mac series, 16 patches (`patches-mac.tar.xz`, sha256 pinned in `macos-legacy/patches-mac.sha256`, gorilla-firefox PR 25). New since the earlier Mac release: `Mac: no Mozilla in the app's identity` (owner decision 2026-10-23).
- Built on Linux with `macos-legacy/recreate-mac.sh all` (Apple SDK pinned by Mozilla, Mozilla's toolchain, Sandy Bridge, no `-march=native`). `fieldkit macair preflight`: `VERDICT READY TO BUILD` (every Mac decision in the source). The script's own check: `PASS: every Mach-O is x86_64 with minimum macOS <= 10.13`, `VERDICT READY`.
- Not run for this build: `fieldkit macair install` and `fieldkit macair verify` on the Air (the stroke and LCD-colour measurement), heat runs.
- Build it yourself: `bash macos-legacy/recreate-mac.sh` on a 64-bit Linux PC.
