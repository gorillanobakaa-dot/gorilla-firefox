# Firefox 154 Gorilla Unleashed — Patch Structure & File Registry

> **Document Version:** 1.1 | **Last Updated:** 2026-07-08 | **Author:** Gorilla  
> **Supersedes:** MAP.md (informal version)  
> **Document Classification:** Technical Reference  
> **Confidentiality:** Public (Open Source)

---

## EXECUTIVE SUMMARY

**Purpose:** This document provides a complete inventory of all patches in the Gorilla Unleashed Firefox 154 project, organized by category with file counts, descriptions, and deployment paths.

**Scope:**
- **Included:** All 156 patch files across 14 categories, deployment script, file-to-path mappings
- **Excluded:** Detailed patch content (covered in category-specific roadmap documents), build procedures (covered in FIREFOX-154.WORKFLOW_IBM.md)

**Target Audience:**
- **Primary:** Developers navigating the patch structure
- **Secondary:** Build engineers deploying patches, auditors reviewing changes

**Prerequisites:**
- Understanding of Firefox source tree structure
- Familiarity with patch deployment concepts
- Knowledge of Firefox build system

**Key Outcomes:**
- **Complete file inventory** — 156 files catalogued by category
- **Clear organization** — 14 logical categories (media, GPU, networking, etc.)
- **Deployment mapping** — Each file's source and destination path documented
- **Quick reference** — Find any patch file instantly

---

## 1. CONTEXT & MISSION

### 1.1 Problem Statement

**Patch Organization Challenge:**

The Gorilla Unleashed project modifies 156 files across the Firefox source tree. Without clear organization:
1. **Hard to find files** — Searching through 156 files is time-consuming
2. **Unclear relationships** — Which files work together?
3. **Deployment confusion** — Where does each file go in the source tree?
4. **Maintenance difficulty** — Hard to update or audit patches

**Impact:**

**Plain Language:** With 156 patch files scattered across 14 categories, you need a map to find anything.

**Technical Detail:** The Firefox source tree has ~500,000 files. Our 156 patches target specific subsystems (media, GPU, networking, etc.). Without a structured inventory, developers waste time searching for files, risk deploying to wrong paths, and struggle to understand patch relationships.

### 1.2 Solution Approach

**Strategy:** Flat directory structure organized by functional category, with a central registry (this document) mapping files to their purpose and deployment paths.

**Organization Principles:**

1. **Functional categories** — Group by subsystem (01.MEDIA, 02.GPU, etc.)
2. **Flat structure** — No deep nesting, all files at category root
3. **Numeric prefixes** — Categories sorted by importance (01 = most critical)
4. **Descriptive names** — Category names clearly indicate purpose
5. **Central registry** — This document maps all files

**Rationale:**
- **Flat structure** — Easier to navigate than deep hierarchies
- **Functional grouping** — Related patches stay together
- **Numeric prefixes** — Enforce logical ordering
- **Central registry** — Single source of truth for file locations

### 1.3 Success Criteria

- [ ] **All 156 files catalogued** — Complete inventory with descriptions
- [ ] **14 categories documented** — Each with file count and purpose
- [ ] **Deployment paths mapped** — Source → destination for every file
- [ ] **Quick reference enabled** — Find any file in <30 seconds
- [ ] **Audit-ready** — Clear structure for code review

### 1.4 Non-Goals

**Explicitly Out of Scope:**
- **Detailed patch content** — See category-specific roadmap documents
- **Build procedures** — See FIREFOX-154.WORKFLOW_IBM.md
- **Performance analysis** — See ROADMAP_IBM.md
- **Historical evolution** — See individual category roadmaps

---

## 2. PATCH STRUCTURE OVERVIEW

### 2.1 Directory Layout

```
patches/
├── deploy.sh                          # Deployment automation script
├── MAP_IBM.md                         # This document
├── DOCUMENTATION_TEMPLATES.md         # IBM-style templates
├── HOW_TO_GET_IBM_QUALITY_DOCS.md    # Prompting framework
├── LLM_TEMPLATE_USAGE_GUIDE.md       # LLM documentation guide
│
├── 01.MEDIA/                          # 19 active build files (+2 archived) + docs - Codec/video/audio (ALL DONE)
├── 02.GPU/                            # 5 files (4 C++ + 1 Master Log) - Graphics driver unlock (ALL DONE)
├── 03.NETWORKING/                     # 10 files (8 C++ + 1 Master Log + 1 Audit Report) - Network stack (ALL DONE)
├── 04.PERFORMANCE/                    # 6 files (4 C++ + 1 Master Log + 1 Audit Report) - Clang-21 build fix, JS telemetry, IVB CC tuning (ALL DONE)
├── 05.PREFS/                          # 7 files (5 configuration + 1 Master Log + 1 Audit Report) - Preferences/config (ALL DONE)
├── 06.QUOTA/                          # (empty - placeholder)
├── 07.TOOLKIT/                        # 21 files (19 source + 1 Master Log + 1 Audit Report) - Browser logic modules (ALL DONE)
├── 08.Look/                      # 92 files (90 source + 1 Master Log + 1 Audit Report) + 236 deep locales - Theme, branding, design tokens (ALL DONE)
├── 09.REMOTE/                         # 2 files - Marionette/RemoteAgent
├── 10.OVERRIDES/                      # 1 file - user.js runtime config
├── 11.FONT.SYSTEM/                    # 5 files - Font scanning patches
└── 12.MOZAMBIQUE.DRILL/               # 3 files - Normandy/Nimbus neutralization

Total: ~155 files + deploy.sh + documentation
```

### 2.2 Category Summary

| Category | Files | Purpose | Priority |
|----------|-------|---------|:--------:|
| 01.MEDIA | 19 (+2 archived) | Codec enforcement, VA-API, audio DSP (ALL DONE) | 🔴 Critical |
| 02.GPU | 5 | Intel HD 4000 unlock, WebRender (ALL DONE) | 🔴 Critical |
| 03.NETWORKING | 10 | HTTP/3, UDP, buffer optimization (ALL DONE) | 🟠 High |
| 04.PERFORMANCE | 6 | Clang-21 build fix, JS telemetry lobotomy, IVB CC tuning (ALL DONE) | 🟠 High |
| 05.PREFS | 7 | Build-time preference locks (ALL DONE) | 🔴 Critical |
| 06.QUOTA | 0 | (placeholder) | ⚪ None |
| 07.TOOLKIT | 21 | Browser logic (addons, search, UI) (ALL DONE) | 🟡 Medium |
| 08.Look | 92 + 236 deep locales | Theme, branding, design tokens (ALL DONE) | 🟡 Medium |
| 09.REMOTE | 2 | Marionette/RemoteAgent locks | 🔴 Critical |
| 10.OVERRIDES | 1 | Runtime user.js config | 🟡 Medium |
| 11.FONT.SYSTEM | 5 | Font scanning bypass + moz.build | 🟢 Low |
| 12.MOZAMBIQUE.DRILL | 3 | Normandy/Nimbus neutralization | 🔴 Critical |

**Total:** ~155 core files + 236 deep locales

### 2.3 Deployment Flow

```
[patches/] → [deploy.sh] → [firefox-source/]
     │              │              │
     │              ├─ Copy flat files
     │              ├─ Apply .patch files
     │              └─ Verify deployment
     │
     └─ Categories:
         ├─ 01.MEDIA/*.cpp → dom/media/
         ├─ 02.GPU/*.cpp → widget/gtk/, gfx/thebes/
         ├─ 03.NETWORKING/*.cpp → netwerk/
         ├─ 04.PERFORMANCE/*.cpp,*.h → dom/, js/, mfbt/
         ├─ 05.PREFS/*.js → browser/app/profile/, modules/libpref/
         ├─ 08.Look/* → browser/themes/shared/, browser/branding/gorilla/, toolkit/themes/shared/
         ├─ 07.TOOLKIT/*.mjs → toolkit/components/, browser/components/
         ├─ 08.Look/154.Deep.Branded.Locales/* → (mirrors source tree under browser/, toolkit/)
         ├─ 09.REMOTE/*.mjs → remote/
         ├─ 10.OVERRIDES/user.js → (user profile, not source tree)
         ├─ 11.FONT.SYSTEM/*.patch → gfx/thebes/
         └─ 12.MOZAMBIQUE.DRILL/*.patch → toolkit/components/normandy/, toolkit/components/nimbus/
```

---

## 3. CATEGORY INVENTORY

### 3.1 Category 01.MEDIA (19 active build files + 2 archived + docs)

**Purpose:** Codec enforcement, hardware video decode (VA-API), psychoacoustic audio DSP, zero software fallback (ALL DONE)

**Priority:** 🔴 Critical — Core mission (hardware-only H.264, reject VP9/AV1)

**Active patched source files (deployed via deploy.sh):**

| File | Deploy Path | Purpose | 2026-07-10 status |
|------|-------------|---------|-------------------|
| `AudioStream.cpp` | `dom/media/AudioStream.cpp` | Psychoacoustic DSP, soft-knee limiter | Patched |
| `CubebUtils.cpp` | `dom/media/CubebUtils.cpp` | Audio interface; 48 kHz pin under policy | Patched |
| `AudioContext.cpp` | `dom/media/webaudio/AudioContext.cpp` | Forces 48kHz native rate, 10ms low latency | Patched (2026-07-10) |
| `AudioDestinationNode.cpp` | `dom/media/webaudio/AudioDestinationNode.cpp` | Fast-Tanh soft-limiter to prevent clipping | Patched (2026-07-10) |
| `DecoderTraits.cpp` | `dom/media/DecoderTraits.cpp` | Codec gatekeeper (blocks VP9/AV1/WebM/Ogg) | Patched |
| `DefaultCodecPreferences.cpp` | `dom/media/webrtc/jsapi/DefaultCodecPreferences.cpp` | H.264-only WebRTC offer list | Patched |
| `FFmpegVideoDecoder.cpp` | `dom/media/platforms/ffmpeg/FFmpegVideoDecoder.cpp` | VA-API decode, 16-frame pool | Patched |
| `PDMFactory.cpp` | `dom/media/platforms/PDMFactory.cpp` | Hardware-only H.264 policy | Patched |
| `RemoteVideoDecoder.cpp` | `dom/media/ipc/RemoteVideoDecoder.cpp` | Zero-copy DMA-BUF | Patched |
| `WebrtcVideoCodecFactory.cpp` | `dom/media/webrtc/libwebrtcglue/` | WebRTC codec factory gating | Patched |
| `VideoConduit.cpp` | `dom/media/webrtc/libwebrtcglue/` | WebRTC AV1 gate | Patched |
| `WebCodecsUtils.cpp` | `dom/media/webcodecs/` | WebCodecs codec gate | Patched |
| `MediaCapabilities.cpp` | `dom/media/mediacapabilities/` | Capability reporting | Patched |
| `VideoDecoder.cpp` | `dom/media/webcodecs/` | WebCodecs decode validation | Patched |
| `VideoEncoder.cpp` | `dom/media/webcodecs/` | WebCodecs encode validation | Patched |
| `DynamicsCompressorNode.cpp` | `dom/media/webaudio/` | Web Audio compressor bypass | Patched |
| `MediaSource.cpp` | `dom/media/mediasource/` | MSE; `IsVP9Forced` gate | Patched |
| `gfxPlatformGtk.cpp` | `gfx/thebes/` | Forces `HW_DECODED_VIDEO_ZERO_COPY` | Patched |
| `moz.build` | `dom/media/moz.build` | `-march=native` build tuning | Patched; now deployed |

**Archived — no patch, upstream used as-is → `01.MEDIA/_archive_unpatched/`:**
`SourceBuffer.cpp` (ref), `RemoteMediaDataDecoder_upstream.cpp` (ref). (All unmodified files purged on 2026-07-10).

**Documentation (dual-track per Gorilla philosophy):**
`MASTER_PROJECT_LOG_FIREFOX_154_MEDIA_PATCHES.md` (single master log; all modular findings, changelogs, and roadmaps consolidated here).

**Verification:**
```bash
# Check hardware video decode active
grep "FEATURE_HARDWARE_VIDEO_DECODING" firefox-source/widget/gtk/GfxInfo.cpp
# Expected: return FEATURE_STATUS_OK;
```

---

### 3.2 Category 02.GPU (5 files)

**Purpose:** Intel HD 4000 unlock, WebRender enablement, GPU blocklist bypass (ALL DONE)

**Priority:** 🔴 Critical — Enables hardware video decode

**Files:**

| File | Deploy Path | Purpose | Type |
|------|-------------|---------|------|
| `gfxPlatform.cpp` | `gfx/thebes/gfxPlatform.cpp` | Sticky kill-switch dead-coded | Flat |
| `GfxDriverInfo.cpp` | `widget/GfxDriverInfo.cpp` | Ivy Bridge device IDs commented out | Flat |
| `GfxInfoBase.cpp` | `widget/GfxInfoBase.cpp` | Vendor short-circuit before blocklist | Flat |
| `GfxInfo.cpp` | `widget/gtk/GfxInfo.cpp` | Override feature status to OK | Flat |

> **2026-07-10:** GPU `.cpp` patches verified; modular documentation fully consolidated into `MASTER_PROJECT_LOG_FIREFOX_154_GPU_PATCHES.md`. Headers `gfxPlatform.h` / `GfxInfo.h` deleted from folder (never deployed).

**Documentation:** `02.GPU/MASTER_PROJECT_LOG_FIREFOX_154_GPU_PATCHES.md`

**Verification:**
```bash
# Check GPU unlock applied
grep "return FEATURE_STATUS_OK" firefox-source/widget/gtk/GfxInfo.cpp
# Expected: Line ~1412
```

---

### 3.3 Category 03.NETWORKING (10 files)

**Purpose:** HTTP/3, UDP optimization, 64MB socket buffers, BBR pacing (ALL DONE)

**Priority:** 🟠 High — Performance optimization

**Files:**

| File | Deploy Path | Purpose | Type |
|------|-------------|---------|------|
| `Http3Session.cpp` | `netwerk/protocol/http/Http3Session.cpp` | HTTP/3 throughput | Flat |
| `HttpChannelParent.cpp` | `netwerk/protocol/http/HttpChannelParent.cpp` | IPC channel optimization | Flat |
| `HttpConnectionUDP.cpp` | `netwerk/protocol/http/HttpConnectionUDP.cpp` | UDP connection tuning | Flat |
| `nsHostResolver.cpp` | `netwerk/dns/nsHostResolver.cpp` | DNS resolver optimization | Flat |
| `nsHttpConnectionMgr.cpp` | `netwerk/protocol/http/nsHttpConnectionMgr.cpp` | Connection pooling | Flat |
| `nsHttpTransaction.cpp` | `netwerk/protocol/http/nsHttpTransaction.cpp` | Transaction handling | Flat |
| `nsSocketTransport2.cpp` | `netwerk/base/nsSocketTransport2.cpp` | 64MB socket buffer | Flat |
| `nsUDPSocket.cpp` | `netwerk/base/nsUDPSocket.cpp` | UDP socket tuning | Flat |

**Documentation:** `03.NETWORKING/MASTER_PROJECT_LOG_FIREFOX_154_NETWORKING_PATCHES.md`

**2026-07-10 update:** Completed C++ code audit and verified telemetry lobotomy implementations. Discovered UDP send buffer sizing opportunities and wired upload pacing designs. Consolidated all networking documentation into a single master project log.

---

### 3.4 Category 04.PERFORMANCE (6 files)

**Purpose:** Clang-21 build compatibility, JS compile-cache telemetry lobotomy, IVB cycle-collector tuning (ALL DONE)

**Priority:** 🟠 High — Build survival + privacy + low-core perf

**Files:**

| File | Deploy Path | Purpose | Type |
|------|-------------|---------|------|
| `Maybe.h` | `mfbt/Maybe.h` | `IsComplete<T>` guarded trait eval (ERR-BUILD-008) | Flat |
| `MaybeStorageBase.h` | `mfbt/MaybeStorageBase.h` | `IsComplete<T>` SFINAE trait | Flat |
| `Stencil.cpp` | `js/src/frontend/Stencil.cpp` | JS compile-cache telemetry lobotomy | Flat |
| `CCGCScheduler.cpp` | `dom/base/CCGCScheduler.cpp` | IVB `kICC*` cycle-collector cadence | Flat |

> **Hygiene (2026-07-08):** The 6 previously-listed upstream-drift files (`ContentChild.cpp`, `ContentParent.cpp`, `TimeoutManager.cpp`, `nsJSEnvironment.cpp`, `RDDParent.cpp`, `WindowGlobalParent.h`) were confirmed byte-identical to vanilla FF154 and removed. This category now holds only genuinely-modified files.

**Documentation:** `04.PERFORMANCE/MASTER_PROJECT_LOG_FIREFOX_154_PERFORMANCE_PATCHES.md`

**2026-07-10 update:** Completed C++ code audit and scoured JIT self-host compile cache telemetry in `Stencil.cpp` under `#ifndef GLEAN_DISABLED`. Consolidated all performance documentation into a single master project log.

---

### 3.5 Category 05.PREFS (7 files)

**Purpose:** Build-time preference locks, mozconfig, language properties (ALL DONE)

**Priority:** 🔴 Critical — Locks telemetry/AI/experiment prefs

**Files:**

| File | Deploy Path | Purpose | Type |
|------|-------------|---------|------|
| `all.js` | `modules/libpref/init/all.js` | Additional preference defaults | Flat |
| `StaticPrefList.yaml` | `modules/libpref/init/StaticPrefList.yaml` | C++ static preferences | Flat |
| `firefox.js` | `browser/app/profile/firefox.js` | Build-time locked prefs | Flat |
| `language.properties` | `browser/locales/en-US/chrome/browser-region/region.properties` | Language/region properties | Flat |
| `mozconfig` | `.mozconfig` (firefox-source root) | Build configuration | Flat |

**Documentation:** `05.PREFS/MASTER_PROJECT_LOG_FIREFOX_154_PREFS_PATCHES.md`

**2026-07-10 update:** Completed static validation of mozconfig build optimizations and StaticPrefList settings. Configured firefox.js default branch to disable toolkit telemetry ping engines directly at build time. Consolidated all preferences and build-profile documentation into a single master project log.

**Verification:**
```bash
# Check critical prefs locked
grep "app.normandy.enabled.*locked" firefox-source/browser/app/profile/firefox.js
grep "browser.ml.chat.enabled.*locked" firefox-source/browser/app/profile/firefox.js
```

---

### 3.6 Category 08.Look (92 deployed files + 236 deep locales)

**Purpose:** Visual theme (CSS), branding assets, and design system tokens — merged from former 06_THEME, 07_BRANDING, and 09_DESIGN_TOKENS (ALL DONE)

**Priority:** 🟡 Medium — Visual identity

**Files (Visual Theme — CSS, 13 files):**

| File | Deploy Path | Purpose | Type |
|------|-------------|---------|------|
| `master-redirect.css` | `browser/themes/shared/master-redirect.css` | Master chrome theme | Flat |
| `activity-stream.css` | `browser/themes/shared/activity-stream.css` | New tab page styles | Flat |
| `nova-activity-stream.css` | `browser/themes/shared/nova-activity-stream.css` | New tab (Nova) styles | Flat |
| `preferences.css` | `browser/themes/shared/preferences.css` | Settings page styles | Flat |
| `browser-shared.css` | `browser/themes/shared/browser-shared.css` | Browser chrome globals | Flat |
| `global-shared.css` | `toolkit/themes/shared/global-shared.css` | Global UI styles | Flat |
| `common-shared.css` | `toolkit/themes/shared/common-shared.css` | Common UI styles | Flat |
| `urlbar-searchbar.css` | `browser/themes/shared/urlbar-searchbar.css` | URL bar styles | Flat |
| `unified-extensions.css` | `browser/themes/shared/unified-extensions.css` | Extensions UI styles | Flat |
| `aboutPrivateBrowsing.css` | `browser/themes/shared/aboutPrivateBrowsing.css` | Private browsing page | Flat |
| `aboutaddons.css` | `browser/themes/shared/aboutaddons.css` | Add-ons manager styles | Flat |
| `aboutconfig.css` | `browser/themes/shared/aboutconfig.css` | about:config styles | Flat |
| `contentSearchHandoffUI.css` | `browser/themes/shared/contentSearchHandoffUI.css` | Search handoff UI | Flat |

**Files (Branding Assets — 60 files):**

Icons, logos, fonts, backgrounds deployed to `browser/branding/gorilla/`. Full listing in deploy.sh.

**Files (Design System Tokens — 16 files):**

CSS + JSON token files deployed to `toolkit/themes/shared/design-system/`. Full listing in deploy.sh.

**Deep Branded Locales (236 files):** en-US locale tree mirroring `browser/locales/en-US/` and `toolkit/locales/en-US/`, including custom `brand.ftl`/`brand.properties` at `browser/branding/gorilla/locales/en-US/`.

**Documentation:** `08.Look/MASTER_PROJECT_LOG_FIREFOX_154_LOOK_PATCHES.md`

**Verification:**
```bash
# Check theme CSS deployed
ls firefox-source/browser/themes/shared/master-redirect.css
# Check branding deployed
ls firefox-source/browser/branding/gorilla/content/
# Expected: 60+ branding assets (icons, fonts, images)
```

---

### 3.7 Category 07.TOOLKIT (21 files)

**Purpose:** Browser logic modules — addons, search, UI components, translations (ALL DONE)

**Priority:** 🟡 Medium — Feature customization

**Files:**

| File | Deploy Path | Purpose | Type |
|------|-------------|---------|------|
| `AddonManager.sys.mjs` | `toolkit/mozapps/extensions/AddonManager.sys.mjs` | Addon management | Flat |
| `AddonRepository.sys.mjs` | `toolkit/mozapps/extensions/AddonRepository.sys.mjs` | Addon repository | Flat |
| `appearance.mjs` | `toolkit/components/extensions/parent/ext-appearance.mjs` | Appearance API | Flat |
| `Base.jsx` | `browser/components/newtab/content-src/components/Base/Base.jsx` | New tab base component | Flat |
| `browserLanguages.js` | `toolkit/components/extensions/parent/ext-browserLanguages.js` | Language API | Flat |
| `DiscoveryStreamBase.jsx` | `browser/components/newtab/content-src/components/DiscoveryStreamBase/DiscoveryStreamBase.jsx` | Discovery stream | Flat |
| `ExperimentAPI.sys.mjs` | `toolkit/components/nimbus/ExperimentAPI.sys.mjs` | Nimbus experiment API | Flat |
| `lib.rs` | `toolkit/components/search/merino/src/lib.rs` | Merino search (Rust) | Flat |
| `LightweightThemeManager.sys.mjs` | `toolkit/mozapps/extensions/LightweightThemeManager.sys.mjs` | Theme manager | Flat |
| `nsContextMenu.sys.mjs` | `browser/actors/nsContextMenu.sys.mjs` | Context menu | Flat |
| `QuickSuggest.sys.mjs` | `browser/components/urlbar/QuickSuggest.sys.mjs` | Quick suggest | Flat |
| `search-config-v2.json` | `toolkit/components/search/search-config-v2.json` | Search engine config | Flat |
| `semantic-categories.mjs` | `browser/themes/shared/design-system/semantic-categories.mjs` | Design categories | Flat |
| `tokens-table.mjs` | `browser/themes/shared/design-system/tokens-table.mjs` | Design tokens table | Flat |
| `TopSites.jsx` | `browser/components/newtab/content-src/components/TopSites/TopSites.jsx` | Top sites component | Flat |
| `TranslationsParent.sys.mjs` | `toolkit/components/translations/TranslationsParent.sys.mjs` | Translations parent | Flat |
| `UrlbarProviderQuickSuggest.sys.mjs` | `browser/components/urlbar/UrlbarProviderQuickSuggest.sys.mjs` | Quick suggest provider | Flat |
| `UrlbarProviderSearchSuggestions.sys.mjs` | `browser/components/urlbar/UrlbarProviderSearchSuggestions.sys.mjs` | Search suggestions | Flat |
| `XPIInstall.sys.mjs` | `toolkit/mozapps/extensions/XPIInstall.sys.mjs` | XPI installation | Flat |

**Documentation:** `07.TOOLKIT/MASTER_PROJECT_LOG_FIREFOX_154_TOOLKIT_PATCHES.md`

**2026-07-10 update:** Completed C++ and Javascript static code audits. Verified all install blockages, mock APIs, and search suggestion overrides are fully aligned. Consolidated all toolkit documentation into a single master project log.

---

### 3.9 Category 08.Look (16 files)

**Purpose:** Design system tokens (CSS + JSON) — colors, fonts, spacing

**Priority:** 🟢 Low — Design system infrastructure

**Files:**

| File | Deploy Path | Purpose | Type |
|------|-------------|---------|------|
| `tokens-brand.css` | `browser/themes/shared/design-system/tokens-brand.css` | Brand tokens | Flat |
| `tokens-platform.css` | `browser/themes/shared/design-system/tokens-platform.css` | Platform tokens | Flat |
| `tokens-shared.css` | `browser/themes/shared/design-system/tokens-shared.css` | Shared tokens | Flat |
| Various `*.tokens.json` files | `browser/themes/shared/design-system/` | Token definitions | Flat |

### 3.8 Category 09.REMOTE (2 files)

**Purpose:** Marionette/RemoteAgent triple-lock (disable remote automation)

**Priority:** 🔴 Critical — Security/privacy

**Files:**

| File | Deploy Path | Purpose | Type |
|------|-------------|---------|------|
| `Marionette.sys.mjs` | `remote/marionette/Marionette.sys.mjs` | Marionette triple-lock | Flat |
| `RemoteAgent.sys.mjs` | `remote/components/RemoteAgent.sys.mjs` | RemoteAgent triple-lock | Flat |

**Documentation:** `09.REMOTE/00_REMOTE_HISTORY_AND_ROADMAP.md`

**Verification:**
```bash
# Check triple-lock applied
grep "TRIPLE_LOCKED" firefox-source/remote/marionette/Marionette.sys.mjs
grep "TRIPLE_LOCKED" firefox-source/remote/components/RemoteAgent.sys.mjs
```

---
### 3.9 Category 10.OVERRIDES (1 file)

**Purpose:** Runtime Firefox configuration overrides (user.js)

**Priority:** 🟡 Medium — Runtime kill switches

**Files:**

| File | Deploy Path | Purpose | Type |
|------|-------------|---------|------|
| `user.js` | (User profile, not source tree) | 329 runtime kill switches | Flat |

**Documentation:** `10.OVERRIDES/00_OVERRIDES_HISTORY_AND_ROADMAP.md`

**Note:** This file is NOT deployed to the source tree. It's copied to the user's Firefox profile directory (`~/.mozilla/firefox/XXXXXXXX.default/user.js`).

---

### 3.10 Category 11.FONT.SYSTEM (5 files)

**Purpose:** Font scanning bypass patches — skip OS font enumeration when bundled fonts suffice

**Priority:** 🟢 Low — Performance optimization (200-400 ms saved)

**Files:**

| File | Deploy Path | Purpose | Type |
|------|-------------|---------|------|
| `gfxFcPlatformFontList.cpp.patch` | `gfx/thebes/gfxFcPlatformFontList.cpp` | Linux/fontconfig skip | Patch |
| `gfxFT2FontList.cpp.patch` | `gfx/thebes/gfxFT2FontList.cpp` | Android/FT2 skip | Patch |
| `gfxDWriteFontList.cpp.patch` | `gfx/thebes/gfxDWriteFontList.cpp` | Windows/DirectWrite skip | Patch |
| `gfxPlatformFontList.cpp.patch` | `gfx/thebes/gfxPlatformFontList.cpp` | Base class log | Patch |

**Documentation:** 
- `11.FONT.SYSTEM/README.md`
- `docs/font-system-patches-developer_IBM.md`
- `docs/font-system-patches-layman_IBM.md`

**Status:** ❌ **PATCHES LOST** — Existed in Firefox 153, not ported to 154

**Verification:**
```bash
# Check if patches applied (when ported)
grep "gfx.bundled_fonts.skip_system_scan" firefox-source/gfx/thebes/gfxPlatformFontList.cpp
```

---

### 3.11 Category 12.MOZAMBIQUE.DRILL (3 files)

**Purpose:** Normandy/Nimbus neutralization — three-shot technique (master switch, data starvation, 60-year sleep)

**Priority:** 🔴 Critical — Telemetry/experiment neutralization

**Files:**

| File | Deploy Path | Purpose | Type |
|------|-------------|---------|------|
| `RecipeRunner.sys.mjs.patch` | `toolkit/components/normandy/lib/RecipeRunner.sys.mjs` | 60-year timer (Normandy) | Patch |
| `RemoteSettingsExperimentLoader.sys.mjs.patch` | `toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs` | 60-year timer (Nimbus) | Patch |
| `policies.json` | `browser/app/distribution/policies.json` | Enterprise policy runtime lock | Flat |
| `README.md` | (Documentation only) | Mozambique Drill explanation | Doc |

**Documentation:** `12.MOZAMBIQUE.DRILL/README.md`

**Complementary Files:**
- `05.PREFS/firefox.js` — Build-time locked prefs
- `10.OVERRIDES/user.js` — Runtime kill switches

**Verification:**
```bash
# Check 60-year timer applied
grep "1893456000" firefox-source/toolkit/components/normandy/lib/RecipeRunner.sys.mjs
grep "1893456000" firefox-source/toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs

# Check policies.json deployed
cat firefox-source/browser/app/distribution/policies.json | grep "app.normandy.enabled"
```

---

## 4. DEPLOYMENT AUTOMATION

### 4.1 deploy.sh Script

**Purpose:** Automated deployment of all patches to firefox-source tree

**Location:** `patches/deploy.sh`

**Features:**
- Auto-detects source tree location
- Dry-run mode for safety (`--dry-run`)
- Applies .patch files with validation
- Copies flat files to correct paths
- Verifies deployment success
- Reports 156/156 files deployed

**Usage:**
```bash
cd patches

# Dry run (no changes)
./deploy.sh --dry-run $HOME/firefox-source

# Actual deployment
./deploy.sh $HOME/firefox-source
```

**Expected Output:**
```
Deploying 156 files to $HOME/firefox-source...
[✓] 01.MEDIA/AudioStream.cpp -> dom/media/AudioStream.cpp
[✓] 01.MEDIA/CubebUtils.cpp -> dom/media/CubebUtils.cpp
...
[✓] 12.MOZAMBIQUE.DRILL/RecipeRunner.sys.mjs.patch -> toolkit/components/normandy/lib/RecipeRunner.sys.mjs

Deployment complete: 156/156 files successful, 0 failed.
```

### 4.2 Deployment Verification

**Post-Deployment Checks:**
```bash
# Check critical patches applied
grep "FEATURE_STATUS_OK" $HOME/firefox-source/widget/gtk/GfxInfo.cpp
grep "1893456000" $HOME/firefox-source/toolkit/components/normandy/lib/RecipeRunner.sys.mjs
grep "Gorilla Unleashed" $HOME/firefox-source/browser/branding/gorilla/locales/en-US/brand.ftl

# Verify file count
find $HOME/firefox-source -name "*.gorilla-patched" | wc -l
# Expected: 156 (if deploy.sh marks patched files)
```

---

## 5. QUICK REFERENCE

### 5.1 Find a File by Purpose

| Need | Category | Key Files |
|------|----------|-----------|
| **Hardware video decode** | 01.MEDIA | DecoderTraits.cpp, PDMFactory.cpp, FFmpegVideoDecoder.cpp |
| **GPU unlock** | 02.GPU | GfxInfo.cpp, GfxInfoBase.cpp |
| **Network performance** | 03.NETWORKING | nsSocketTransport2.cpp, Http3Session.cpp |
| **JS performance** | 04.PERFORMANCE | CCGCScheduler.cpp (IVB CC tuning), Stencil.cpp (telemetry) |
| **Pref locks** | 05.PREFS | firefox.js, all.js |
| **Visual theme / Branding / Design tokens** | 08.Look | master-redirect.css, 60 branding assets, 16 token files |
| **Addon system** | 07.TOOLKIT | AddonManager.sys.mjs, XPIInstall.sys.mjs |
| **Remote automation** | 09.REMOTE | Marionette.sys.mjs, RemoteAgent.sys.mjs |
| **Deep branded locales** | 08.Look/154.Deep.Branded.Locales | brand.ftl (236 en-US files) |
| **Runtime config** | 10.OVERRIDES | user.js |
| **Font system** | 11.FONT.SYSTEM | gfxFcPlatformFontList.cpp.patch |
| **Telemetry kill** | 12.MOZAMBIQUE.DRILL | RecipeRunner.sys.mjs.patch, policies.json |

### 5.2 Find a File by Name

**Search Command:**
```bash
cd patches
find . -name "AudioStream.cpp"
# Output: ./01.MEDIA/AudioStream.cpp
```

**Common Files:**
- `AudioStream.cpp` → 01.MEDIA
- `GfxInfo.cpp` → 02.GPU
- `nsSocketTransport2.cpp` → 03.NETWORKING
- `CCGCScheduler.cpp` → 04.PERFORMANCE
- `firefox.js` → 05.PREFS
- `master-redirect.css` → 08.Look
- `brand.ftl` → 08.Look/154.Deep.Branded.Locales
- `user.js` → 10.OVERRIDES
- `RecipeRunner.sys.mjs.patch` → 12.MOZAMBIQUE.DRILL

---

## 6. MAINTENANCE PROCEDURES

### 6.1 Adding a New Patch

**Procedure:**
```bash
# Step 1: Determine category
# Example: Adding new media patch

# Step 2: Create patch file
cp /path/to/NewFile.cpp patches/01.MEDIA/

# Step 3: Update this document (MAP_IBM.md)
# Add entry to 01.MEDIA file list

# Step 4: Update deploy.sh (if needed)
# Usually auto-detected, but verify

# Step 5: Deploy and test
cd patches
./deploy.sh $HOME/firefox-source
cd $HOME/firefox-source
./mach build
./mach run
```

### 6.2 Removing a Patch

**Procedure:**
```bash
# Step 1: Remove from category directory
rm patches/01.MEDIA/OldFile.cpp

# Step 2: Update this document (MAP_IBM.md)
# Remove entry from file list

# Step 3: Restore vanilla file in source tree
cp /path/to/vanilla/OldFile.cpp $HOME/firefox-source/dom/media/

# Step 4: Rebuild
cd $HOME/firefox-source
./mach build
```

### 6.3 Reorganizing Categories

**Procedure:**
```bash
# Step 1: Create new category directory
mkdir patches/15_NEW_CATEGORY

# Step 2: Move files
mv patches/01.MEDIA/SomeFile.cpp patches/15_NEW_CATEGORY/

# Step 3: Update this document (MAP_IBM.md)
# Add new category section, update file lists

# Step 4: Update deploy.sh
# Add new category to deployment logic

# Step 5: Test deployment
./deploy.sh --dry-run $HOME/firefox-source
```

---

## 7. REFERENCES

### 7.1 Internal Documentation

- [ROADMAP_IBM.md](../ROADMAP_IBM.md) — Strategic roadmap
- [FIREFOX-154.WORKFLOW_IBM.md](../FIREFOX-154.WORKFLOW_IBM.md) — Build procedures
- Category-specific roadmaps:
  - [01.MEDIA/MASTER_PROJECT_LOG_FIREFOX_154_MEDIA_PATCHES.md](01.MEDIA/MASTER_PROJECT_LOG_FIREFOX_154_MEDIA_PATCHES.md)
  - [02.GPU/MASTER_PROJECT_LOG_FIREFOX_154_GPU_PATCHES.md](02.GPU/MASTER_PROJECT_LOG_FIREFOX_154_GPU_PATCHES.md)
  - [03.NETWORKING/MASTER_PROJECT_LOG_FIREFOX_154_NETWORKING_PATCHES.md](03.NETWORKING/MASTER_PROJECT_LOG_FIREFOX_154_NETWORKING_PATCHES.md)
  - [04.PERFORMANCE/MASTER_PROJECT_LOG_FIREFOX_154_PERFORMANCE_PATCHES.md](04.PERFORMANCE/MASTER_PROJECT_LOG_FIREFOX_154_PERFORMANCE_PATCHES.md)
  - [05.PREFS/MASTER_PROJECT_LOG_FIREFOX_154_PREFS_PATCHES.md](05.PREFS/MASTER_PROJECT_LOG_FIREFOX_154_PREFS_PATCHES.md)
  - [07.TOOLKIT/MASTER_PROJECT_LOG_FIREFOX_154_TOOLKIT_PATCHES.md](07.TOOLKIT/MASTER_PROJECT_LOG_FIREFOX_154_TOOLKIT_PATCHES.md)
  - [08.Look/00_LOOK_HISTORY_AND_ROADMAP.md](08.Look/00_LOOK_HISTORY_AND_ROADMAP.md)
  - [09.REMOTE/00_REMOTE_HISTORY_AND_ROADMAP.md](09.REMOTE/00_REMOTE_HISTORY_AND_ROADMAP.md)
  - [10.OVERRIDES/00_OVERRIDES_HISTORY_AND_ROADMAP.md](10.OVERRIDES/00_OVERRIDES_HISTORY_AND_ROADMAP.md)
  - [11.FONT.SYSTEM/README.md](11.FONT.SYSTEM/README.md)
  - [12.MOZAMBIQUE.DRILL/README.md](12.MOZAMBIQUE.DRILL/README.md)

### 7.2 External Resources

- [Mozilla Firefox Source Tree](https://hg.mozilla.org/mozilla-central/)
- [Firefox Build Documentation](https://firefox-source-docs.mozilla.org/setup/index.html)

---

## APPENDIX A: FILE COUNT BY CATEGORY

| Category | Flat Files | Patch Files | Reference Files | Total |
|----------|------------|-------------|-----------------|-------|
| 01.MEDIA | 19 | 0 | 0 | 19 | (+2 unpatched archived in _archive_unpatched/) |
| 02.GPU | 4 | 0 | 0 | 4 | (+1 master log) |
| 03.NETWORKING | 8 | 0 | 0 | 8 | (+1 master log + 1 audit report) |
| 04.PERFORMANCE | 4 | 0 | 0 | 4 | (+1 master log + 1 audit report) |
| 05.PREFS | 5 | 0 | 0 | 5 | (+1 master log + 1 audit report) |
| 07.TOOLKIT | 19 | 0 | 0 | 19 | (+1 master log + 1 audit report) |
| 08.Look | 90 | 0 | 0 | 90 |
| 09.REMOTE | 2 | 0 | 0 | 2 |
| 10.OVERRIDES | 1 | 0 | 0 | 1 |
| 11.FONT.SYSTEM | 1 | 4 | 0 | 5 |
| 12.MOZAMBIQUE.DRILL | 1 | 2 | 0 | 3 |
| **TOTAL** | **158** | **6** | **0** | **164** |

**Note:** Reference files are not deployed, only used for diffing/comparison.

---

## APPENDIX B: DEPLOYMENT PATH MAPPING

**Format:** `patches/CATEGORY/FILE → firefox-source/PATH`

**Media:**
- `01.MEDIA/AudioStream.cpp` → `dom/media/AudioStream.cpp`
- `01.MEDIA/DecoderTraits.cpp` → `dom/media/DecoderTraits.cpp`
- `01.MEDIA/FFmpegVideoDecoder.cpp` → `dom/media/platforms/ffmpeg/FFmpegVideoDecoder.cpp`
- `01.MEDIA/PDMFactory.cpp` → `dom/media/platforms/PDMFactory.cpp`
- `01.MEDIA/RemoteVideoDecoder.cpp` → `dom/media/ipc/RemoteVideoDecoder.cpp`

**GPU:**
- `02.GPU/GfxInfo.cpp` → `widget/gtk/GfxInfo.cpp`
- `02.GPU/GfxInfoBase.cpp` → `widget/GfxInfoBase.cpp`
- `02.GPU/GfxDriverInfo.cpp` → `widget/GfxDriverInfo.cpp`
- `02.GPU/gfxPlatform.cpp` → `gfx/thebes/gfxPlatform.cpp`

**Networking:**
- `03.NETWORKING/nsSocketTransport2.cpp` → `netwerk/base/nsSocketTransport2.cpp`
- `03.NETWORKING/Http3Session.cpp` → `netwerk/protocol/http/Http3Session.cpp`

**Performance:**
- `04.PERFORMANCE/CCGCScheduler.cpp` → `dom/base/CCGCScheduler.cpp`
- `04.PERFORMANCE/Stencil.cpp` → `js/src/frontend/Stencil.cpp`

**Preferences:**
- `05.PREFS/firefox.js` → `browser/app/profile/firefox.js`
- `05.PREFS/all.js` → `modules/libpref/init/all.js`
- `05.PREFS/mozconfig` → `.mozconfig` (root)

**Theme:**
- `08.Look/master-redirect.css` → `browser/themes/shared/master-redirect.css`
- `08.Look/activity-stream.css` → `browser/themes/shared/activity-stream.css`

**Branding:**
- `08.Look/*` → `browser/branding/gorilla/*` (mirrors structure)

**Deep Branded Locales (under 08.Look/154.Deep.Branded.Locales/):**
- `browser/*` → `browser/locales/en-US/*` (mirrors structure)
- `toolkit/*` → `toolkit/locales/en-US/*` (mirrors structure)

**Mozambique Drill:**
- `12.MOZAMBIQUE.DRILL/RecipeRunner.sys.mjs.patch` → `toolkit/components/normandy/lib/RecipeRunner.sys.mjs`
- `12.MOZAMBIQUE.DRILL/policies.json` → `browser/app/distribution/policies.json`

---

## DOCUMENT HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-06 | Gorilla | Initial IBM-format conversion from MAP.md |
| 1.1 | 2026-07-08 | Gorilla | Reflected 2026-07-08 work: 01.MEDIA → 17 active build files + 10 archived; 02.GPU doc refresh; 03.NETWORKING 4 files + doc updated; moz.build now deployed; PGO enabled in 05.PREFS/mozconfig |
| 1.2 | 2026-07-10 | Gorilla | Marked 01.MEDIA, 02.GPU, 03.NETWORKING, 04.PERFORMANCE, 05.PREFS, and 07.TOOLKIT as complete. Added AudioContext/AudioDestinationNode to active 01.MEDIA. Documented GPU, Networking, Performance, Prefs, and Toolkit file consolidations. |

---

**Document Classification:** Technical Reference  
**Confidentiality:** Public (Open Source)  
**Review Cycle:** On patch structure changes  
**Next Review:** 2026-10-06

---

**END OF DOCUMENT**
