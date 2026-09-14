# 10.OVERRIDES — Master Project Log

*Canonical doc for this folder. Policy: one master project log per folder; the dual-track
LAYMAN/DEVELOPER/AUDIT docs + PRECHECK are merged VERBATIM below and the loose copies deleted
(recoverable via git history).*

---

# ═══ REGENERATION 2026-08-04 — dual-track docs regenerated and re-merged (supersedes the 2026-08-02 merge) ═══

The 2026-08-02 merge (still in git history) is **superseded**. It carried two errors this
regeneration fixes:
1. It repeated the false "single / sole ~1,121-line user.js" claim. Tree-verified fact: this
   room owns **two** small pref files — `NEW_FILES/user.js` (53 lines, 11 real keys) and the
   unshipped `user.js.privacy-close-list.js` (23 lines). The ~1,121-line file is real but lives
   **outside this room** at `patches/Mozconfig/user.js` (60,283 bytes). Three pref files total.
2. Its audit was a bare "PASS / no defects". This regeneration records four real P3 items,
   including the **four hallucinated (inert) pref keys** in the privacy list and the stale
   `00_OVERRIDES_HISTORY_AND_ROADMAP.md` narrative (which still says "8GB RAM" and "sole user.js").

Verification anchors used this pass (against `FF_SRC=the source tree`):
- All 4 suspect keys ABSENT from the whole tree: `toolkit.telemetry.coverage.opt-out`,
  `browser.ping-centre.telemetry`, `browser.attribution.enabled`,
  `messaging-system.rsexperimentloader.enabled`.
- GORILLA `UserForceEnable` zero-copy block at `gfx/thebes/gfxPlatformGtk.cpp:276-283`
  (gated by `StaticPrefs::media_gorilla_hardware_only_mode()`); vanilla `UserEnable` at :257.
- `GORILLA HW-ONLY POLICY` at `dom/media/platforms/PDMFactory.cpp:456`.
- `media.ffmpeg.vaapi.force-surface-zero-copy` default `2` (StaticPrefList.yaml:12814-12816);
  `gfx.webrender.compositor` default `false` on Linux (StaticPrefList.yaml:8381-8386).
- Precheck (rules): P0 0 / P1 0 / P2 0 / P3 0.
- Quality gate (renderer-computed): LAYMAN 90 / DEVELOPER 86 / AUDIT 95 (gate 85). All PASS.

Deployment reminder (README.txt, verbatim): `user.js` goes to
`obj-x86_64-pc-linux-gnu/tmp/profile-default/user.js` — the **profile**, NOT the source tree.


---

# ═══ MERGED DOCUMENT: 10-overrides.AUDIT.md (verbatim · sha256:86283001f81d6c33 · merged 2026-08-04) ═══

# IBM-Style Audit Report: 10.OVERRIDES

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target** | 10.OVERRIDES |
| **Files scanned** | see payload |
| **Date / time** | 2026-08-04 07:15:37 |
| **Audit status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Plain Language)

This room ships settings files, not program changes. The main file (53 lines, 11 settings) is what keeps this laptop's graphics working on Wayland and routes video to the built-in H.264 hardware decoder. It is correct and safe on its target hardware. A second file is a draft privacy list that is not switched on yet; four of its ten lines name settings that do not exist and therefore do nothing. Think of it like a fuse box: the live panel is wired and labelled correctly, and there is a spare panel on the bench with four switches that were never connected to anything. Nothing here blocks shipping. The open items are tidiness: finish or clearly label the draft, and fix the four dead lines and some stale wording in the old roadmap.

## SECTION C: TECHNICAL SUMMARY (Developer)

Pref-layer topic, no compiled changes. NEW_FILES/user.js (11 user_pref keys) is the Wayland/media runtime belt: gpu-process off (golden rule 1), VA-API forced in RDD, zero-copy via force-surface-zero-copy=1 bypassing gfxInfo, native Wayland compositor force-enabled, AV1/VP9 off to negotiate H.264. All 11 keys are real prefs and back compiled-in C++ (gfxPlatformGtk.cpp UserForceEnable at 276-283; PDMFactory.cpp HW-ONLY POLICY at 456). user.js.privacy-close-list.js is an unshipped Topic-14 staging fragment: 6 of 10 keys are real (discovery, shield optoutstudies, crashReports probe, tab crash report, AS telemetry, AS feeds telemetry), 4 are hallucinated and inert (toolkit.telemetry.coverage.opt-out, browser.ping-centre.telemetry, browser.attribution.enabled, messaging-system.rsexperimentloader.enabled) — verified absent from the whole FF_SRC tree. No P0/P1. The precheck (rule pass) reports 0/0/0/0.

## SECTION D: DETECTED DEFECTS

0 found by rules, 4 by review. Rule findings are deterministic; review findings are judgement.

### 🟢 P3-101 — P3 *(found by review)*

- **Plain English:** Four privacy switches are wired to nothing. They are spelled for Firefox settings that do not exist, so flipping them does nothing. Harmless, but they can fool a reader into thinking a tracking door is shut.
- **Technical:** user.js.privacy-close-list.js:16,19,22,23 — messaging-system.rsexperimentloader.enabled, browser.ping-centre.telemetry, toolkit.telemetry.coverage.opt-out, browser.attribution.enabled. grep -rIl across FF_SRC returns zero hits for each.
- **Fix:** Replace with the real key names for those intents (or remove the lines) so the file does not overstate coverage.
- **Effort:** 30min

### 🟢 P3-102 — P3 *(found by review)*

- **Plain English:** The privacy draft is a spare part on the bench: it is written but not connected to the build, so it protects nobody yet.
- **Technical:** user.js.privacy-close-list.js is not referenced by README.txt (which only names NEW_FILES/user.js as the profile artifact) or any deploy path found in this room.
- **Fix:** Either wire the real subset into the profile deployment per Topic 14, or rename/annotate it explicitly as a draft.
- **Effort:** 1-2h

### 🟢 P3-103 — P3 *(found by review)*

- **Plain English:** The old roadmap in this room still tells the wrong story: it calls a single 1,100-line file the 'only' user.js and cites 8GB RAM.
- **Technical:** 00_OVERRIDES_HISTORY_AND_ROADMAP.md lines 15,44,63,76 — 'single authoritative user.js (~1121 lines)', '8GB RAM', 'sole runtime user.js'. The 1,121-line file is at patches/Mozconfig/user.js; reference machine is 16 GiB UMA.
- **Fix:** Reconcile the roadmap with the 2026-08-03/04 corrections already recorded in the master log.
- **Effort:** 30min

### 🟢 P3-104 — P3 *(found by review)*

- **Plain English:** A performance claim in the comments (a big drop in memory-bandwidth) has no measurement behind it.
- **Technical:** NEW_FILES/user.js:41 'cutting IMC bandwidth from ~2500 MiB/s to ~500 MiB/s' and :39 '~4x extra GPU memory bandwidth' are asserted without a cited measurement.
- **Fix:** Attach a measurement (e.g. intel_gpu_top before/after) or reword as an estimate.
- **Effort:** 1h

## SECTION E: PRODUCTION READINESS

**Overall readiness: 🟡 88%**

**Done:**
- [x] NEW_FILES/user.js: 11 real user_pref keys, all confirmed present in the FF_SRC tree
- [x] gpu-process-off trio present and correct (golden rule 1, Wayland black-window avoidance)
- [x] VA-API/zero-copy/compositor prefs match their compiled-in C++ belts (gfxPlatformGtk.cpp 276-283, StaticPrefList defaults 2 and false)
- [x] AV1/VP9-off codec prefs consistent with the PDMFactory.cpp hardware-only policy (line 456)
- [x] Precheck clean: P0 0 / P1 0 / P2 0 / P3 0 (rules)
- [x] Deployment destination documented (README.txt: profile, not source tree)
- [x] Doc-drift correction for the 'sole/only 1121-line' claim already recorded in the master log

**To do:**
- [ ] P3-101: fix or remove the 4 hallucinated keys in the privacy list
- [ ] P3-102: ship or clearly label the unshipped privacy-close-list draft
- [ ] P3-103: reconcile 00_OVERRIDES_HISTORY_AND_ROADMAP.md stale claims (8GB, 'sole' file)
- [ ] P3-104: measure or re-word the bandwidth claim

**Not verified:**
- LIBVA_DRIVER_NAME=i965 in /etc/environment — a system file outside the repo; not checkable here
- The IMC bandwidth ~2500->500 MiB/s figure — asserted in-comment, not independently measured
- That the privacy list touches none of the five pillars (DRM/WebAuthn/WebRTC/PKI/sandbox) — taken from the file header, not re-audited pillar-by-pillar here
- Runtime effect of the prefs on a live profile — verified statically against source, not by launching the build in this pass

## SECTION F: PHASED PLAN

### Phase 0 — `user.js.privacy-close-list.js`
- **Change:** Replace the 4 hallucinated keys with real equivalents or delete them; add a header line stating deployment status.
- **Expected impact:** File stops overstating coverage; safe to reason about.

### Phase 1 — `deploy path (Topic 14)`
- **Change:** Wire the real 6-key subset into the profile deployment if the egress lockdown is to be active.
- **Expected impact:** Turns the draft into actual hardening.

### Phase 1 — `00_OVERRIDES_HISTORY_AND_ROADMAP.md`
- **Change:** Correct the 'sole 1121-line user.js' and 8GB claims to match the three-file reality and 16 GiB UMA.
- **Expected impact:** Roadmap stops contradicting the master log.

### Phase 2 — `NEW_FILES/user.js comments`
- **Change:** Attach a measurement to the bandwidth claim or mark it an estimate.
- **Expected impact:** Honest, falsifiable perf note.

## POSITIVE OBSERVATIONS

- All 11 keys in NEW_FILES/user.js are real prefs that exist in the tree, and each backs compiled-in C++ rather than standing alone.
- The gpu-process-off decision is the correct one for this Wayland build and matches golden rule 1.
- Every line carries a WHY comment; the file is fully auditable in plain text.
- The privacy list is honest about scope in its header (independent-transport doors first, five pillars untouched) even though four of its keys are dead.
- Keeping the deliberate no-op (gfx.x11-egl.force-enabled) self-documented avoids a future reader mistaking it for a live setting.

## VERIFICATION COMMANDS

Run these to check the claims above rather than trusting them.

```bash
wc -l patches/new.patches/10.OVERRIDES/NEW_FILES/user.js   # 53
grep -c user_pref patches/new.patches/10.OVERRIDES/NEW_FILES/user.js   # 11
for k in toolkit.telemetry.coverage.opt-out browser.ping-centre.telemetry browser.attribution.enabled messaging-system.rsexperimentloader.enabled; do grep -rIl -F "$k" $FF_SRC >/dev/null && echo FOUND $k || echo ABSENT $k; done   # all ABSENT
sed -n '276,283p' $FF_SRC/gfx/thebes/gfxPlatformGtk.cpp   # GORILLA UserForceEnable
grep -n 'GORILLA HW-ONLY POLICY' $FF_SRC/dom/media/platforms/PDMFactory.cpp   # line 456
sed -n '12814,12816p' $FF_SRC/modules/libpref/init/StaticPrefList.yaml   # force-surface-zero-copy value: 2
wc -l patches/Mozconfig/user.js   # 1121 — the big file lives OUTSIDE this room
```

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| 11 real keys in NEW_FILES/user.js | 📄 stated in input | NEW_FILES/user.js  (js, 53 lines, sha256:e89ddfd918a4b3fd) |
| 4 hallucinated keys, absent from tree | 🤖 model inference | *(none — model judgment)* |
| 6 privacy keys are real | 🤖 model inference | *(none — model judgment)* |
| Precheck clean 0/0/0/0 | 🤖 model inference | *(none — model judgment)* |
| 1,121-line user.js is at patches/Mozconfig/user.js | 🤖 model inference | *(none — model judgment)* |
| Destination is the profile | 📄 stated in input | user.js goes to: obj-x86_64-pc-linux-gnu/tmp/profile-default/user.js (profile, NOT source tree) |
| Bandwidth 2500->500 is in-comment, not measured | 📄 stated in input | cutting IMC bandwidth from ~2500 MiB/s to ~500 MiB/s |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.


---

# ═══ MERGED DOCUMENT: 10-overrides.DEVELOPER.md (verbatim · sha256:15a82d189dc3027a · merged 2026-08-04) ═══

# 10.OVERRIDES: Wayland/Media Runtime user.js and the Unshipped Privacy Close-List

> Generated 2026-08-04 | Source: `10.OVERRIDES`

---

## Purpose

This topic is the profile-layer override set for the Gorilla Unleashed Firefox 154 build. It contains no source patches. It ships preference files that libpref reads on every launch and applies to the user branch, which wins over the app-default branch and loses only to policies.json (Topic 12). This room owns two files: NEW_FILES/user.js (53 lines, 11 user_pref keys, sha256 e89ddfd918a4b3fd), the Wayland/media runtime override that the graphics and codec C++ patches depend on being present at the pref layer; and user.js.privacy-close-list.js (23 lines, 10 keys, sha256 7f0c766ee594d5a0), an unshipped staging fragment for the egress-lockdown work in Topic 14. Trust level: part of the build artifact, not attacker-reachable input.

## Design Rationale

Values live at the pref layer, not only compiled-in, for two reasons the build relies on. First, defence in depth: several of these prefs are belt-and-suspenders for C++ that is already compiled in — the hardware-only codec policy in PDMFactory.cpp and the zero-copy UserForceEnable in gfx/thebes/gfxPlatformGtk.cpp — so a silently reset pref cannot defeat the intended behaviour. Second, iteration speed: a pref edit plus restart replaces a 10-20 minute rebuild. The privacy list is a separate file precisely so it can be reviewed and staged independently before it is wired into any deploy path.

## Architecture

- **Pattern:** libpref user-branch overrides read at profile init; no code, declarative user_pref() only.
- **Trust boundary:** Pref files are trusted because they are part of the build artifact. They set state; they do not parse untrusted network input.
- **Attack surface:** None reachable remotely. A local actor who can write the profile user.js can change these prefs, but that actor already controls the profile.
- **Dependencies:** `gfx/thebes/gfxPlatformGtk.cpp (UserForceEnable zero-copy, lines 276-283)`, `dom/media/platforms/PDMFactory.cpp (GORILLA HW-ONLY POLICY, line 456)`, `modules/libpref/init/StaticPrefList.yaml (pref defaults)`, `Topic 12 policies.json (locks that outrank user.js)`, `Topic 14 FORENSIC_AUDIT_AND_HARDENING_PLAN_2026-08-01.md (privacy-list rationale)`

## Flags & Configuration

| Name | Type | Default | Effect | Notes |
|------|------|---------|--------|-------|
| `layers.gpu-process.enabled` | `bool` | `true (platform)` | false: no GPU process. Required on this Wayland build. | Golden rule 1: GPU process must stay off on Wayland or the window is black. |
| `layers.gpu-process.force-enabled` | `bool` | `false` | kept false to prevent a forced GPU process. | Belt for the line above. |
| `media.gpu-process-decoder` | `bool` | `true` | false: decoding does not go through the GPU process. | VA-API decode is in RDD, not GPU process. |
| `gfx.x11-egl.force-enabled` | `bool` | `false` | no-op in a cairo-gtk3-wayland build; InitX11EGLConfig body is skipped under #ifdef MOZ_X11. | Deliberate no-op kept for pref-list tidiness (self-documented in the file). |
| `media.ffmpeg.vaapi.enabled` | `bool` | `false (see StaticPrefList)` | true: VA-API decode path enabled in RDD. | Requires i965 driver; LIBVA_DRIVER_NAME=i965 in /etc/environment (not verifiable from repo). |
| `media.ffmpeg.vaapi.decode.force-enabled` | `bool` | `false` | true: forces VA-API, no silent software fallback. | Software fallback would be rejected by the C++ hardware-only policy anyway. |
| `media.ffmpeg.vaapi.force-surface-zero-copy` | `uint32_t` | `2 (StaticPrefList.yaml:12814-12816, mirror: once)` | 1: skip the gfxInfo GetFeatureStatus call so a non-ALLOW_ALWAYS status cannot set mEnvironment=Blocklisted. | Belt for the C++ UserForceEnable at gfxPlatformGtk.cpp:283. |
| `gfx.webrender.compositor.force-enabled` | `bool` | `gfx.webrender.compositor is false on Linux (StaticPrefList.yaml:8381-8386)` | true: bypass gfxInfo blocklist, activate native Wayland compositor so NV12 DMABuf surfaces go to KMS hardware planes. | Side effect: UploadSWDecodeToDMABuf() also becomes true when GetWebRenderCompositorType()==WAYLAND. |
| `media.av1.enabled` | `bool` | `true` | false: AV1 off. | Belt for the compiled-in DecoderTraits CANPLAY_NO patch; also makes isTypeSupported() return false in JS. |
| `media.vp9.enabled` | `bool` | `true` | false: VP9 off. | Same belt-and-suspenders role. |
| `media.mediasource.vp9.enabled` | `bool` | `true` | false: VP9 blocked in MSE so sites negotiate H.264 MP4. | Same role. |
| `browser.discovery.enabled` | `bool` | `true (browser/app/profile/firefox.js)` | false: closes TAAR add-on recommendation to services.addons. | privacy-close-list; REAL key; unshipped. |
| `app.shield.optoutstudies.enabled` | `bool` | `true (modules/libpref/init/all.js)` | false: no Shield studies. | privacy-close-list; REAL key; unshipped. |
| `browser.crashReports.unsubmittedCheck.enabled` | `bool` | `false (firefox.js)` | false: no unsubmitted-crash probe. | privacy-close-list; REAL key; unshipped. |
| `browser.tabs.crashReporting.sendReport` | `bool` | `true (firefox.js)` | false: no tab-crash report to crash-stats.mozilla.org. | privacy-close-list; REAL key; unshipped. |
| `browser.newtabpage.activity-stream.telemetry` | `bool` | `false (firefox.js AS defaults)` | false: newtab telemetry off. | privacy-close-list; REAL AS key; unshipped. |
| `browser.newtabpage.activity-stream.feeds.telemetry` | `bool` | `AS store key (Store.sys.mjs:121)` | false: newtab feed telemetry off. | privacy-close-list; REAL AS store key set dynamically under the activity-stream namespace; unshipped. |
| `messaging-system.rsexperimentloader.enabled` | `bool` | `N/A - key absent from tree` | no effect: unknown key, ignored by libpref. | HALLUCINATED. Grep of the whole FF_SRC tree returns zero hits. INERT noise. |
| `browser.ping-centre.telemetry` | `bool` | `N/A - key absent from tree` | no effect: unknown key, ignored. | HALLUCINATED. Zero hits in tree. INERT noise. |
| `toolkit.telemetry.coverage.opt-out` | `bool` | `N/A - key absent from tree` | no effect: unknown key, ignored. | HALLUCINATED. Zero hits in tree. INERT noise. |
| `browser.attribution.enabled` | `bool` | `N/A - key absent from tree` | no effect: unknown key, ignored. | HALLUCINATED. Zero hits in tree. INERT noise. |

## API Surface

| Symbol | Description | Side Effects |
|--------|-------------|--------------|
| `user_pref(key, value)` | libpref user-branch setter read on every profile init. | Sets the user-branch value; overrides app defaults, loses to policies.json locks. |

## Kill Switches

### `NEW_FILES/user.js:6-8 (gpu-process trio)`
- **Condition:** read at profile init
- **Effect:** keeps the GPU process off on Wayland; prevents the black-window failure
- reversible
- Comment out to restore platform default; expect a black window on this Wayland build.

### `NEW_FILES/user.js:21-31 (VA-API enable + zero-copy)`
- **Condition:** read at profile init
- **Effect:** forces VA-API in RDD and bypasses gfxInfo for zero-copy
- reversible
- Belt for gfxPlatformGtk.cpp:283 UserForceEnable.

### `NEW_FILES/user.js:51-53 (av1/vp9 off)`
- **Condition:** read at profile init
- **Effect:** blocks AV1/VP9 at the pref layer so H.264 is negotiated
- reversible
- Belt for the compiled-in DecoderTraits patch.

### `user.js.privacy-close-list.js:14-23 (10 keys)`
- **Condition:** would apply at profile init IF deployed
- **Effect:** closes 6 real surveillance/experiment channels; 4 lines are inert
- reversible
- UNSHIPPED staging fragment; not wired into any deploy path found.

## Dead Code

- **`user.js.privacy-close-list.js: messaging-system.rsexperimentloader.enabled, browser.ping-centre.telemetry, toolkit.telemetry.coverage.opt-out, browser.attribution.enabled`** — None of these keys exist anywhere in the FF_SRC tree; libpref ignores unknown keys. (risk: Removing them changes nothing functionally; keeping them misleads readers into believing a channel is closed. Low risk either way; prefer replacing with real keys.)
- **`NEW_FILES/user.js:13 gfx.x11-egl.force-enabled`** — No effect in a cairo-gtk3-wayland build; InitX11EGLConfig is compiled out under #ifdef MOZ_X11. (risk: None. Kept intentionally for pref-list clarity; self-documented.)

## Performance

- **CPU:** Not benchmarked in this room. Hardware H.264 decode keeps video off the CPU on Ivy Bridge.
- **MEMORY:** Reference machine is 16 GiB, UMA-shared with the HD 4000. Distribution targets are ~4 GB. No per-pref memory measurement.
- **IO:** The unshipped privacy list, if deployed, would remove a few background egress connections (discovery, crash-report probes).
- **NOTES:** The in-file claim 'IMC bandwidth from ~2500 MiB/s to ~500 MiB/s' and '~4x extra GPU memory bandwidth' are author comments, NOT independently measured here. Treat as not measured.

## Security

- **Remote execution:** None. Declarative prefs only; no code path.
- **Data handling:** NEW_FILES/user.js sends nothing. The privacy list closes egress channels; it does not open any.
- **Attack surface:** None reachable by a remote party. Requires local write access to the profile, which already implies control.
- **Notes:** The privacy list header states none of its entries touch DRM/WebAuthn/WebRTC/PKI/sandbox (the five pillars). Not independently re-audited pillar-by-pillar here.

## Error Conditions

| Error | Cause | Remedy |
|-------|-------|--------|
| `Black window on Wayland` | GPU process re-enabled or user.js not present in profile | Confirm gpu-process trio present and false; confirm file at obj-*/tmp/profile-default/user.js. |
| `Video refuses to play` | VA-API not initialised; hardware-only policy rejects software fallback | Verify media.ffmpeg.vaapi.enabled=true and i965 driver present. |
| `Unknown pref shown as user-set with no default` | One of the 4 hallucinated keys | Replace with a real key or delete the line. |

## Tasks

### Confirm the pref files and their SHAs

Verify what is actually in the room before trusting the docs.

**Prerequisites:**
- Checkout of the patches repo

**Step 1:** wc -l patches/new.patches/10.OVERRIDES/NEW_FILES/user.js
  - Expected: 53
**Step 2:** grep -c user_pref patches/new.patches/10.OVERRIDES/NEW_FILES/user.js
  - Expected: 11
**Step 3:** wc -l patches/new.patches/10.OVERRIDES/user.js.privacy-close-list.js
  - Expected: 23

**After this task:** File inventory matches this document.

### Prove the four hallucinated keys are absent from the source

The four keys must be shown to exist nowhere, not merely assumed.

**Prerequisites:**
- FF_SRC=the source tree

**Step 1:** for k in toolkit.telemetry.coverage.opt-out browser.ping-centre.telemetry browser.attribution.enabled messaging-system.rsexperimentloader.enabled; do grep -rIl -F "$k" $FF_SRC && echo FOUND $k || echo ABSENT $k; done
  - Expected: ABSENT for all four.

**After this task:** The four keys are confirmed inert.

### Verify the C++ that these prefs back

The zero-copy and codec prefs are belts for compiled-in code; confirm that code exists.

**Prerequisites:**
- FF_SRC=the source tree

**Step 1:** sed -n '276,283p' $FF_SRC/gfx/thebes/gfxPlatformGtk.cpp
  - Expected: GORILLA UserForceEnable block gated by StaticPrefs::media_gorilla_hardware_only_mode().
**Step 2:** grep -n 'GORILLA HW-ONLY POLICY' $FF_SRC/dom/media/platforms/PDMFactory.cpp
  - Expected: line 456.

**After this task:** The pref-layer belts are confirmed to match real source.

## Troubleshooting

**Symptom:** Black window on Wayland
**Cause:** GPU process enabled or user.js missing from profile
**Remedy:** Ensure the gpu-process trio is present and false; confirm file deployed to the profile
**Verify:** about:support > Graphics shows GPU process not running; window renders.

**Symptom:** Video will not play
**Cause:** VA-API not initialised; software fallback rejected by policy
**Remedy:** Set/confirm media.ffmpeg.vaapi.enabled=true; verify i965 driver
**Verify:** about:support Media shows VA-API available; H.264 clip plays.

**Symptom:** Privacy line appears set but does nothing
**Cause:** One of the four hallucinated keys
**Remedy:** Replace with the real key name or delete
**Verify:** grep the key across FF_SRC returns zero hits.

## Technical Debt

🟡 **LOW** — Four hallucinated pref keys in user.js.privacy-close-list.js → Replace with the real equivalents (or delete): the coverage/ping-centre/attribution/experiment-loader intents should map to keys that actually exist, or be dropped so the file does not overstate coverage.
🟠 **MEDIUM** — privacy-close-list.js is unshipped and not wired into any deploy path → Either wire it into the profile deployment (as Topic 14's egress lockdown intends) or mark it clearly as a draft so it is not mistaken for active hardening.
🟡 **LOW** — Stale narrative in 00_OVERRIDES_HISTORY_AND_ROADMAP.md (single ~1121-line 'sole' user.js, 8GB RAM) → The 8GB figure and 'sole user.js' claim are wrong; reference machine is 16 GiB UMA and the 1,121-line file is at patches/Mozconfig/user.js. Reconcile the roadmap with the master log correction.
🟡 **LOW** — In-file bandwidth numbers are unmeasured claims → Either attach a measurement (e.g. intel_gpu_top before/after) or reword the comment as an estimate.

## Impact If Removed

Remove NEW_FILES/user.js and the profile falls back to platform defaults: the GPU process can re-enable on Wayland (black window), VA-API zero-copy loses its pref-layer belt, and AV1/VP9 can be attempted where no hardware decoder exists. The compiled-in C++ policies still hold the hardest lines, but the defence-in-depth and the graphics-blocklist bypass are gone. Remove user.js.privacy-close-list.js and nothing changes today, because it is not deployed.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| NEW_FILES/user.js: 53 lines, 11 keys, sha256 e89ddfd918a4b3fd | 📄 stated in input | NEW_FILES/user.js  (js, 53 lines, sha256:e89ddfd918a4b3fd) |
| privacy-close-list.js: 23 lines, sha256 7f0c766ee594d5a0 | 📄 stated in input | user.js.privacy-close-list.js  (js, 23 lines, sha256:7f0c766ee594d5a0) |
| GPU process kept off to avoid a black window on Wayland | 📄 stated in input | so EGL surface creation fails and the window stays black |
| VA-API decode runs in the RDD process | 📄 stated in input | VA-API decode still works via the RDD process (media.rdd-ffmpeg.enabled) |
| Hardware-only policy in PDMFactory.cpp rejects non-hardware decode | 📄 stated in input | The Gorilla hardware-only policy (PDMFactory.cpp) rejects ALL video unless the decoder reports DecodeSupport::HardwareDecode |
| H.264 must not silently fall back to software decode | 📄 stated in input | H.264 never silently falls back |
| LIBVA_DRIVER_NAME=i965 must be set in /etc/environment | 📄 stated in input | LIBVA_DRIVER_NAME=i965 must be set in /etc/environment (it is) |
| force-surface-zero-copy defaults to 2 (gfxInfo-controlled) | 📄 stated in input | media.ffmpeg.vaapi.force-surface-zero-copy defaults to 2 (gfxInfo-controlled) |
| State 1 skips the gfxInfo GetFeatureStatus call | 📄 stated in input | State 1 skips the gfxInfo GetFeatureStatus call entirely |
| The zero-copy prefs are a belt for the C++ UserForceEnable fix | 📄 stated in input | the Gorilla UserEnable() at gfxPlatformGtk.cpp:282 is overridden |
| gfx.webrender.compositor defaults to false on Linux | 📄 stated in input | gfx.webrender.compositor defaults to false on Linux |
| IMC bandwidth 2500->500 MiB/s is an in-file claim, not measured | 📄 stated in input | cutting IMC bandwidth from ~2500 MiB/s to ~500 MiB/s |
| Native compositor also flips UploadSWDecodeToDMABuf() true | 📄 stated in input | UploadSWDecodeToDMABuf() also becomes true |
| AV1/VP9-off is a belt for the compiled-in DecoderTraits CANPLAY_NO patch | 📄 stated in input | the compiled-in Gorilla DecoderTraits patch that returns CANPLAY_NO for VP9/AV1/WebM |
| gfx.x11-egl.force-enabled is a no-op in a cairo-gtk3-wayland build | 📄 stated in input | gfx.x11-egl.force-enabled has no effect in a cairo-gtk3-wayland build |
| The privacy list claims none of its keys touch the five pillars | 📄 stated in input | none touch DRM/WebAuthn/WebRTC/PKI/sandbox (the 5 pillars) |
| Destination is the profile, not the source tree (README.txt) | 📄 stated in input | user.js goes to: obj-x86_64-pc-linux-gnu/tmp/profile-default/user.js (profile, NOT source tree) |
| Verified outside the 2-file input: the four privacy keys (coverage.opt-out, ping-centre.telemetry, attribution.enabled, rsexperimentloader.enabled) are absent from the entire FF_SRC tree, and the ~1,121-line user.js lives at patches/Mozconfig/user.js | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Auto-generated DITA-structured developer documentation.*


---

# ═══ MERGED DOCUMENT: 10-overrides.LAYMAN.md (verbatim · sha256:53e96eb889378b74 · merged 2026-08-04) ═══

# The Override Layer: Preference Files That Get the Final Say When Firefox Starts — Plain Language Guide

> Generated 2026-08-04 from `10.OVERRIDES`

---

## Should You Run This?

Run NEW_FILES/user.js only on the hardware it is written for: an Intel HD 4000 (Ivy Bridge) laptop on Wayland with the i965 VA-API driver. On that target it is safe and it is what makes video and graphics work. It is NOT a generic privacy pack and NOT tuned for other chips. Do not treat the draft privacy-close-list as active — it is unshipped, and four of its lines are dead.

## Worst Case, Honestly

The realistic worst outcome is a cosmetic or playback problem, not a data leak. If the GPU-process lines were wrong or missing, Firefox on this Wayland build shows a black window. If the VA-API lines were wrong, video would refuse to play, because this build's hardware-only rule rejects software decoding. Neither loses your data or your money. The four non-existent settings in the draft privacy file are inert: Firefox ignores them, so the worst they do is mislead a reader into thinking a door is shut when that line never touched anything.

## What Data This Touches

These files do not send any data anywhere. NEW_FILES/user.js is entirely about graphics and video on your own machine; nothing in it phones home. The draft privacy list is the opposite of surveillance: every line it sets is meant to CLOSE a Mozilla tracking or experiment channel (add-on recommendations, unsent-crash probes, the experiment loader). But that draft is not deployed, so today it changes nothing on your machine either way.

## Before You Trust It

You are about to let settings written by someone else steer your browser's graphics and video. You can confirm what they do without reading code.

**Step 1:** Open the file: patches/new.patches/10.OVERRIDES/NEW_FILES/user.js
  - Look for: 53 lines, 11 lines starting with user_pref. Every line has a plain-English comment above it. Nothing sends data.
**Step 2:** After Firefox is running, open about:support and find the Media section.
  - Look for: Hardware H.264 / VA-API listed as available. If video plays and the window is not black, the GPU-off and VA-API-on settings are doing their job.
**Step 3:** Open about:config and search for one of the four suspect keys, e.g. browser.ping-centre.telemetry.
  - Look for: It shows as a user-added string with no matching built-in default, confirming it is an unknown key Firefox ignores.
**Step 4:** Confirm the big file is elsewhere: look at patches/Mozconfig/user.js.
  - Look for: About 1,121 lines. This proves the 'only file, in this room' story is wrong.

## The Big Picture

This folder holds preference files. A preference file is a plain-text list of settings, one per line, that Firefox reads when it starts up. Firefox reads these AFTER its own built-in defaults, so whatever these files say wins. They are the last word before the browser opens a window.

This particular room (10.OVERRIDES) holds two small files. The first, NEW_FILES/user.js, is 53 lines and sets 11 real settings. Every one of them is about graphics and video on this exact laptop: keep the GPU helper process OFF on the Wayland display system (because turning it on makes the window go black on this build), and steer all video onto the chip's built-in H.264 hardware decoder. The second file, user.js.privacy-close-list.js, is a 23-line draft that would switch off some of Mozilla's tracking and experiment features. It is not wired into the build yet, and four of its ten lines name settings that do not exist in Firefox.

One thing to be clear about: the often-repeated claim that this room contains a single 1,100-line 'only' user.js is wrong. There really is a big user.js of about 1,121 lines, but it lives elsewhere in the project (at patches/Mozconfig/user.js), not here. Across the whole project there are three such files, and this room owns two of them. All of them are copied into your Firefox PROFILE, never into the program's source code.

## Key Concepts

| Name | What It Means | Real-World Comparison |
|------|--------------|------------------------|
| `user.js` | A settings file Firefox reads on every launch; its lines overwrite the defaults. | A sticky note taped to the dashboard that says 'ignore the factory settings, use these instead' — read fresh every time you start the car. |
| `Profile (not source tree)` | The folder where Firefox keeps your settings, history, and this user.js. The file goes there, not into the program's code. | Your seat and mirror settings live in the car's memory, not welded into the chassis. |
| `GPU process on Wayland` | A separate helper program Firefox normally uses for graphics. On this build's Wayland display it fails and the window turns black, so it is deliberately left off. | A second engine that, on this specific car, stalls the whole vehicle — so you tape its ignition switch to OFF. |
| `VA-API in the RDD process` | Hardware video decoding still happens, just in a different helper (the RDD process), so turning the GPU process off does not stop video. | You disconnected one engine, but the built-in video motor sits in a different bay and keeps running. |
| `Hallucinated preference` | A setting name that was written down but does not actually exist in Firefox. Firefox silently ignores it, so it does nothing — good or bad. | A light switch screwed to the wall with no wire behind it. Flipping it changes nothing. |

## How It Works — Step by Step

### Step 1: Firefox reads the file from your profile

On every launch Firefox opens user.js in the profile folder and applies each line. README.txt in this room states the destination exactly: obj-x86_64-pc-linux-gnu/tmp/profile-default/user.js — the profile, not the source tree.

### Step 2: The GPU helper process is switched OFF

Three lines set layers.gpu-process.enabled, layers.gpu-process.force-enabled, and media.gpu-process-decoder to false. On this Wayland build the GPU-process window has no Wayland handle to draw into, so leaving it on paints a black window. Off is the working state here.

### Step 3: Hardware H.264 video is routed to the RDD process

Two lines turn on media.ffmpeg.vaapi.enabled and media.ffmpeg.vaapi.decode.force-enabled. VA-API is the chip's built-in H.264 decoder, and it runs in the RDD helper — a different process from the GPU one that was just switched off. So video keeps working.

### Step 4: The graphics blocklist is stepped around for two speed features

Firefox keeps a blocklist of graphics chips it distrusts. Two lines (force-surface-zero-copy set to 1, and gfx.webrender.compositor.force-enabled) tell Firefox to skip that check for zero-copy video and the native Wayland compositor, so decoded frames go straight to the screen instead of being copied around. The in-file comment says this cuts memory-bandwidth use, but that number is not independently measured here.

### Step 5: Newer video formats are blocked so sites serve H.264

Three lines switch off AV1 and VP9 (media.av1.enabled, media.vp9.enabled, media.mediasource.vp9.enabled). This makes sites like YouTube offer the H.264 version, which is the only one this laptop's chip can decode in hardware. It is a backup for a rule already compiled into the browser.

### Step 6: A separate draft would close tracking doors (not active yet)

The privacy-close-list file lists ten Mozilla channels to switch off. Six are real settings; four are names that do not exist in Firefox and do nothing. The file is a staging draft and is not copied into any build today.

## Quirky Things Worth Knowing

### The GPU process is turned off ON PURPOSE

It feels backwards to switch off graphics acceleration, but on this build's Wayland the GPU process paints a black window. Video acceleration is unaffected because it lives in a different process (RDD).

### There are three user.js files, and the biggest is not in this room

The famous ~1,121-line file is at patches/Mozconfig/user.js. This room's NEW_FILES/user.js is only 53 lines. Anyone told 'the one and only 1,100-line user.js is here' has been misinformed.

### Four privacy settings are spelled for switches that do not exist

toolkit.telemetry.coverage.opt-out, browser.ping-centre.telemetry, browser.attribution.enabled, and messaging-system.rsexperimentloader.enabled appear nowhere in Firefox's code. They are harmless but they are noise, and they can fool a reader into a false sense of coverage.

### One line is a deliberate no-op kept for tidiness

gfx.x11-egl.force-enabled is set to false even though, as its own comment admits, it does nothing in a Wayland-only build. It is kept only to keep the settings list clean and unsurprising.

### These files live in your profile, not the program

You can open, read, edit, and delete them without rebuilding Firefox. That is the whole point of this layer — fast changes without a 10-20 minute recompile.

## What This Means For You

### Battery, Processor & Memory

The zero-copy and native-compositor lines are intended to reduce graphics memory-bandwidth on this laptop's shared-memory (UMA) graphics. The in-file comment claims a drop from about 2500 MiB/s to about 500 MiB/s, but that figure is stated in the comment and is NOT independently measured here — treat it as the author's claim, not a verified result. The reference machine has 16 GiB of RAM shared between the CPU and the HD 4000 graphics; the laptops this build targets for others have around 4 GB.

### Speed

Video decoding stays on the hardware decoder rather than the slower software path, which matters on an Ivy Bridge chip. No before/after speed numbers were measured for this room.

### Your Privacy

NEW_FILES/user.js has no effect on tracking; it is purely graphics and video. The draft privacy list would close add-on-recommendation, crash-report, and experiment channels — but it is not deployed, so today it changes nothing.

### Your Internet

NEW_FILES/user.js does not change your network use. If the draft privacy list were shipped, it would cut a few background connections (add-on discovery, crash-report probes). Not measured in numbers.

## The Off Switch

**What it is:** The whole file is a bank of individual switches. Each line is one setting you can turn off by deleting the line or putting // in front of it, then restarting Firefox.

**Without it:** Firefox falls back to its own defaults: the GPU process could come back on (black window on this Wayland build), and AV1/VP9 could be attempted (no hardware decoder for them here).

**Think of it like:** A row of clearly labelled breaker switches in a fuse box. Each one controls exactly one circuit, and you can flip any single one without touching the rest.

## How this file reaches your browser

**Before you start:**
- A built Firefox 154 profile directory
- Wayland session on Intel HD 4000 with the i965 VA-API driver

**Step 1:** The build copies NEW_FILES/user.js to the profile path shown in README.txt (obj-.../tmp/profile-default/user.js).
  - You should see: The file is present in the profile before first launch.
**Step 2:** Start Firefox.
  - You should see: The window draws normally (not black), and H.264 video plays on the hardware decoder.

## If Something Goes Wrong

**The browser window is black on Wayland.**
The GPU process came back on, or user.js was not copied into the profile.
What to do: Confirm the three gpu-process lines are present and set to false, and that the file is in the profile folder, then restart.

**Video will not play.**
This build rejects software video decoding, and VA-API is not initialising.
What to do: Check that media.ffmpeg.vaapi.enabled is true and that the i965 driver is installed; see 01.MEDIA for the hardware requirement.

**A privacy setting looks set but has no effect.**
It is one of the four non-existent keys; Firefox ignores unknown settings.
What to do: Treat those four lines as noise until they are replaced with real setting names or removed.

## Why a Developer Would Do This

A developer keeps these as editable files because a settings change should not cost a 10-20 minute rebuild, and because the safest place to override a factory default that an update might silently reset is the layer that is re-read on every launch. Keeping the reasons in comments is what lets a non-programmer audit the machine they are trusting.

## Why It Matters That You Can Read This

Every line in these files is plain text with a comment above it explaining WHY. You do not have to trust a claim — you can read the exact setting and its reason yourself. The project also keeps GORILLA markers in the matching source code so a change can be traced from the setting here to the C++ that enforces it. In a closed browser these switches are hidden, undocumented, and can be changed by an update without telling you. Here, if a setting is wrong (like the four non-existent privacy keys), anyone reading the file can spot it — which is exactly how that problem was found.

## Glossary

**user.js** — A Firefox settings file in the profile folder whose lines are applied on every startup, overriding the defaults.

**Profile** — The per-user folder where Firefox stores settings and data; user.js lives here, not in the program's code.

**VA-API** — The Linux interface that lets Firefox use the graphics chip's built-in video decoder instead of the processor.

**RDD process** — The separate Firefox helper that runs media decoding, kept apart from the GPU process.

**Zero-copy** — Sending a decoded video frame straight to the screen without copying it through memory again.

**Hallucinated preference** — A setting name that does not exist in Firefox; it is written down but does nothing.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| NEW_FILES/user.js is 53 lines with 11 real settings | 📄 stated in input | NEW_FILES/user.js  (js, 53 lines, sha256:e89ddfd918a4b3fd) |
| GPU process kept off on Wayland to avoid black window | 📄 stated in input | so EGL surface creation fails and the window stays black |
| VA-API decode runs via the RDD process | 📄 stated in input | VA-API decode still works via the RDD process (media.rdd-ffmpeg.enabled) |
| Destination is the profile, not the source tree | 📄 stated in input | user.js goes to: obj-x86_64-pc-linux-gnu/tmp/profile-default/user.js (profile, NOT source tree) |
| Bandwidth ~2500 to ~500 MiB/s is a comment claim, not measured | 📄 stated in input | cutting IMC bandwidth from ~2500 MiB/s to ~500 MiB/s |
| The ~1,121-line user.js is at patches/Mozconfig/user.js, not this room | 🤖 model inference | *(none — model judgment)* |
| Four privacy keys do not exist anywhere in the Firefox source | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Human Track. Its Developer Track twin covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*


---

# ═══ MERGED DOCUMENT: 10-overrides.PRECHECK.md (verbatim · sha256:fb4362150f6abe1e · merged 2026-08-04) ═══

# Offline Pre-Check: 10-overrides

*Generated 2026-08-04 07:05:39 by rules only. No model was involved, so everything below is a deterministic finding about the files as they are on disk.*

## Files Scanned

| File | Language | Lines | Code | Complexity | SHA-256 |
|---|---|---|---|---|---|
| `NEW_FILES/user.js` | js | 53 | 11 | 3 | `e89ddfd918a4b3fd` |
| `user.js.privacy-close-list.js` | js | 23 | 10 | 2 | `7f0c766ee594d5a0` |

## Findings

🔴 P0: 0 · 🟠 P1: 0 · 🟡 P2: 0 · 🟢 P3: 0

*No findings. The rules found nothing wrong; this is not a statement that the code is correct.*


---

# ═══ MERGED DOCUMENT: 10-overrides.PRECHECK.json (verbatim · sha256:637b552b1c40a648 · merged 2026-08-04) ═══

```json
[]
```
