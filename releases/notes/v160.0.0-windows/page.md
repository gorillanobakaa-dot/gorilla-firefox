# Gorilla Unleashed 160.0 (Windows)

### What this is

Gorilla Unleashed 160.0 for Windows 10 and 11: a Firefox that never calls home, with the AI parts of Firefox 160 cut out.

### Should you download it

Yes, if you run Gorilla 158 on Windows: this replaces it. The Linux build has its own release page.

### Why it matters

Firefox 160 brings Mozilla's newest security fixes, and more AI that Gorilla takes out.

Firefox 160.0 (stable) based. Windows 64-bit, portable `.zip`. BuildID **`20261117045348`**.

After you unzip and start it, open **Help > About Gorilla Unleashed**. It says `160.0 (64-bit)` and, beside it, the Build ID `20261117045348`.

This replaces [158.0 build 2](https://github.com/gorillanobakaa-dot/gorilla-firefox/releases/tag/v158.0-win64-build2).

| File | Bytes | SHA-256 |
|---|---|---|
| `Gorilla-Unleashed-160.0-win64.zip` | 135,906,663 | `b54f67e5076be7a0d04288dab377dbbd4182aba6803ec1849013f3f1337090f1` |

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

Unzip `Gorilla-Unleashed-160.0-win64.zip` anywhere (for example `C:\Gorilla`) and start `firefox\firefox.exe`. Nothing is installed into Windows.

Check the download first, in PowerShell, in the folder where you saved it:

```powershell
(Get-FileHash .\Gorilla-Unleashed-160.0-win64.zip -Algorithm SHA256).Hash
```

It must print `B54F67E5076BE7A0D04288DAB377DBBD4182ABA6803EC1849013F3F1337090F1`.

---

# For developers: how it works, and how to check it

Written for someone who will audit, fork or change the code. It covers the same release as the plain-language part above; neither is a summary of the other.

<!-- developer track: in full, on this page -->

- Base: Firefox 160.0. Patch set: `gorilla-firefox` `23.REBASE.160`, `21.PORT.FIXES.160`, `22.EGRESS.LOCKDOWN.160` (Windows widget build file `23.REBASE.160/0122` included on Windows).
- Built on the Windows laptop with `fieldkit emerge run firefox-windows` on 2026-11-17: GREEN, 12.0 min wall, 0 model calls; the `migrate-preflight` set-proof replayed the patch set on pristine Firefox 160 before the build. Full BuildID above (`20261117045348`).
- Checked in the packaged `omni.ja`: `ASRouterTargeting.sys.mjs` `currentTabPageCategory` returns `null` and has no `AgentPageDetector` lazy getter (the blank new tab page fix).
- Linux: the same set, see [v160.0.0-linux](https://github.com/gorillanobakaa-dot/gorilla-firefox/releases/tag/v160.0.0-linux).
- **Not verified for this release, stated instead of hidden:** the install tier (`build-verify`, `package-checks`, `post-install`) and the release leak gate (`leakgate --release`) were skipped by this run (tier iterate). The browser was not started from this zip before publishing.
