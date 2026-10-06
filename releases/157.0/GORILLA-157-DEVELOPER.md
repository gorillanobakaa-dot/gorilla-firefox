# Gorilla Unleashed 157.0 for Windows: patch set, decision register, build and verification (`gorilla-patchset/patches`, `decisions/PRODUCT-DECISIONS.yaml`, Fieldkit `build-harness`)

> Written 2026-10-03 and 2026-10-04 for the 157.0 release, build 27 (BuildID `20261004224302`). The full release leak test last ran on build 26, not on this build; the release notes say what it found and what build 27 changed.

---

## Purpose

Gorilla Unleashed 157.0 is Firefox 157.0 (`FIREFOX_157_0_RELEASE`, `fdd757a2e09c9471cddf383e64e631e4ce178499`) with a patch set that removes every network caller the browser would use on its own initiative, removes the AI and machine-learning features, seals the add-on system around one bundled extension (uBlock Origin 1.74.0), and applies the maintainer's product decisions. The governing rule is decision D-157-00: the browser contacts only the sites the user opens; the only exceptions are recorded trade-offs.

**Trust level.** The release is a Windows x86-64 build, distributed as an unsigned installer and an unsigned zip, each with a SHA-256 fingerprint. It is trusted to the extent of the proofs run on that exact build: the post-install proof rows, the decision register in strict mode, the claims audit and the leak gate in release mode. For build 27: every post-install row ok; visual check 0 failures (20 static and 47 run-time failures before builds 22 to 26); claims audit 0 contradicted, 0 failing patches (456), the 58 stale entries retired and kept on record; decision register strict OK (34 entries: 31 enforced, 3 trade-offs, 0 pending). Release leak gate: The four-hour release leak test last ran in full on build 26 (run `20261004-165832`) and **failed**. One finding was real: through a proxy, a page on `127.0.0.1` could reach `10.0.0.1` and `192.168.0.1`. Build 27 fixes it in `nsHttpChannel.cpp` (only the same address space counts). The other failures were faults of the test itself (processes seen dying counted as lingering, DNS aliases, another program's DNS lookup, run-to-run comparison), since corrected, and items waiting for the maintainer's approval, since approved at the maintainer's terminal. **PASS on this exact build** (6 October 2026, 10:08 to 14:08, run `20261006-100814`): all 19 checks, every scene three times, with packet capture. Getting there took four full runs on this build; the two failed runs before it failed only on faults of the test itself (it lost track of the browser window it had to close; it blamed the browser for traffic from other programs on the test machine), and the reference check, which fails on the first run of every version by design. Each fault is fixed in the test, and the test now names the program behind every captured packet. Anything those proofs do not measure is not claimed. In particular, real-link speed, battery and long-running behaviour beyond the leak gate's scenes are not measured.

**Scope.** Windows only. Group `01.MEDIA` (VA-API, PulseAudio) is Linux-only and not applied. Linux builds use the separate `patchset-155.0b4/` set, which must never be applied to the same tree.

## Known Alternatives Considered

Only alternatives the source documents record:

- **Switching features off with preferences only** was the earlier approach. It was rejected for network callers because a preference can be flipped back; every caller is now cut at the source with a `GORILLA UNLEASHED - PHYSICAL LOCK` early return, and the preferences are locked as a second layer (D-157-21 "switched off as well as cut").
- **CRLite for revocation** was rejected: its filters arrive only through Remote Settings, which is cut. **Live OCSP** was rejected because it tells certificate authorities which sites the user visits. Chosen: the bundled OneCRL dump applied offline at start-up (D-157-07).
- **`privacy.resistFingerprinting` on by default** was rejected because users rejected forced UTC time, light pages and canvas prompts before; it stays opt-in, with `privacy.fingerprintingProtection` locked on (D-157-06).
- **Locking `media.peerconnection.ice.no_host`** was tried and removed on 3 October because it broke same-LAN calls; local addresses stay hidden by mDNS (D-157-06).
- **A compression proxy for slow links** was rejected as a third-party service (D-157-00); Gorilla.Satellite mode only changes what the browser fetches, what it keeps on disk and how long it waits.
- **Installing with the NSIS installer** was replaced by unpacking the hashed zip after the installer once exited 0 having installed nothing.
- **Porting the published patch set** was replaced by porting a snapshot captured from the built 155.0.1 tree, because the published set did not rebuild the shipped browser.

## Architecture

**Patch groups.** `patches/` is cut against pristine 157.0 and applied in policy order; inside each group: every `*.patch` sorted by path with `patch -p1 --forward --no-backup-if-mismatch --fuzz=0`, then `NEW_FILES/`, then `REPLACE_FILES/` (byte-exact, for binaries and line-ending changes), then `DELETED_FILES.manifest.txt`.

| Group | Patch files | What it carries |
|---|---|---|
| `02.GPU` | 3 | Graphics blocklist relaxed for old Intel, AMD and NVIDIA chips |
| `03.NETWORKING` | 3 | DNS resolver, HTTP/3 socket buffers, upload chunking (DNS pool restored to upstream in this release) |
| `04.PERFORMANCE` | 4 | Cycle-collector scheduling, stencil telemetry compiled out, a `Maybe` build fix |
| `05.PREFS` | 4 | Built-in settings (`firefox.js`, `all.js`, `StaticPrefList.yaml`, locale default) |
| `06.QUOTA` | 1 | Storage quota |
| `07.TOOLKIT` | 13 | AI, suggestion and remote features removed; add-on and theme install paths cut ("API Lobotomy") |
| `08.Look` | 232 | Dark theme, Gorilla branding, reworded English strings |
| `09.REMOTE` | 2 | Marionette and Remote Agent hard-wired off |
| `11.FONT.SYSTEM` | 4 | Font list handling |
| `12.MOZAMBIQUE.DRILL` | 2 | Normandy and Nimbus loaders neutralised, plus `distribution/policies.json` |
| `13.TELEMETRY.KILL` | 22 | Glean recording a compile-time no-op; FOG and memory telemetry stopped |
| `16.SNAPSHOT.DELTA.2026-08-12` | 84 | The August 2026 chrome, address-bar, sidebar and settings work |
| `20.SNAPSHOT.DELTA.155.0.1` | 8 | Bundled uBlock Origin, AI Window stub, built-in extension registration, the 432-file AI excision |
| `21.PORT.FIXES.157` | 5 | Repairs needed to carry the set onto 157 |
| `22.EGRESS.LOCKDOWN.157` | 28 | Every network caller, identifier and helper executable cut at the source for 157 |

`10.OVERRIDES` and `14.EGRESS.LOCKDOWN` hold documents only; `01.MEDIA` holds 20 Linux-only patches. Total: 435 patch files, 1,825 hunks. Groups 21 and 22 are re-exported from recorded hand steps (`export-hand`); after the build 21 re-export, `21.PORT.FIXES.157` holds 9 patches and `22.EGRESS.LOCKDOWN.157` 46 (457 patch files in all, 437 in the groups enabled for Windows).

**Decision register.** `decisions/PRODUCT-DECISIONS.yaml` holds 34 entries on build 27 (31 enforced, 3 trade-offs, 0 pending); D-157-32 and D-157-33 cover Gorilla.Satellite mode. Check kinds: `pref` (value and lock in the shipped package), `tree_contains`, `tree_lacks`, `omni_absent`, `installed_absent`, `installed_present`, `mozconfig_has`, `image_sharp` (edge energy against the master) and `fieldkit_test`. `build-harness decisions --strict` and the post-install `decisions` row fail on any enforced entry whose check fails and, in strict mode, on any pending entry. The leak-gate baseline stores the register's sha256, so a baseline always names the decisions it was taken with.

**Gorilla.Satellite mode (D-157-32, D-157-33).** `browser/modules/GorillaLinkMode.sys.mjs` observes the integer pref `gorilla.linkmode` (0 Off, 1 Satellite, 2 Very slow link) and writes its level's values to the default branch, remembering the shipped defaults so level 0 restores them exactly; user-set values always win, and a locked pref keeps its locked value. The level is chosen with the toolbar button right of the address bar ("Gorilla.Satellite mode: Off/Satellite/Very slow link", black menu, cyan text, hover explanations) or in Settings > General > Network. The menu also carries the per-site switches "This site: show the normal (desktop) version" and "This site: allow JavaScript", and tick-boxes for mobile pages and for no-JavaScript. Satellite and Very slow link keep the disk cache across restarts and write HTTPS pages to it; with the mode Off the browser ships `privacy.clearOnShutdown.cache` true (the cache is emptied at shutdown) and `browser.cache.disk_cache_ssl` false (HTTPS pages are never written to disk), which is why the mode's disk cache had held nothing before builds 22 to 26. The cache also sized itself at start-up, before the level applied, with Gorilla's shipped capacity 0 and evicted everything (found with Firefox's own cache log); `browser.cache.disk.capacity` now ships at 262144 while the disk cache stays off with the mode Off. In Very slow link a cached page opens without revalidation, also for `must-revalidate` responses (`VALIDATE_NEVER`); Reload still fetches. `nsHttpChannel` sends `Save-Data: on` only at level 2, which switches `gorilla.network.save_data` on (it ships false).

**Dependencies and trust boundary.** At run time the browser trusts the system DNS resolver (TRR mode 5), the bundled OneCRL dump, uBlock Origin's list hosts, and Google and Cisco for the two GMP plug-ins, fetched on demand with sha512 and size checks against the built-in `gmp-sources/*.json`, as anonymous requests. At build time the trust chain is the pinned upstream commit, the patch set, Mozilla's toolchains fetched by `mach`, and the maintainer's build laptop. The release artefact is not code-signed.

**Attack surface that remains by design.** WebRTC's STUN candidate reveals the public address to a page that starts a call. Manual updates mean a known upstream vulnerability stays open until the user installs a new build. Safe Browsing is off (D-157-25). Ordinary site certificates are not revocation-checked (D-157-07). Unlocked preferences can still be changed in `about:config`.

## Flags & Configuration

- `gorilla.linkmode` (int, default 0): Gorilla.Satellite mode level.
- `gorilla.network.save_data` (bool, default false): the `Save-Data` header; set only by level 2.
- `browser.cache.disk.capacity` (int, 262144 shipped): the size the disk cache takes at start-up; the disk cache itself stays off while Gorilla.Satellite mode is Off.
- Build configuration (`config/mozconfig.win64`, `gorilla-patchset/windows/mozconfig.win64`, `gorilla-patchset/mozconfig`): `--disable-updater`, `--disable-maintenance-service`, `--disable-crashreporter`, `--disable-default-browser-agent`, `--disable-webspeech`, `--disable-necko-wifi`, `--disable-parental-controls`, checked by D-157-01 and D-157-22.
- Network settings changed in this release: `network.http.http2.send-buffer-size` 131072 to 0; `network.http.response.timeout` 15 to 300; DNS resolver pool back to `MaxResolverThreads()` (the 154-era patch had become a cap of 16 against upstream's 64).
- `browser.ai.control.*` (eight string prefs): `"blocked"`, locked. They had been set to boolean `false`, which libpref drops as a type mismatch.

## Kill Switches

- **Gorilla.Satellite mode:** Off, from the toolbar button, Settings > General > Network, or `gorilla.linkmode` = 0, restores the shipped defaults.
- **Video plug-ins:** the GMP prefs are locked on by D-157-12; there is no user switch. Removing the decision is the maintainer's call.
- **Every cut network caller:** none by design. A `PHYSICAL LOCK` early return has no preference behind it.
- **Strong fingerprinting:** `privacy.resistFingerprinting`, unlocked, off by default.

## Dead Code

Compiled but unreachable or inert in this build: Normandy, Nimbus, the legacy Telemetry component, Sync and Firefox Accounts (switched off, network callers cut; removal planned in that order); the HWInference IPC glue in `toolkit/components/ml/ipc` (kept because `ipc/glue` and `dom/ipc` depend on it at build time); the Remote Agent and Marionette (enable switch hard-wired false); `AIWindowStub.sys.mjs` and an empty `smartwindow-themes-notice.mjs` stub (kept so 157's importers resolve); `BuiltInThemeConfig`'s map, kept empty for the same reason; the CLD2 language detector (kept for `browser.i18n.detectLanguage` and Reader View).

## Performance

Measured by `build-harness netbench` against local servers (127.0.0.1) through a user-space relay emulating four links, three repetitions, medians. Before: build of 3 October, BuildID `20261003112601`, label `before-build16`. After: build 18, BuildID `20261003155534`, label `after-build18` (this table was not re-run on builds 19 to 26; Gorilla.Satellite mode's measurements follow it).

| Bench | Link | Before | After |
|---|---|---|---|
| B1 article set, cold load | broadband / starlink / geo / austere | 0.75 s / 0.83 s / 3.92 s / 95.6 s | 0.39 s / 0.37 s / 3.21 s / 95.6 s |
| B1 after a restart | austere | 95.7 s (16 requests, everything re-fetched: no disk cache) | 95.6 s (unchanged: with Gorilla.Satellite mode Off there is no disk cache) |
| B2 HTTP/2 up | broadband / geo | 9.67 / 7.92 Mbit/s | 9.87 / 7.97 Mbit/s |
| B3 QUIC buffers granted | local | receive and send granted, 0 failures | unchanged |
| B4 peak private bytes | broadband | 717 MB | 729 MB (within spread; Starlink-like 906 to 770 MB, austere 553 to 586 MB) |
| B5 keep-alive | all | long-lived idle 900 s, 0 failures | unchanged |

Limits recorded by the bench itself: the relay terminates the browser's TCP on loopback, so the HTTP/2 send-buffer cap is not reproduced; loss is modelled optimistically; HTTP/3 is not used through the relay; DNS is not exercised, so the resolver-pool fix is not measured; there is no video fixture. Gorilla.Satellite mode on the same bench (emulated links, 3 repetitions, medians):

| Link | Off | Satellite or Very slow link |
|---|---|---|
| 5 KB/s, 700 ms: first visit | 95.6 s | **41.0 s** (Very slow link) |
| 5 KB/s: after a restart | 95.6 s | **23.7 s** (Very slow link; everything but the page itself comes from the disk) |
| GEO satellite (600 ms, 1% loss): after a restart | 3.78 s | **2.51 s** (Satellite; 1 request instead of 16) |
| Starlink-like: first visit | 0.45 to 0.67 s | 0.43 to 0.56 s (Satellite; no slowdown) |
| The same page again (a page that says must-revalidate, local test, build 25) | asked the site again | **opened from the disk, no request** (Very slow link; Reload still fetches a fresh copy) |

Gorilla.Satellite mode on real sites, over the maintainer's link, empty cache each time; the times at 5 KB/s are computed from the bytes, not timed on a 5 KB/s link:

| Site | As shipped | Very slow link | At 5 KB/s |
|---|---|---|---|
| BBC News | 1,636 KB | 101 KB | about 21 s |
| The Guardian | 1,121 KB | 148 KB | about 30 s |
| DuckDuckGo search | 2,504 KB | 207 KB | about 42 s |
| Reuters | 2,230 KB | 315 KB | about 65 s |
| Wikipedia (Starlink article) | 744 KB | 322 KB | about 66 s |
| CNN | 14,057 KB | 608 KB | about 2 minutes |

Most of the saving comes from leaving JavaScript out; asking for the mobile version barely changes the size on these sites. Not measured: a real satellite link.

## Security

**No remote control plane (D-157-31, builds 20 and 21).** `AboutNewTab.onBrowserReady` no longer awaits `NimbusFeatures.newtabTrainhop.ready()` (with Normandy cut, nothing called `ExperimentAPI.init()` in 157, so the new tab and start page never rendered). Train-hop is cut in `AboutNewTabResourceMapping` (`updateTrainhopAddonState`, `_installTrainhopAddon`, `firstStartupNewProfile` return at once) and `PrefsFeed._getTrainhopConfig` (always empty); `browser.newtabpage.trainhopAddon.xpiBaseURL` is "", locked. Nothing starts Nimbus: `AboutWelcomeParent.waitForNimbusForAboutWelcome`, `DefaultLaunchOnLogin.waitForNimbusReady`, `BackgroundTasksUtils.enableNimbus` and `Normandy.finishInit` return first; `ConfigSearchEngine` no longer reads search parameters from the `searchConfiguration` feature. `Utils.LOAD_DUMPS` returns true: the dummy Remote Settings server URL had silently disabled every packaged dump.

**Local network access is decided before the connection (D-157-16, build 21).** `DnsAndConnectSocket::TransportSetup::SetupStreams` refuses with `NS_ERROR_LOCAL_NETWORK_ACCESS_DENIED` when every resolved address is local or private and `AllowedToConnectToIpAddressSpace` says no, before any socket exists; upstream only checked after TCP connect, so the SYN to an unanswering LAN address left the machine (seen by the release leak gate on build 20). Mixed public/private answers keep upstream's late check. Build 22 closed the proxied path: no local-network access through a proxy. Technique T-157-16-A.

**Build 22 locks.** Nothing is written outside the profile for updates (D-157-01). `mach`'s own build telemetry never runs (`DISABLE_TELEMETRY`). `about:credits` and `about:rights` no longer open mozilla.org; they show the local licence page (D-157-00).

Cut at the source in this release (`22.EGRESS.LOCKDOWN.157` and the hand steps after it): Remote Settings sync, attachments and signatures; region lookup; Web Push and its command-line wake-up; add-on metadata, discovery, abuse reports and update checks; the system add-on updater; the connectivity probe and captive-portal service; legacy telemetry, `pingsender.exe`, `nmhproxy.exe`; the DAP sender; Normandy initialisation; Merino; new-tab feeds; UITour; the MITM-priming request; search partner codes; network geolocation; Safe Browsing list downloads; `desktop-launcher.exe`; four AI-window `about:` registrations. Add-on routes closed: every non-system install, the temporary add-on in `about:debugging`, and sideloaded add-ons in profile, global and registry locations. The Windows content sandbox uses Mozilla's own Windows level (D-157-02).

## Error Conditions

- A refused add-on or theme install raises the `addon-install-gorilla-refused` notification, shown as a doorhanger.
- A level written by Gorilla.Satellite mode to a locked pref is logged to the console and skipped.
- A GMP download whose sha512 or size does not match is refused.

## Tasks

Commands run from the Fieldkit folder in PowerShell on the build laptop, against the task `firefox-157.0-truth`. Builds, installs and the leak gate never run in parallel.

### Know where the migration stands

```powershell
fieldkit build-harness migrate sitrep firefox-157.0-truth
```

Expected: the stage and gate status, the red items, per-group intent progress, open briefs, parked tickets and one next action as a command. Pass: the gate of the current stage is green. Fail: red items listed by id; work them with `migrate work`.

### Check the tree before a build

```powershell
fieldkit build-harness verify firefox-157.0-truth
fieldkit build-harness repair firefox-157.0-truth
fieldkit build-harness truthbound firefox-157.0-truth
fieldkit build-harness decisions firefox-157.0-truth --strict
fieldkit build-harness techniques firefox-157.0-truth
```

Expected: `verify` parses every changed JavaScript file with `node --check`, checks member-of-import, placement, false completions, new files, and the `moz.build` rules (empty assignments, unsorted lists). `truthbound` prints the number of changed files and an empty unexplained list; the last port run explained 1,664 files with none unexplained. `decisions --strict` fails on a pending entry; on build 21 none is pending. `techniques` scans the tree for the patterns each Gorilla technique must handle (Fieldkit `fieldkit/buildh/techniques.py`) and fails on any unguarded place; the build gate runs the same scan. On build 21: T-157-31-A (nothing waits for or starts Nimbus), T-157-31-B (no remotely delivered code or configuration) and T-157-31-C (a lock never switches off built-in data) all hold.

### Build and package

```powershell
fieldkit thermal prove
fieldkit build-harness build-run firefox-157.0-truth
```

Expected: `build gate passed`, the thermal source and its grade, `build OK`, `package OK`, then the package rows (tree unchanged since the gate, installer and zip from this build and of real size, version, every branding icon embedded, crisp logo, installer stub icon, the maintainer's preflight) and `BUILD OK`. Known stops fix themselves: clobber, missing toolchain, corrupt object, excision-creep include, console interrupt, jar manifest undeclared, empty `moz.build` assignment, unsorted `moz.build` list, thermal (cool down and retry). An unknown stop prints `no known fix`.

### Install and prove

```powershell
fieldkit build-harness install firefox-157.0-truth
fieldkit build-harness post-install firefox-157.0-truth
fieldkit build-harness post-install firefox-157.0-truth --drive --only verify_address_bar
```

Expected: a backup, the hashed zip unpacked, start-up caches cleared, the install marker verified, `INSTALL OK`. Post-install rows: `profiles`, `prefs`, `excised`, `startup`, `egress`, `adblock`, `leaks`, `decisions`, `visual`, `claims`, then the maintainer's `verify_installed_build`, `verify_no_phone_home`, `webrtc_selftest`, and `verify_address_bar` (keyboard; only with `--drive` after a countdown). On build 21 every row was ok except `visual` (Gorilla's own images and pages all passed, including RT-CONTENT; the rest were Mozilla's layouts) and `claims` (strict). Builds 22 to 26 took `visual` from 20 static and 47 run-time failures to 0: branding regenerated from the gorilla master (Windows tiles, installer images, wizard bitmaps, PDF document icon), Mozilla's leftover art and macOS-only files removed, layout fixes on `about:license`, `about:checkerboard` and `about:certificate`, a vector icon for the new-tab search button, and a more exact checker (hidden radio buttons, clipping, policy-blocked pages such as `about:telemetry` verified as blocked). `verify_address_bar` needs `--drive`.

### Check the menus and Settings

```powershell
fieldkit build-harness ui-check firefox-157.0-truth
```

Expected: every menu item and Gorilla Settings control at contrast 4.5:1 or more against what is painted, no script errors while menus and Settings open, no empty menus. `--static` checks the ported tree only, without starting a browser. Rules and colours: `docs/GORILLA-THEME-AND-UI.md`.

### Run the leak gate

In an administrator PowerShell:

```powershell
fieldkit build-harness leakgate firefox-157.0-truth --release
```

Expected: every scenario three times, at full duration, with packet capture. Policies include network, telemetry, DNS, process, file system, socket, WebRTC, proxy, IPv6, canary, shutdown, reproducibility, source, binary, allowlist, TLS, regression, dependency and LAN. Pass: release `PASS`. The first baseline may be seeded from a release run whose only failure is the missing baseline (D-157-09), by the maintainer only, and the next release run must pass in full. Read `test-results.json` in the run folder: every FAIL carries its reason. Build 20's run found the local-network gap fixed in build 21. Build 26, run `20261004-165832`: FAIL. Real: LAN_POLICY, a `127.0.0.1` page reached `10.0.0.1` and `192.168.0.1` through the proxy (fixed in build 27: `fromLanPage = trigAddr.GetIpAddressSpace() == target`). Gate faults, corrected in Fieldkit: SHUTDOWN_POLICY counted processes merely seen dying; DNS_POLICY ignored CNAME answers and blamed another program's lookup on the browser; REPRODUCIBILITY compared background traffic approved for every scenario. Waiting for the maintainer, since done at the maintainer's terminal: 4 profile files on the allowlist, the source, binary and dependency dispositions (`leakgate-dispositions`, 150 entries). Build 27 also cut what that review marked reachable after one pref flip: five Merino fetches in `TemporaryMerinoClientShim.sys.mjs`, the null-server fallback of `RustSharedRemoteSettingsService.sys.mjs` (`toolkit.contentRelevancy.*` locked), and `Microsoft.WindowsAppRuntime.dll` dropped from `widget/windows/moz.build` and `package-manifest.in`. Build 27: published before the gate ran (maintainer's decision, 4 October 2026). Release run `20261005-083304` (08:33-12:32): FAIL on SHUTDOWN_POLICY and REGRESSION_POLICY only. REGRESSION: no baseline yet (expected). SHUTDOWN: a gate fault. From the elevated launcher, Firefox's launcher process starts the browser de-elevated through the shell, so the browser was not in the started process's tree; the sampler recorded 0 processes for shutdown-graceful, WM_CLOSE never reached the window, `proc.wait` returned on the exiting launcher and the browser was reported alive 60 s later in all six graceful runs. Fixed in Fieldkit: the sampler, the graceful close and the kill follow every process running from the scene's build copy. Measured on build 27 from a normal shell: WM_CLOSE to the minimised window, all 11 processes gone within 5 s. That run is not eligible as the first baseline (D-157-09 needs the missing baseline to be its only failure), so the next release run seeds it and the one after must pass. To run it unattended, use the Fieldkit tool `leak-gate` (`toolbox/leak-gate-launcher/run-leakgate.ps1`): it asks for administrator rights once, keeps Windows awake, waits for an optional marker file and records the result.

### Audit the public claims

```powershell
fieldkit build-harness claims firefox-157.0-truth --strict
```

Expected: `claims/AUDIT-157.md` regenerated. The run of 3 October 07:57 found 5,575 claims: 484 proven, 4,852 unproven, 193 contradicted, 46 stale; 415 patches, 8 failing. Release check: FAIL. Build 21: 5,703 claims, 0 contradicted, 58 stale (reworded since registered), the rest proven or unproven; 436 patches, 0 failing. Build 27: 5,749 claims, 898 proven, 4,851 unproven, 0 contradicted, 0 stale; 456 patches, 0 failing; the 58 stale entries retired and kept on record.

### Measure the network fixes and Gorilla.Satellite mode

```powershell
fieldkit build-harness netbench firefox-157.0-truth --label after-build17
fieldkit build-harness netbench firefox-157.0-truth --label after-build17-satellite --profile satellite
fieldkit build-harness netbench firefox-157.0-truth --label after-build17-slow --profile slow
```

Expected: YAML and JSON records in `bench/`, with medians, spreads and every unmeasured value marked UNMEASURED.

### Export the hand steps and prove the replay

```powershell
fieldkit build-harness export-hand firefox-157.0-truth
```

Then, in a scratch git index of the build repository, start from the pristine commit, apply groups 02 to 22 in policy order as described in `patches/BASELINE.txt` (GNU patch with `--fuzz=0`, `NEW_FILES`, `REPLACE_FILES`, `DELETED_FILES.manifest.txt`) and write the tree. Pass: the replayed tree hash equals `HEAD^{tree}` of the build, with 0 patch failures. The harness does it in one command: `fieldkit build-harness replay firefox-157.0-truth` (it records the result in the journal). Build 20: 436 patches, 0 failures, both trees `804bf2db46a28e880ca044600dc3fd43a272e7f4`. Build 27: 456 patches, 0 failures, both trees `109fd17fb5b9926e5e0c17115e9a69418b8173be`. Before any push, scan the files that will be published:

```powershell
fieldkit privacy scan <the files to publish>
```

## Troubleshooting

**`no known fix` after a build stop.** The signature and first errors are in the journal. Find the cause, write the fixer as a function, add the signature to the known stops in `fieldkit/buildh/buildrun.py`, add a verify detector when it can be seen before `mach`, add a test, then rebuild. The run is not finished until the next occurrence would fix itself.

**Build refused: no CPU temperature source responds to load.** Run `fieldkit thermal prove`. The proof is capped at 60%, half the threads and 80 °C, and is reused for 12 hours per boot. A lowered power cap left by a crash is restored by the next run.

**The browser starts but the address bar or extensions are dead.** A JavaScript module failed to parse or imports a missing symbol; the build is still green. Run `verify` and `repair`, rebuild, and reinstall: the install clears every start-up cache, which is keyed on the BuildID.

**A removed module is back in `omni.ja`.** Stale output from an earlier build. The build loop sweeps removed paths from `dist/bin` before packaging; check the `excised` row and the `dist-sweep` journal event.

**`decisions` row fails on a `pref` check that the tree sets.** Another default file, or a later block in the same file, redefines the pref; the last definition wins. Settings are edited in place on Mozilla's own lines, and the preflight's prefs-last-wins rule should name the shadowing line. Also check the type: a boolean written over a string pref is dropped.

**`INSTALL NOT OK` with every version row false.** The installer did nothing; installs use the hashed zip and the marker file. Do not trust an exit code.

**A Gorilla menu is unreadable or does nothing.** Run `ui-check`. Build 23 shipped the Gorilla.Satellite mode menu as cyan text on the system's light grey (1.25:1) with a handler that threw, because `Node.ownerGlobal` does not exist in Firefox 157; build 24 fixed both. The same check found the autocomplete pop-up height fix broken by `ownerGlobal` since FF155-era code, and a Settings error on every open (a removed AI pane still imported); both fixed. Follow `docs/GORILLA-THEME-AND-UI.md`.

**Gorilla.Satellite mode keeps nothing across a restart.** Check `privacy.clearOnShutdown.cache`, `browser.cache.disk_cache_ssl` and `browser.cache.disk.capacity` in force; Firefox's cache log shows an eviction at start-up if the capacity was 0 when the cache sized itself.

**A leak-gate run died.** It leaves no `test-results.json` and is not a pass. A watchdog stops the packet capture when the gate process ends; check `pktmon status` if in doubt.

## Technical Debt

- **Normandy, Nimbus, Sync, FxA and telemetry still compiled.** Next action: remove Normandy and Nimbus JavaScript first, then make the telemetry senders dead code, then Sync and FxA, each behind the same leak gate.
- **Claims audit release check FAIL.** Next action: replace group-wide evidence seeds with cluster checks, label Linux-only text, and record the three bookkeeping verdicts listed in the claims backlog (maintainer only).
- **Six address-bar messages in conflict (intent I-1977b622eb against P-014).** Next action: the maintainer picks Gorilla or Mozilla wording.
- **`08.Look` strings Firefox 157 renamed.** Next action: port the remaining `.ftl` hunks by message id or record each as obsolete.
- **Gorilla.Satellite mode has no test on a real satellite link.** Next action: run the acceptance test on a real link (a text article readable in under 60 s at 5 KB/s and 700 ms; under 15 s on revisit).
- **The WhatsApp call settings (512 workers per site, WebM and Ogg on) are not a recorded decision.** Next action: the maintainer records it and the three lines leave the `05.PREFS` patch.
- **Search engine list.** Mozilla's 157 list without partner codes, while older text says Google-only. Next action: a maintainer decision to prune or reword.
- **Linux-only work without a Windows equivalent** (hardware-only video policy, bundled fonts, GfxInfo short-circuit, TCP keep-alive patch). Next action: decide per item; the keep-alive patch is not needed on Windows, where keep-alive is already driven by prefs.

## Impact If Removed

Without the egress lockdown, the browser asks Mozilla servers for things on its own again, as 155.0.1 did with eight hosts. Without the decision register, decisions drift silently between ports, as they did before. Without the snapshot and replay proof, the published patch set stops describing the shipped browser. Without the post-install proof, a green build can ship a dead address bar.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| every caller is cut at the source with a PHYSICAL LOCK | 📄 stated in input | Each cut returns before the code that would send, with a `GORILLA UNLEASHED - PHYSICAL LOCK` comment |
| the patch set replays to the built tree hash | 📄 stated in input | 0 patch failures, identical tree hash |
| 32 decisions on build 21 | 📄 stated in input | RELEASE-NOTES-157.0.md release status |
| Gorilla.Satellite mode measurements | 📄 stated in input | RELEASE-NOTES-157.0.md section 6 |
| AI control prefs were dropped by a type mismatch | 📄 stated in input | the hunk's boolean `false` was dropped by libpref (type mismatch) |
| the DNS patch had become a cap | 📄 stated in input | the same patch now *cuts* it to 16 |
| the HTTP/2 send buffer re-enabled an upload cap | 📄 stated in input | switches back on an upload cap that Mozilla has switched off |
| satellite mode writes to the default branch | 📄 stated in input | The level's values are written to the DEFAULT branch |
| bench limits | 📄 stated in input | The link is emulated by a user-space relay. |
| the NSIS installer once installed nothing | 📄 stated in input | the NSIS installer: it went silent into an empty dir once |
| the thermal proof is capped | 📄 stated in input | proof now capped at 60%, half the threads, stops at 80 C, reused per boot for 12 h |
| the claims audit release check fails | 📄 stated in input | Release check (the same, and every claim proven): **FAIL** |
| sideloaded add-ons are refused | 📄 stated in input | sideloaded add-ons (profile extensions folder, global dirs, registry) are never registered at startup |
| the impact of removing each part | 🤖 model inference | *(none — model judgment)* |
| the list of attack surface that remains by design | 🤖 model inference | *(none — model judgment)* |
