# Gorilla Unleashed 158.0-1 (Linux)

Firefox 158.0 (stable) based. Debian/Ubuntu `.deb`, 64-bit, 110.2 MB.
BuildID `20261016001633`.

This replaces the 155 Linux download. It is the first Gorilla Unleashed built on Firefox 158.

## 🧸 What changed, in plain words

**1. Nothing can be installed into this browser behind your back, and nobody can talk you into it.**

Add-ons and themes are small programs. Their makers can change them from the internet at any time, and each one
widens the ways a browser can be attacked. Gorilla has never allowed them (uBlock Origin, the ad blocker, is built
in). This version closes the remaining side doors and says why when something is refused:

- trying to install an extension or a theme now says it is **blocked on purpose** and why, instead of Mozilla's
  confusing "not compatible";
- websites can no longer offer extensions or search engines; Google is the only search engine and none can be added;
- the browser ignores policy files that other programs could drop into the system to reconfigure it;
- it refuses to load "security device" drivers (native programs that would run inside the browser);
- the buttons and links that used to offer add-ons, dictionaries and language packs are gone.

**Checked on this exact build, 2026-10-16:** uBlock Origin is active, Google is the only engine, and an attempt to
add an engine is refused by the browser itself.

**2. No AI features.** The AI sidebar, "Smart Window", AI tab suggestions and their texts are removed from the
browser, not just switched off.

**3. Dialogs show their whole message.** "Leave page?" and other page dialogs were cut to a thin strip (seen on
WhatsApp Web). Fixed: the dialog is measured after it is drawn.

**4. Hardware video decoding on old graphics chips.** Older Intel, AMD and NVIDIA chips are not refused any more,
so video plays on the graphics chip's video engine instead of the processor.

[![YouTube 1080p60 playing; intel-gpu-top shows the Video engine 7% busy for the gorilla-unleashed process](https://raw.githubusercontent.com/gorillanobakaa-dot/gorilla-firefox/v158.0-1/releases/158.0/screenshots/youtube-1080p60-gpu-video-engine.webp)](https://raw.githubusercontent.com/gorillanobakaa-dot/gorilla-firefox/v158.0-1/releases/158.0/screenshots/youtube-1080p60-gpu-video-engine.webp)

*Above: YouTube at 1080p60. `intel-gpu-top` (right) shows the Video engine busy for the gorilla-unleashed process:
the decoding is on the graphics chip. The same picture shows 834 dropped frames of 8667 at 60 frames per second on
this 2012 laptop; that gap is known and still being measured.*

**5. Still the Gorilla you know:** never calls home, Gorilla.Satellite mode for slow and expensive connections,
studies and telemetry refused.

[![Settings: Gorilla.Satellite mode with its three levels, for slow or expensive internet](https://raw.githubusercontent.com/gorillanobakaa-dot/gorilla-firefox/v158.0-1/releases/158.0/screenshots/settings-satellite-mode-and-privacy.png)](https://raw.githubusercontent.com/gorillanobakaa-dot/gorilla-firefox/v158.0-1/releases/158.0/screenshots/settings-satellite-mode-and-privacy.png)

[![about:studies: "We do not do studies... We refuse to be test subjects."](https://raw.githubusercontent.com/gorillanobakaa-dot/gorilla-firefox/v158.0-1/releases/158.0/screenshots/about-studies-refused.png)](https://raw.githubusercontent.com/gorillanobakaa-dot/gorilla-firefox/v158.0-1/releases/158.0/screenshots/about-studies-refused.png)

[![about:telemetry is a blocked page](https://raw.githubusercontent.com/gorillanobakaa-dot/gorilla-firefox/v158.0-1/releases/158.0/screenshots/about-telemetry-blocked.png)](https://raw.githubusercontent.com/gorillanobakaa-dot/gorilla-firefox/v158.0-1/releases/158.0/screenshots/about-telemetry-blocked.png)

[![about:robots, Gorilla's version](https://raw.githubusercontent.com/gorillanobakaa-dot/gorilla-firefox/v158.0-1/releases/158.0/screenshots/about-robots.png)](https://raw.githubusercontent.com/gorillanobakaa-dot/gorilla-firefox/v158.0-1/releases/158.0/screenshots/about-robots.png)

The screenshots were taken by the maintainer on 2026-10-15 on the build before this one; what they show did not
change in this build. The new "blocked on purpose" message is not pictured yet.

### Install

```bash
sudo apt install ./gorilla-unleashed_158.0-1_amd64.deb
```

Check the download first: `sha256sum gorilla-unleashed_158.0-1_amd64.deb` must print the line in `SHA256SUMS`.

## 💻 Developer

| item | value |
|---|---|
| Firefox base | 158.0, tag `FIREFOX_158_0_RELEASE`, commit `3c71aeacdb29` |
| BuildID | `20261016001633` |
| package | `gorilla-unleashed_158.0-1_amd64.deb`, 110,239,400 bytes |
| SHA-256 | `26fd13195f25a626838c0066df83f8733f88c366fa7bb3009f75791725c78e86` |
| toolchain | clang 21, lld, ThinLTO, sccache, unpacked chrome (no omni.ja) |
| patch set | 681 patches on Linux (659 on Windows), see below |

### The patch set reproduces this build

Pristine Firefox 158.0 + the public patch set (`patches/`, groups in `config/patch_policy.json` order) gives the
tree this package was built from: same git tree hash (`fieldkit build-harness replay`). 107 patches of the 157 era
no longer apply to 158 (Mozilla changed the code around them, or they were built on one that did); each is marked
`superseded_158` in the policy and kept as history, and the 158 form of every file is in `23.REBASE.158`
(`23.REBASE.158.linux` for files only Linux parts touch). Whether each superseded patch's logic reached 158 was
checked line by line: `patches/23.REBASE.158/SUPERSEDED.md`. Two real losses were found and ported (DNS negative
cache 3 s, a SessionStore call into removed Smart Window code) plus about 25 Gorilla wordings on renamed message ids.

One policy now serves both systems: `platforms` and `exclude_on` pick the patches for the system the harness runs
on (01.MEDIA, the GTK graphics unlock and the Linux font list are Linux only).

### Decisions this build enforces (decisions/PRODUCT-DECISIONS.yaml)

| id | what | where it is enforced |
|---|---|---|
| D-157-05 | no extensions except uBlock Origin | XPIInstall, XPIDatabase, XPIProvider, AddonManager PHYSICAL LOCKs (no test bypass); locked `extensions.webapi.enabled`, `xpinstall.enabled`, `extensions.InstallTrigger.enabled`; refusal message `gorilla-addon-install-refused` |
| D-158-13 | Google is the only search engine; none can be added | `SearchService.#addEngineToStore` keeps only application engines; add APIs throw; no page offer, no form "Add Search Engine" |
| D-158-17 | only Gorilla's own policies | `EnterprisePoliciesParent.sys.mjs`: no `/etc/firefox/policies`, no Windows GPO, no alternate path |
| D-158-18 | no PKCS#11 module is loaded | `PKCS11ModuleDB::DoAddModule` refuses every route |
| D-158-08 | no AI in the browser | AI UI, Smart Window, texts and stylesheets removed |
| D-158-06 | old GPUs unlocked | `widget/GfxInfoBase.cpp`, `widget/GfxDriverInfo.cpp`, `widget/gtk/GfxInfo.cpp` |

Register on the installed build: 57 enforced, 0 violated (`fieldkit build-harness decisions firefox-158-linux`).

### How it was checked

`fieldkit pipeline run firefox-linux` (preflight, build, package, install), then `build-harness decisions`,
`build-harness probe ... js=install-surface`, `build-harness clip-check`, and `build-harness release-roundtrip`
(the published file downloaded from this page, checked against `SHA256SUMS`, installed, verified). Tools:
[Gorilla.Fieldkit](https://github.com/gorillanobakaa-dot/Gorilla.Fieldkit).
