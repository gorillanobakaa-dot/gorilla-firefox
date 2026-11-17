# Gorilla Unleashed 160.0

### What this is

Gorilla Unleashed, a Firefox that never calls home, for **Linux, Windows and old Macs**. Every file for every computer is on this page.

### Should you download it

Yes. Pick the file for your computer:

| Your computer | Download | Size |
|---|---|---|
| Linux (Debian, Ubuntu) | `Gorilla-Unleashed-160.0-linux-x86_64.deb` | 111 MB |
| Windows 10 / 11, 64-bit | `Gorilla-Unleashed-160.0-win64.zip` | 136 MB |
| Old Intel Mac, macOS 10.13 High Sierra or newer | `Gorilla-Unleashed-157.0-mac-x86_64.zip` | 127 MB |

The Mac build is 157, not 160: nobody keeps Firefox 160 alive for macOS 10.13 yet (the newest Momiji is a 158 beta).

### Why it matters

Firefox 160 brings Mozilla's newest security fixes, and more AI that Gorilla takes out.

| File | Bytes | SHA-256 |
|---|---|---|
| `Gorilla-Unleashed-160.0-linux-x86_64.deb` | 110,853,028 | `eddf949e1909dc3555bf5c67cee3009d7e440fc4b1383a9c895d69bca00f214e` |
| `Gorilla-Unleashed-160.0-win64.zip` | 135,906,663 | `b54f67e5076be7a0d04288dab377dbbd4182aba6803ec1849013f3f1337090f1` |
| `Gorilla-Unleashed-157.0-mac-x86_64.zip` | 126,924,188 | `513e03e150baee5e795e8fe3d1801dbf3423228e37930a21ffc918748c7bebb5` |
| `patches-mac.tar.xz` | 26,483,176 | `ce242403fa7155a33836456d2d9f5edb0e6dba1f1edfe796b1753b72a44abf8a` |

`SHA256SUMS` lists the same numbers. Each system also has its own page: [Linux](https://github.com/gorillanobakaa-dot/gorilla-firefox/releases/tag/v160.0.0-linux), [Windows](https://github.com/gorillanobakaa-dot/gorilla-firefox/releases/tag/v160.0.0-windows), [macOS](https://github.com/gorillanobakaa-dot/gorilla-firefox/releases/tag/v157.0.0-mac).

---
# In plain language: everything in this release

This is the complete explanation, not a summary of one. Nothing below is behind a link.

<!-- plain-language track: in full, on this page -->

### Linux and Windows: what changed in 160, in plain words

**1. Firefox 160 underneath.** The browser is now built on Firefox 160.0. All the security fixes Mozilla made since 158 are in.

**2. Firefox 160's new AI parts are cut out.** Firefox 160 added more AI: an on-device text generator and an "AI control" switch. In Gorilla, the AI switch is locked to "blocked", and the text-generation code is taken out of the browser completely, so nothing is left to switch back on.

**3. The new tab page works.** A Firefox 160 module that guesses what kind of page you are on (shopping, news) was removed from Gorilla. One leftover line still asked for it, and the new tab page stayed blank. That line is fixed.

**4. Two settings removed.** Firefox 160's "Link preview" and "Highlight to search" settings are gone from Settings: the features behind them are not in Gorilla.

**Still the Gorilla you know:** it never calls home, uBlock Origin is built in and nothing else can be installed, Gorilla.Satellite mode is there for slow and expensive connections, and studies and telemetry are refused.

#### Install on Linux

```bash
sudo apt install ./Gorilla-Unleashed-160.0-linux-x86_64.deb
```

Check the download first, in the folder where you saved both files:

```bash
sha256sum -c SHA256SUMS
```

#### Install on Windows

Unzip `Gorilla-Unleashed-160.0-win64.zip` anywhere (for example `C:\Gorilla`) and start `firefox\firefox.exe`. Nothing is installed into Windows.

Check the download first, in PowerShell, in the folder where you saved it:

```powershell
(Get-FileHash .\Gorilla-Unleashed-160.0-win64.zip -Algorithm SHA256).Hash
```

It must print `B54F67E5076BE7A0D04288DAB377DBBD4182ABA6803EC1849013F3F1337090F1`.

### Old Macs (macOS 10.13): what changed, in plain words

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

### Linux

- Base: Firefox 160.0. Patch set: `gorilla-firefox` master `5f40f3e` (`23.REBASE.160`, `23.REBASE.160.linux`, `21.PORT.FIXES.160`, `22.EGRESS.LOCKDOWN.160`). Checked on the built tree with `git apply --check -R`: every patch of `23.REBASE.160.linux` (3), `21.PORT.FIXES.160` (4) and `22.EGRESS.LOCKDOWN.160` (3) is in; `23.REBASE.160` 115 in, and 4 (`0016`, `0020`, `0047`, `0105`) no longer reverse because later fixes (`21.PORT.FIXES.160/007`, `/005`, `/003`, `22.EGRESS.LOCKDOWN.160/005`) edit the same lines again. `0122` (Windows widget build file) is left out on Linux (owner decision 2026-11-17).
- The full build is from 2026-11-11 (BuildID 20261111185950). Port fixes `005` and `007` are front-end only (JavaScript); they were committed into the port tree on 2026-11-17 and built with `mach build faster`, so the BuildID did not change. Checked in the packaged files: `ASRouterTargeting.sys.mjs` `currentTabPageCategory` returns `null`; `tabs-browsing.mjs` equals the fixed tree.
- Windows: the same set, built on the Windows laptop; the egress lockdown was checked there on the built tree.
- **Not verified for this release, stated instead of hidden:** the install-and-proof run on an installed `.deb` (`build-harness post-install`), the release leak gate (`leakgate --release`), and the claims audit were not run for 160 on Linux. The browser was not started from this package before publishing.

### Windows

- The same Firefox 160 patch set, built on the Windows laptop with `fieldkit emerge run firefox-windows`; port fix `007 v2` (gorilla-firefox PR 24) and the blank-new-tab fix are in. The egress lockdown (`22.EGRESS.LOCKDOWN.160`) was checked there on the built tree (`git apply --check -R`: applied).
- Not verified for this release: the install tier, the release leak gate, and starting the browser from the zip.

### macOS

- Base: Momiji `v157.0-mj`, commit `189d295392c5` (github.com/aobaharuki2005/firefox). Route A: Momiji plus our Mac series, 16 patches (`patches-mac.tar.xz`, sha256 pinned in `macos-legacy/patches-mac.sha256`, gorilla-firefox PR 25). New since the earlier Mac release: `Mac: no Mozilla in the app's identity` (owner decision 2026-10-23).
- Built on Linux with `macos-legacy/recreate-mac.sh all` (Apple SDK pinned by Mozilla, Mozilla's toolchain, Sandy Bridge, no `-march=native`). `fieldkit macair preflight`: `VERDICT READY TO BUILD` (every Mac decision in the source). The script's own check: `PASS: every Mach-O is x86_64 with minimum macOS <= 10.13`, `VERDICT READY`.
- Not run for this build: `fieldkit macair install` and `fieldkit macair verify` on the Air (the stroke and LCD-colour measurement), heat runs.
- Build it yourself: `bash macos-legacy/recreate-mac.sh` on a 64-bit Linux PC.
