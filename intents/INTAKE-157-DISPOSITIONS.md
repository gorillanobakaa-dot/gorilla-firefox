# S1 intake 155.0.1 -> 157.0: proposed dispositions (22 briefs)

Written 2026-10-03 by the batch agent (one writer), under D-157-00 (never calls home) and D-157-30 (faster, lighter or
closed wins). The source is `fieldkit build-harness migrate intake firefox-157.0-truth` (pristine fb95137a04 ->
fdd757a2e0): 63 items in 22 clusters had no disposition. Each item below was read in the 157 tree (and the installed
build where stated).

**Status: PROPOSED, NOT RECORDED.** The drift guard refused `migrate work S1.INTAKE-...` because the migration is at
S6 (parked as P-004). The source cuts are staged as an apply-ready patch:
`Scripts/Fieldkit/_private/BATCH-20261003/patches/item1-intake-cuts.patch` (`git apply --check` passes on the tree).
Pref lines are in `Scripts/Fieldkit/_private/PREFS-BATCH-20261003.js`. A brief is closed only by
`build-harness decide`, which is the maintainer's call. This file does not close any brief.

Legend: **CUT** = cut at the source (staged), **PREF** = locked pref proposed (PREFS-BATCH), **NOT-NET** = not
network-capable or not built on Windows, so no cut is needed, **DORMANT** = already cut or excised; no further action.

| Brief | Item(s) | What it is | Disposition | Why |
|---|---|---|---|---|
| B-INTAKE-AI-ML-all | about:smartformfillreview | AI-window form-fill review page | **CUT** | Its target `chrome://browser/content/aiwindow/...` is not packaged (aiwindow is out of DIRS), so the registration is a dangling door. It is removed from AboutRedirector.cpp and components.conf, together with the same-family about:aichatcontent, about:aitab and about:smartwindowtasks. |
| B-INTAKE-AI-ML-browser-ai | browser.ai.control.speechRecognition | per-feature AI switch (string pref) | **PREF** `"blocked"`, locked | **Bug found:** Gorilla's all.js "AGGRESSIVE PURGE" sets the string prefs `browser.ai.control.*` to boolean `false`. libpref drops a redefinition of a different type, so the installed build (omni.ja greprefs.js, read today) still ships `"available"`/`"default"`. PREFS-BATCH sets all eight to `"blocked"`, locked. |
| B-INTAKE-AI-ML-browser-components-aiwindow | 18 modules (AITab, SmartFormFill*, Conversation*, MonitorAttention, SQLiteStoreBase ...) | AI window code | **DORMANT** | `browser/components/moz.build` excises "aiwindow". The installed browser/omni.ja holds no aiwindow module, only .ftl strings and icons. Its actors are excised in DesktopActorRegistry. AITab's only `fetch(` reads a packaged schema; json-schema.org and mozilla.org are a `$schema` id and licence text. |
| B-INTAKE-AI-ML-browser-ml | browser.ml.hwinference.max_restarts, browser.ml.linkPreview.smokeTest.lastBuildID, browser.ml.modelHub.testing | ML counters and test flags | **DORMANT** | The ML engine actors, llama backend and MLModelHubService are excised (toolkit/components/ml/moz.build). `browser.ml.modelHubRootUrl` is `""`, locked. No URL value. |
| B-INTAKE-AI-ML-browser-smartwindow | 8 prefs (agent.monitorAnnouncement, agent.toolbar.enabled, 4 logLevels, aitab.enabled, aitab.viewerURL) | AI window UI state and logging | **DORMANT** + **PREF** | aiwindow is excised. viewerURL is `""`. PREFS-BATCH locks `browser.smartwindow.aitab.enabled` false, and `browser.smartwindow.agent.enabled` (ships **true**; found alongside) false. |
| B-INTAKE-AI-ML-toolkit-components-ml | MLModelHubService.sys.mjs, ipc/HWInference{Child,Parent,Types} | model hub XPCOM wrapper; HW inference IPC | **DORMANT** | MLModelHubService is excised (moz.build comment, components.conf). The HWInference IPC stays only because ipc/glue and dom/ipc depend on it at build time. It has no network API, and only the excised ML engine starts it. |
| B-INTAKE-about-all | about:aitab | AI tab page | **CUT** | Same as above: dangling registration removed. The `browser.smartwindow.aitab.enabled` gate in NewChannel goes with it. |
| B-INTAKE-about-all | about:sync-log | local viewer of Sync log files | **NOT-NET** | It reads local files only. Sync is off (FxA locked off). No cut is needed, but it could be removed later for tidiness. |
| B-INTAKE-host-apache-org | www.apache.org | licence URL in a comment (PdfEmbedFallbackStreamConverter) | **NOT-NET** | A comment, never fetched. |
| B-INTAKE-host-json-schema-org | json-schema.org | `$schema` dialect id in AITab | **NOT-NET** | An identifier string, never fetched. The module is not packaged anyway. |
| B-INTAKE-host-mozilla-org | bugzilla.mozilla.org | bug link in a StaticPrefList comment | **NOT-NET** | A comment. |
| B-INTAKE-host-mozilla-org | mozilla.org | MPL licence headers (AITab and others) | **NOT-NET** | Licence text. |
| B-INTAKE-module-browser-modules-ASWebAuthSessionService-sys-mjs | ASWebAuthSessionService.sys.mjs | macOS ASWebAuthenticationSession sign-in broker | **NOT-NET** (on Windows) | It is built only for `cocoa` and NIGHTLY_BUILD (browser/modules/moz.build:114), so it is not in a Windows build. |
| B-INTAKE-module-toolkit-components-pdfjs | PdfEmbedFallbackStreamConverter.sys.mjs | pdf.js fallback for PDFs in `<embed>`/`<object>` | **NOT-NET** (user-initiated) | It loads the PDF the visited page embeds: a request the user's page made, not a call home. Cutting it would break embedded PDFs. |
| B-INTAKE-pref-app-backgroundNotifications | receivePushMessages.perMessageTimeoutMs / totalTimeoutMs | timeouts of the new `--receive-push-messages` handler (Windows background notifications start a window-less Firefox to drain push) | **CUT** | Push is already cut at the source (PushService PHYSICAL LOCK). The new toolkit/components/push/PushCommandLineHandler.sys.mjs now also returns at once, so nothing wakes the push service. |
| B-INTAKE-pref-browser-ipProtection | hasSeenFeature, l10nGateVersion | UI state of IP Protection (Mozilla's VPN proxy) | **PREF** | The feature needs FxA and Mozilla servers. PREFS-BATCH locks `browser.ipProtection.enabled` false (it ships false, unlocked). |
| B-INTAKE-pref-browser-netError | searchCTA.connectivityFreshnessMs / RecheckTimeoutMs | "search instead" button on a DNS error page; re-checks connectivity first | **NOT-NET** (closed) | The re-check goes through the captive-portal service. That is off and locked (D-157-25), and NetErrorParent returns early when it is off. The feature itself is off outside Nightly (firefox.js:1451). Any search it offers starts only on the user's click. |
| B-INTAKE-pref-browser-promo | browser.promo.relay.enabled (ships **true**) | Firefox Relay promo in login forms | **PREF** false, locked | A Mozilla service promo that needs FxA. No promos. |
| B-INTAKE-pref-browser-urlbar | newtab.featureGate, searchModeSwitcher.skipTabStop | address-bar UI and keyboard focus | **NOT-NET** | Local UI. featureGate is false outside Nightly. |
| B-INTAKE-pref-identity-fxaccounts | identity.fxaccounts.telemetry.clientInfoPing.enabled (ships **true**) | FxA telemetry ping | **PREF** false, locked | FxA is off and locked. This makes the dormant sender's switch say so too (D-157-21 pattern). |
| B-INTAKE-pref-javascript-options | javascript.options.experimental.export_star_default | JS language feature flag | **NOT-NET** | Language semantics only. |
| B-INTAKE-pref-network-android-doh | network.android_doh.rollout_request_timeout_ms | Android DoH rollout timeout | **NOT-NET** (Android) | Not used on Windows. TRR mode 5 is locked (D-157-18). |
| B-INTAKE-pref-remote-experimental | dynamicstart.{prompt,banner,connectionbanner}.enabled | prompt and banners of the remote agent's (WebDriver BiDi) start-on-demand | **MAINTAINER** (see below) | It opens a local control port, never a call home. Locking `remote.experimental.dynamicstart.enabled` false closes a door, but may cost developers or the harness. |
| B-INTAKE-pref-widget-use-xdg-desktop-portal | native-messaging-proxy | Linux Flatpak portal | **NOT-NET** (Linux) | Not used on Windows. |

## For the maintainer (not decided here)

1. **remote.experimental.dynamicstart.enabled locked false**: this closes a local remote-control door (D-157-30
   "closed wins"), but developers who start WebDriver BiDi from the browser lose it. The pref line is in PREFS-BATCH
   with a CHECK FIRST note. Confirm that the harness's headless proofs do not use dynamic start before applying it.
2. **about:sync-log**: keep it (local, harmless), or remove it for tidiness. No privacy effect either way.

## Proposed register checks (for the decision/claims owners, not written here)

- `tree_lacks: {path: browser/components/about/components.conf, text: "'aitab'"}` (and the same for
  `'smartformfillreview'`)
- `tree_contains: {path: toolkit/components/push/PushCommandLineHandler.sys.mjs, text: "GORILLA UNLEASHED - PHYSICAL LOCK: no background push"}`
- `pref: {name: browser.ai.control.default, value: "blocked", locked: true}`, plus one per `browser.ai.control.*` line
