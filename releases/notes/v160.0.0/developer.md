## Linux

- Base: Firefox 160.0. Patch set: `gorilla-firefox` master `5f40f3e` (`23.REBASE.160`, `23.REBASE.160.linux`, `21.PORT.FIXES.160`, `22.EGRESS.LOCKDOWN.160`). Checked on the built tree with `git apply --check -R`: every patch of `23.REBASE.160.linux` (3), `21.PORT.FIXES.160` (4) and `22.EGRESS.LOCKDOWN.160` (3) is in; `23.REBASE.160` 115 in, and 4 (`0016`, `0020`, `0047`, `0105`) no longer reverse because later fixes (`21.PORT.FIXES.160/007`, `/005`, `/003`, `22.EGRESS.LOCKDOWN.160/005`) edit the same lines again. `0122` (Windows widget build file) is left out on Linux (owner decision 2026-11-17).
- The full build is from 2026-11-11 (BuildID 20261111185950). Port fixes `005` and `007` are front-end only (JavaScript); they were committed into the port tree on 2026-11-17 and built with `mach build faster`, so the BuildID did not change. Checked in the packaged files: `ASRouterTargeting.sys.mjs` `currentTabPageCategory` returns `null`; `tabs-browsing.mjs` equals the fixed tree.
- Windows: the same set, built on the Windows laptop; the egress lockdown was checked there on the built tree.
- **Not verified for this release, stated instead of hidden:** the install-and-proof run on an installed `.deb` (`build-harness post-install`), the release leak gate (`leakgate --release`), and the claims audit were not run for 160 on Linux. The browser was not started from this package before publishing.

## Windows

- The same Firefox 160 patch set, built on the Windows laptop with `fieldkit emerge run firefox-windows`; port fix `007 v2` (gorilla-firefox PR 24) and the blank-new-tab fix are in. The egress lockdown (`22.EGRESS.LOCKDOWN.160`) was checked there on the built tree (`git apply --check -R`: applied).
- Not verified for this release: the install tier, the release leak gate, and starting the browser from the zip.

## macOS

- Base: Momiji `v157.0-mj`, commit `189d295392c5` (github.com/aobaharuki2005/firefox). Route A: Momiji plus our Mac series, 16 patches (`patches-mac.tar.xz`, sha256 pinned in `macos-legacy/patches-mac.sha256`, gorilla-firefox PR 25). New since the earlier Mac release: `Mac: no Mozilla in the app's identity` (owner decision 2026-10-23).
- Built on Linux with `macos-legacy/recreate-mac.sh all` (Apple SDK pinned by Mozilla, Mozilla's toolchain, Sandy Bridge, no `-march=native`). `fieldkit macair preflight`: `VERDICT READY TO BUILD` (every Mac decision in the source). The script's own check: `PASS: every Mach-O is x86_64 with minimum macOS <= 10.13`, `VERDICT READY`.
- Not run for this build: `fieldkit macair install` and `fieldkit macair verify` on the Air (the stroke and LCD-colour measurement), heat runs.
- Build it yourself: `bash macos-legacy/recreate-mac.sh` on a 64-bit Linux PC.
