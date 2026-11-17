# Gorilla Unleashed 160.0 (Linux)

### What this is

Gorilla Unleashed 160.0 for Debian and Ubuntu: a Firefox that never calls home, with the AI parts of Firefox 160 cut out.

### Should you download it

Yes, if you run Gorilla 158 on Linux: this replaces it. The Windows build has its own release page.

### Why it matters

Firefox 160 brings Mozilla's newest security fixes, and more AI that Gorilla takes out.

Firefox 160.0 (stable) based. Debian/Ubuntu `.deb`, 64-bit. BuildID **`20261111185950`**.

After you install, open **Help > About Gorilla Unleashed**. It says `160.0 (64-bit)` and, beside it, the Build ID `20261111185950`.

This replaces [158.0-2](https://github.com/gorillanobakaa-dot/gorilla-firefox/releases/tag/v158.0-2).

| File | Bytes | SHA-256 |
|---|---|---|
| `Gorilla-Unleashed-160.0-linux-x86_64.deb` | 110,853,028 | `eddf949e1909dc3555bf5c67cee3009d7e440fc4b1383a9c895d69bca00f214e` |

`SHA256SUMS` lists the same number, computed from this exact file.

---
# In plain language: everything in this release

This is the complete explanation, not a summary of one. Nothing below is behind a link.

<!-- plain-language track: in full, on this page -->

**1. Firefox 160 underneath.** The browser is now built on Firefox 160.0. All the security fixes Mozilla made since 158 are in.

**2. Firefox 160's new AI parts are cut out.** Firefox 160 added more AI: an on-device text generator and an "AI control" switch. In Gorilla, the AI switch is locked to "blocked", and the text-generation code is taken out of the browser completely, so nothing is left to switch back on.

**3. The new tab page works.** A Firefox 160 module that guesses what kind of page you are on (shopping, news) was removed from Gorilla. One leftover line still asked for it, and the new tab page stayed blank. That line is fixed.

**4. Two settings removed.** Firefox 160's "Link preview" and "Highlight to search" settings are gone from Settings: the features behind them are not in Gorilla.

**Still the Gorilla you know:** it never calls home, uBlock Origin is built in and nothing else can be installed, Gorilla.Satellite mode is there for slow and expensive connections, and studies and telemetry are refused.

#### Install

```bash
sudo apt install ./Gorilla-Unleashed-160.0-linux-x86_64.deb
```

Check the download first, in the folder where you saved both files:

```bash
sha256sum -c SHA256SUMS
```

---

# For developers: how it works, and how to check it

Written for someone who will audit, fork or change the code. It covers the same release as the plain-language part above; neither is a summary of the other.

<!-- developer track: in full, on this page -->

- Base: Firefox 160.0. Patch set: `gorilla-firefox` master `5f40f3e` (`23.REBASE.160`, `23.REBASE.160.linux`, `21.PORT.FIXES.160`, `22.EGRESS.LOCKDOWN.160`). Checked on the built tree with `git apply --check -R`: every patch of `23.REBASE.160.linux` (3), `21.PORT.FIXES.160` (4) and `22.EGRESS.LOCKDOWN.160` (3) is in; `23.REBASE.160` 115 in, and 4 (`0016`, `0020`, `0047`, `0105`) no longer reverse because later fixes (`21.PORT.FIXES.160/007`, `/005`, `/003`, `22.EGRESS.LOCKDOWN.160/005`) edit the same lines again. `0122` (Windows widget build file) is left out on Linux (owner decision 2026-11-17).
- The full build is from 2026-11-11 (BuildID above). Port fixes `005` and `007` are front-end only (JavaScript); they were committed into the port tree on 2026-11-17 and built with `mach build faster`, so the BuildID did not change. Checked in the packaged files: `ASRouterTargeting.sys.mjs` `currentTabPageCategory` returns `null`; `tabs-browsing.mjs` equals the fixed tree.
- Windows: the same set, built on the Windows laptop; the egress lockdown was checked there on the built tree.
- **Not verified for this release, stated instead of hidden:** the install-and-proof run on an installed `.deb` (`build-harness post-install`), the release leak gate (`leakgate --release`), and the claims audit were not run for 160 on Linux. The browser was not started from this package before publishing.
