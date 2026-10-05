**Gorilla Unleashed 157.0 for Windows: Firefox 157.0 that only talks to the sites you open.**

Windows 10 and 11, 64-bit. Based on Firefox 157.0 (tag `FIREFOX_157_0_RELEASE`, commit `fdd757a2e09c9471cddf383e64e631e4ce178499`).

BuildID **`20261004224302`** (build 27 of the final port). Check it in `about:support` after you install.

> **Release status, stated before anything else.** Every line below is a result on this exact build, except the leak test, which says so.
>
> - Leak gate, release mode: The four-hour release leak test last ran in full on build 26 (run `20261004-165832`) and **failed**. One finding was real: through a proxy, a page on `127.0.0.1` could reach `10.0.0.1` and `192.168.0.1`. Build 27 fixes it in `nsHttpChannel.cpp` (only the same address space counts). The other failures were faults of the test itself (processes seen dying counted as lingering, DNS aliases, another program's DNS lookup, run-to-run comparison), since corrected, and items waiting for the maintainer's approval, since approved at the maintainer's terminal. **The full leak test is running on this exact build** (started 5 October 2026, 08:33 UK time). It takes about four hours; because this is the first run of the 157 line, the maintainer then records it as the reference, and a second full run must pass against it. Both results will be added to this page.
> - Post-install proof on build 27: settings, removed parts, start-up, egress (8 hosts in 75 seconds on a real page, **0 Mozilla or Firefox hosts**), ad blocking (a news front page through 20 hosts, no ad or tracker host reached), WebRTC/WebGL/battery leaks, decisions: **all ok**. Visual: static 331 pass, 0 fail; run-time 122 pass, 0 fail. Menus and Settings readable (lowest contrast 16.75:1), no script errors. Address bar (keyboard test): **OK**, typed address, bare host name and search all navigate.
> - Installer: installed silently into an empty folder, started, the files are identical to the zip's, and uninstalled cleanly. The program icon carries all 10 sizes from 16 to 256 pixels.
> - Decision register, strict: **OK**: 34 entries, 31 enforced with checks, 3 recorded trade-offs, 0 pending, 0 violated.
> - Claims audit: **0 contradicted claims and 0 failing patches** (456 patches). It started this port at 1,199 contradicted; most were the audit reading its own report back, and the rest were fixed or explained. Strict check: still FAIL, because most of the 5,749 sentences in the older project logs have no automated check (unproven, not false). 58 registered sentences that were since reworded are retired and kept on record.
> - Replay proof (public patch set + pristine 157.0 = the compiled tree): **OK**: 456 patches, 0 failures; replayed tree and built tree both `109fd17fb5b9926e5e0c17115e9a69418b8173be`.

---

## What Gorilla 157 is

Gorilla Unleashed is Firefox with every call home cut out of the source code. It contacts the sites you open, the filter-list hosts of its built-in ad blocker, and, only when a page asks for protected video or a video call needs it, Google's or Cisco's video plug-in servers. Nothing else, on its own initiative: no Mozilla, Google, Microsoft, Cloudflare or certificate authority.

That rule is written down as decision **D-157-00, "THIS BROWSER NEVER CALLS HOME"**, and every other choice in this release is a decision with a reason, a cost and a check that runs against the built browser.

## What changed since 155.0.1

### 1. The calls home that 155.0.1 still made are cut at the source

On 2 October 2026 the browser's own network log showed that **155.0.1 asked eight Mozilla hosts for things on its own**: Remote Settings and its attachment and signature servers, the location service, push, the add-ons API, the system add-on updater and the connectivity probe. The earlier check had matched DNS names against shared CDN addresses and could not see it.

In 157 each of those callers returns before it sends, with a `GORILLA UNLEASHED - PHYSICAL LOCK` comment in the source, so no setting can turn it back on. The same treatment went to legacy telemetry and its `pingsender.exe`, the DAP telemetry sender, Normandy start-up, Merino suggestions, the new-tab feeds (stories, sponsored tiles, weather, stocks, wallpapers), the Safe Browsing list downloads, captive-portal detection, network geolocation, UITour, the MITM-detection ping on certificate errors, search partner codes, and `desktop-launcher.exe` (shipped since 155; it downloaded Mozilla's installer when Firefox was not found). It is no longer built.

Measured on the build of 2 October (BuildID `20261002132610`): over 75 seconds on a real page, the browser's own HTTP log listed 8 hosts and **0 Mozilla or Firefox hosts**. On a news front page it loaded through 20 hosts and reached **0 of 16 known ad and tracker domains**.

This build (27): the post-install egress row listed 8 hosts in 75 seconds on a real page and **0 Mozilla or Firefox hosts**.

Build 27 closed three more doors the review of the build 26 leak test found. None was seen sending anything; each could have been opened by changing one setting:
- five new-tab requests to Mozilla's Merino server (hourly forecast, sports, watch-live, picture of the day) now return before they send, like the others;
- a second Remote Settings client (written in Rust) fell back to Mozilla's production server when given no address; it now always gets an address that leads nowhere, and its switch is locked off;
- `Microsoft.WindowsAppRuntime.dll`, a Microsoft library with push-notification and telemetry code that nothing in the browser loads, is no longer shipped.

### 1a. Nothing can change the browser after it ships (new: decision D-157-31)

The maintainer's rule, in their words: anything that gives Firefox a remote configuration and experimentation control plane that can change parts of the browser after the binary has shipped is a no. Finding it out was not planned: on build 19 the new tab and the start page were **completely black**.

- **Why it was black.** Firefox 157 builds the new tab only after its experiment system (Nimbus) says it has nothing new for the page. Gorilla never starts Normandy, and in 157 that was the only thing that started Nimbus, so the answer never came. The page waited for ever.
- **What it was waiting for.** A feature called *train-hop*: Mozilla can replace the whole new-tab page with a package downloaded from `archive.mozilla.org`, and change its layout, ads, widgets and some default settings, after you have installed the browser.
- **What 157 does now.** The new tab no longer asks the experiment system anything. Train-hop is cut out at the source (no download, no install, no remote configuration, the download address blank and locked). Nothing else may start the experiment system either: the first-run page, launch-on-login and background tasks were also cut, and search addresses can no longer take extra parameters pushed through it.
- **A second hidden fault found on the way.** Firefox only uses the data built into it (search-engine icons, the list of tracking parameters stripped from links, password-field rules) when it believes it talks to Mozilla's real server. Gorilla's lock had pointed it at a dummy one, so all of that built-in data was silently ignored. Nothing leaked; features did less. It is used again; it is local files only.
- **So it cannot happen again**: a new automatic check fails any build whose new tab does not show the Gorilla logo and the search box, and the build harness now scans every new Firefox for code that waits for, or starts, the experiment system, and refuses to build until each place is handled.

### 1b. Websites cannot knock on your home network (decision D-157-16, fixed in builds 21, 22 and 27)

The release leak test on build 20 caught a page reaching for `192.168.0.1` and `10.0.0.1`: Firefox 157 checks local-network permission only *after* a connection opens, so for an address where nothing answers, the knock had already left the computer. Nothing could be read, but a site could time the answers to map a home network. In 157 the check runs **before** the connection, with Firefox's own permission rules, so a router page you open yourself still works and a website must ask first. Verified on build 21: no connection to either address. Build 22 closed the same door for connections made through a proxy. The leak test on build 26 then caught one case left: through a proxy, a page on the computer itself (`127.0.0.1`) could still reach `10.0.0.1` and `192.168.0.1`. Build 27 allows only the same kind of address (a router page loading its own files, a local page talking to the computer itself).

### 2. Every product choice is now a recorded decision with a check

The decision register holds 34 entries: 31 enforced and 3 recorded trade-offs, none pending. Each enforced entry is checked against the built browser (a locked setting, a file absent from the package, a marker in the source). The ones you will notice:

| Decision | What it means for you | What it costs you |
|---|---|---|
| D-157-01 No automatic updates | The browser never downloads or installs anything by itself. | You update by downloading the next release. |
| D-157-03 English only | No translation engine, no language packs. | The interface is English only; pages are not translated. |
| D-157-04 One theme | The Gorilla dark frame, nothing else. | No choice of look. Web pages keep their own dark mode. |
| D-157-05 No add-ons except uBlock Origin | uBlock Origin 1.74.0 is built in; every other install route is closed, including the temporary-add-on and sideloading routes. | No password-manager or other add-ons. uBlock Origin itself updates only with a new Gorilla build (its filter lists update themselves). |
| D-157-06 Fingerprinting | Light protection on and locked; the GPU model string is hidden; no motion sensors. | The strict Tor-style mode is off (you can switch it on). |
| D-157-07 Offline revocation | The revocation list of intermediate certificate authorities ships inside the build (1,880 records, June 2026). No OCSP calls. | Revocation of ordinary site certificates is not checked; the list is as fresh as the build. |
| D-157-12 Video compromise | Widevine (protected films) and OpenH264 (calls) are downloaded only when a page asks, straight from Google and Cisco, checked against built-in checksums. | Those two downloads are the browser's only own-initiative contact, and only on demand. |
| D-157-13 No location | Sites cannot ask where you are. | "Find me on the map" needs an address typed in. |
| D-157-14 No speculative connections or pings | Nothing is fetched for links you only hover over. | A first click may feel a few milliseconds slower. |
| D-157-16 Local network protection | A public page cannot scan your router or printers without asking. | A router admin page asks first. |
| D-157-17 No Windows SSO, no Windows certificate store | HTTPS cannot be silently intercepted by certificates added to Windows. | Antivirus "HTTPS scanning" and company inspection proxies cause certificate errors. |
| D-157-18 No DNS-over-HTTPS | Names go to your system's own resolver; no provider is chosen for you. | Your internet provider sees which names are looked up. |
| D-157-19 No suggestions, no download verdicts | Nothing you type leaves the computer before Enter. | No search suggestions while typing. |
| D-157-20 No backup feature, no profile manager | No OneDrive default folder, no Mozilla CDN images. | Copy your profile folder by hand to back it up. |
| D-157-25 Safe Browsing and captive-portal detection off | No Google or Mozilla list servers. | No built-in phishing and malware warnings (uBlock Origin still blocks known bad hosts); hotel and airport Wi-Fi login pages must be opened by hand. |
| D-157-26 policies.json ships | A second, runtime lock: Firefox's own enterprise policies "disable studies" and "disable telemetry". | `about:telemetry` says it is blocked by your organisation. (The file was missing from 155.0.1; an earlier 157 build shipped settings Firefox refuses in that file, so the lock did not exist until this build.) |
| D-157-31 No remote control plane | No experiment, rollout, settings push or downloaded replacement page can change the browser after you install it. | New-tab fixes arrive only with a new Gorilla build. |
| D-157-28 Cookies kept on shutdown (trade-off) | You stay logged in after a restart. | Less private than clearing on shutdown; clear data yourself when you want to. |
| D-157-08 Captchas (trade-off) | No protection is removed to avoid them. | Some sites, Google among them, show more captchas. |

The full register, with each decision's reason and its checks, is in the developer documentation in this folder.

### 3. AI and machine-learning parts removed

The AI Window, the chatbot sidebar and link previews (`aiwindow`, `genai`) are not built. The on-device ML engine's JavaScript is not packaged; only the inter-process glue Firefox 157 needs to start its utility process remains. Firefox Translations is removed at the source (D-157-03).

A real bug was found on the way: Gorilla's settings set Mozilla's per-feature AI switches (`browser.ai.control.*`) to `false`, but those are text settings, and Firefox silently drops a setting of the wrong type. They shipped switched on. In 157 all eight are set to `"blocked"` and locked.

### 4. Add-on installs are refused out loud

Until now a refused install failed silently: the button went pale and nothing happened. 157 shows a message that Gorilla does not install add-ons or themes and that uBlock Origin is built in. The message is in this build (patch `22.EGRESS.LOCKDOWN.157/047`); no automated test clicks an install button yet, so it is checked by hand only.

### 5. Network fixes, measured before and after

A study of every network setting found that none of the network tweaks inherited from the Linux build had ever been measured, and that three of them work against speed on Firefox 157. Fixed in this build, under the standing rule that faster and lighter wins (D-157-30):

- **DNS resolver pool**: the old patch was written to raise Firefox 154's pool to 16 threads; Firefox 157's own limit is 64, so the same patch had become a cap. Upstream's limit is restored.
- **HTTP/2 upload cap**: `network.http.http2.send-buffer-size` was 131072, switching back on an upload cap Mozilla had switched off. It is back to 0.
- **Response timeout**: `network.http.response.timeout` was 15 seconds, a trap for slow satellite links if keep-alive is ever off. It is back to 300.

The bench runs against local servers only (127.0.0.1), with emulated links, three repetitions, medians. "Before" is the build of 3 October morning (BuildID `20261003112601`); "after" is build 18 (BuildID `20261003155534`). This table was not re-run on builds 19 to 27, which changed logos, the new tab, the experiment cut, the local-network check and Gorilla.Satellite mode (its own measurements, with the mode Off and on, are in section 6):

| Measurement | Link | Before | After |
|---|---|---|---|
| Article set, first visit, load time | Broadband (50/10 Mbit/s, 20 ms) | 0.75 s | **0.39 s** |
| Same | Starlink-like (100/15 Mbit/s, 40 ms, 0.5% loss) | 0.83 s | **0.37 s** |
| Same | GEO satellite (10 Mbit/s, 600 ms, 1% loss) | 3.92 s | **3.21 s** |
| Same | Austere (5 KB/s, 700 ms) | 95.6 s | 95.6 s (the link is full: 465 KB at 5 KB/s takes 93 s) |
| Same page after a browser restart | Austere | 95.7 s | 95.6 s (everything downloaded again: with Gorilla.Satellite mode Off there is no disk cache; see section 6) |
| HTTP/2 download | Starlink-like | 84.1 Mbit/s (84% of the link) | **94.0 Mbit/s (94%)** |
| HTTP/2 upload | Broadband | 9.67 Mbit/s (97% of the link) | 9.87 Mbit/s (99%) |
| HTTP/2 upload | GEO | 7.92 Mbit/s (79% of the link) | 7.97 Mbit/s (80%) |
| HTTP/2 download | GEO | 7.90 Mbit/s (79% of the link) | 7.94 Mbit/s (79%) |
| Browser memory, peak private bytes, fixed workload | Broadband | 717 MB | 729 MB (within the run-to-run spread) |
| Same | Starlink-like | 906 MB | **770 MB** |
| Same | Austere | 553 MB | 586 MB (up by 33 MB) |

What the bench cannot show: the relay ends the browser's TCP connection on the same machine, so the HTTP/2 upload cap (the main reason for the fix) is not reproduced by it; DNS is not exercised; HTTP/3 is not used through the relay. Real-link numbers for these fixes are **not measured**.

### 6. Gorilla.Satellite mode: a switch on the toolbar and in Settings (decisions D-157-32, D-157-33)

**Gorilla.Satellite mode** is for slow, far-away or expensive internet: satellite, Starlink, rural mobile, down to 5 KB per second. You switch it in either of two places:
- the **Gorilla.Satellite mode** button right of the address bar, which says which level is on;
- Settings, General, under Network.

Hover over any choice for the full explanation. Nothing in it sends anything anywhere: it makes the browser download less, keep what it already has, and wait longer before giving up.

| Level | What it does |
|---|---|
| **Off** (default) | The browser as shipped. |
| **Satellite** (fast but far: Starlink, satellite broadband) | Sites are asked for their mobile version. Videos never start by themselves and are not downloaded in advance. Longer connection, TLS and response timeouts. Addresses kept 10 minutes. Up to 256 MB of pages kept on disk **across restarts** (including HTTPS pages, which Gorilla otherwise never writes to disk). |
| **Very slow link** (down to 5 KB/s) | Everything in Satellite, plus: no JavaScript, no pictures, no web fonts, `Save-Data: on`, 6 connections per site. A page you already have opens from the disk without asking the site; Reload fetches a fresh copy. |

The toolbar menu also has these switches:
- **This site: show the normal (desktop) version**, for a site whose mobile version is poor;
- **This site: allow JavaScript**, for webmail, maps, some shops and logins;
- a tick-box for the mobile versions, and one for no-JavaScript.

All are remembered per site. Off restores every shipped value.

**Measured on real sites, over the maintainer's link, with an empty cache each time.** The times at 5 KB/s are worked out from the bytes, not timed on a 5 KB/s link.

| Site | As shipped | Very slow link | At 5 KB/s |
|---|---|---|---|
| BBC News | 1,636 KB | 101 KB | about 21 s |
| The Guardian | 1,121 KB | 148 KB | about 30 s |
| DuckDuckGo search | 2,504 KB | 207 KB | about 42 s |
| Reuters | 2,230 KB | 315 KB | about 65 s |
| Wikipedia (Starlink article) | 744 KB | 322 KB | about 66 s |
| CNN | 14,057 KB | 608 KB | about 2 minutes |

The text of all six pages stays readable without JavaScript; pictures of each page were looked at.

Most of the saving comes from leaving JavaScript out. Asking for the mobile version barely changes the size on these sites, because most of them now send one page to phones and computers alike.

**Measured on the local test bench** (emulated links, 3 repetitions, medians):

| Link | Off | Satellite or Very slow link |
|---|---|---|
| 5 KB/s, 700 ms: first visit | 95.6 s | **41.0 s** (Very slow link) |
| 5 KB/s: after a restart | 95.6 s | **23.7 s** (Very slow link; everything but the page itself comes from the disk) |
| GEO satellite (600 ms, 1% loss): after a restart | 3.78 s | **2.51 s** (Satellite; 1 request instead of 16) |
| Starlink-like: first visit | 0.45 to 0.67 s | 0.43 to 0.56 s (Satellite; no slowdown) |
| The same page again (a page that says must-revalidate, local test, build 25) | asked the site again | **opened from the disk, no request** (Very slow link; Reload still fetches a fresh copy) |

**Costs, recorded in D-157-33.**
- A phone identity on a large screen is a rare mix a website could notice.
- `Save-Data` is one more small difference from other users.
- Pages you visited stay on disk after you close the browser (history, form data and downloads are still wiped).
- A cached page can be out of date until you press Reload.
- A site switched back to its desktop version still sees the Android platform name from JavaScript.

A restart keeps the pages on disk at every speed: the cache used to size itself at start-up before the level was applied, with Gorilla's shipped limit of 0, and so emptied itself (found with Firefox's cache log, fixed by shipping the limit at 256 MiB; the disk cache itself stays off while the mode is Off).

### 7. Also in this release

- Windows content sandbox: Mozilla's own Windows level (its strictest) instead of the Linux number, which had weakened it (D-157-02).
- Every logo and piece of branding rebuilt from the gorilla master image: Windows tiles, installer images, wizard bitmaps and the PDF document icon. Mozilla's leftover artwork and macOS-only files are removed. No "Nightly" wordmark or Nightly update links left (D-157-24).
- Layout fixes on `about:license`, `about:checkerboard` and `about:certificate`; the new-tab search button uses a sharp vector icon. The visual check went from 20 static and 47 run-time failures to 0. The checker itself was made more exact on the way: hidden radio buttons, clipping, and pages blocked by policy (such as `about:telemetry`) are now checked as blocked.
- The toolbar menus and Gorilla's Settings are checked for readability on every build: each item must have a contrast of at least 4.5:1, no script errors, and no empty menus. The check was added after the first Gorilla.Satellite mode menu (build 23) shipped cyan text on light grey (1.25:1) with a handler that failed; build 24 fixed both. The same check found an older address-bar pop-up height fix that had silently stopped working, and a Settings error on every opening (a removed AI pane was still imported). Both are fixed.
- The address bar says "Search with Gorilla or enter address you Apple Moron" also when a default search engine is known (real profiles had shown "Search with Google or enter address").
- `about:credits` and `about:rights` no longer open mozilla.org: they show the local licence page (D-157-00).
- Nothing is written outside the profile for updates (D-157-01), and the build tool's own build telemetry never runs.
- Every build configuration carries every disable: no default-browser agent, no speech API, no Wi-Fi scanning (D-157-22).
- Searches carry no Mozilla partner code (D-157-23).

## What it cannot do: known limits

Each of these is either a recorded cost of a decision or an open item, stated so you do not discover it by accident:

- **No automatic updates.** You update by hand. Old builds stay old.
- **English only. One theme. No add-ons other than uBlock Origin.**
- **No sync, no search suggestions, no translations, no location, no built-in profile backup.**
- **No Safe Browsing warnings.** uBlock Origin blocks known bad hosts, but the browser does not warn about phishing or malware pages on its own.
- **Ordinary site certificates are not checked for revocation.** Revoked intermediate authorities are refused from the bundled list.
- **Certificate errors behind antivirus HTTPS scanning or company proxies.** That is the protection working.
- **More captchas** on some sites.
- **Cookies and logins are kept** when you close the browser.
- **The Tor-style fingerprinting mode is off by default.** Light protection is on; a determined site can still tell browsers apart.
- **The built-in password manager stays on.** "No password manager" in older documents meant no password-manager add-ons.
- **Normandy, Nimbus, Sync, Firefox Accounts and the telemetry code are still compiled in.** They are switched off and their network callers are cut, but the code ships. Removing it is the next phase.
- **Some dialogs may still say Firefox or Mozilla.** Firefox 157 renamed messages; most Gorilla wording was carried over, not all. Six address-bar messages are waiting for the maintainer's choice between Gorilla and Mozilla wording.
- **Gorilla.Satellite mode** has been measured on real sites over an ordinary link and on an emulated satellite bench, not on a real satellite link.
- **The installer and the zip are not signed.** Windows SmartScreen will warn. See "Install" below.
- **The four-hour leak test on build 27 is running** (started 5 October 2026, 08:33 UK time); it ran in full on build 26 (see the status at the top).
- **The video plug-ins** (Widevine, OpenH264) come from Google and Cisco when a page needs them. That is the one recorded network compromise.
- **Linux:** this release is Windows only. The Linux build uses the 155 patch set.

## Install

There are two downloads. They hold the same browser, file for file.

**The installer: `GorillaUnleashed-157.0-win64-setup.exe`**, 96,333,980 bytes (about 92 MB). Download it, check its fingerprint (below), double-click it and follow the steps. Windows may say "Windows protected your PC": click **More info**, then **Run anyway**. Edge and Chrome may offer to delete the download: choose **Keep**.

**The zip, no installation: `Gorilla-Unleashed-157.0-win64.zip`**, 139,215,860 bytes (about 133 MB). Steps for the zip:

1. Download the zip from the Assets list of this release. Ignore "Source code (zip)" and "Source code (tar.gz)": those are the recipe, not the browser.
2. Check the fingerprint (see below) before you open it.
3. Right-click the zip, choose **Extract All**, and pick a folder you will keep, for example a folder called `Gorilla Unleashed` in your Documents.
4. Open that folder and double-click `firefox.exe`. To make a shortcut, right-click `firefox.exe` and choose **Send to**, then **Desktop (create shortcut)** (on Windows 11, choose **Show more options** first).
5. Windows may say "Windows protected your PC". Click **More info**, then **Run anyway**. This happens because the file is not signed with a paid certificate, not because anything is wrong with it. The fingerprint check is the stronger proof.
6. Open `about:support` and check that the BuildID matches the one at the top of this page.

If the Gorilla icon on your desktop looks blurry after you replace an older version, double-click **`Fix-blurry-icons.cmd`** from the Assets list: it asks Windows to draw its icons again and changes nothing else.

To update later: close the browser, run the new installer, or extract the new zip over a fresh folder and start the new `firefox.exe`. Your profile (bookmarks, logins, history) lives in your Windows user folder, not in the program folder, so it carries over.

### Check what you downloaded

In PowerShell, in your Downloads folder:

```
Get-FileHash <the file name> -Algorithm SHA256
```

The answer must be exactly this, for the installer:

```
02A7A403C314ACDAF55D7C70449CE06C520D45DC30A845D6D6F1C67B0670DBA5
```

and this, for the zip:

```
1E9CB307A2CC50194C006552FA534F19641D8665B53D0345E97682B4235A474A
```

## How to verify it yourself

You do not have to take this page's word for any of it:

1. **Watch the browser's own network log.** Start it with an empty profile and the HTTP log on (`MOZ_LOG=nsHttp:3`, `MOZ_LOG_FILE` set to a file), open a page, wait a minute, close it, and search the log for `mozilla`. The full recipe is in `docs/PRIVACY-AND-HARDENING.md` of the source repository.
2. **List what ships.** `omni.ja` and `browser/omni.ja` in the program folder are zip files. Open a copy with any zip tool: there is no `genai`, no `aiwindow`, no translations folder, and the bundled uBlock Origin is in `chrome/browser/gorilla-addons/ublock-origin/`.
3. **Read the audit.** `AUDIT-157.md` in the source repository checks every public claim and every patch against the built tree. It is generated by the build harness, and a check that could not run counts as unproven, never as proven. The copy in this release was generated for build 27.
4. **Replay the patch set.** `patches/BASELINE.txt` gives the method: pristine Firefox 157.0 plus the patch groups in order, with `--fuzz=0`, must give the same git tree hash as the source that was compiled. The build harness now does it in one command, `fieldkit build-harness replay <task>`. For build 27: **OK**: 456 patches, 0 failures; replayed tree and built tree both `109fd17fb5b9926e5e0c17115e9a69418b8173be`.
5. **The leak gate.** The release gate runs the installed browser through scenes (idle start-up, new tab, home, a real page, Settings, the add-ons page, canary pages in normal and private windows, WebRTC, workers, certificate errors, a file download, local-network probes, protected video and H.264 calls), with several witnesses at once: the browser's HTTP and DNS logs, a decrypting proxy, the socket table, the process tree, the file system and, in an administrator shell, a packet capture. It fails closed. The four-hour release leak test last ran in full on build 26 (run `20261004-165832`) and **failed**. One finding was real: through a proxy, a page on `127.0.0.1` could reach `10.0.0.1` and `192.168.0.1`. Build 27 fixes it in `nsHttpChannel.cpp` (only the same address space counts). The other failures were faults of the test itself (processes seen dying counted as lingering, DNS aliases, another program's DNS lookup, run-to-run comparison), since corrected, and items waiting for the maintainer's approval, since approved at the maintainer's terminal. **The full leak test is running on this exact build** (started 5 October 2026, 08:33 UK time). It takes about four hours; because this is the first run of the 157 line, the maintainer then records it as the reference, and a second full run must pass against it. Both results will be added to this page.

## Why this took five days, in short

Moving Gorilla from Firefox 155.0.1 to 157 sounds like re-applying a stack of patches. In practice the patch set published for 155 was not exactly what the 155 browser had been built from, so the port first had to capture the truth from the built browser. Firefox 157 had moved code the patches pointed at and had wired new uses of components Gorilla removes, so builds stopped on missing headers and refused build files. A build that compiled cleanly shipped a browser with a dead address bar. The laptop reset twice from heat, once because of a temperature sensor that had stopped moving and once because of the harness's own sensor test. An installer reported success and installed nothing. A leak-test run died and left a packet capture recording for seven hours. Settings shadowed each other, so a language switcher came back and the AI switches shipped on. An audit of the public documents found claims the build did not keep.

Each of these became a permanent check in the build harness, so it cannot cost time twice. By build 21 the task journal recorded 36 build runs for this port, 18 of which produced a verified package, and 389 recorded hand-port steps. The release took 27 builds of the build harness's own counter; the maintainer raised the limit from 20 to 27. Builds 19 to 21 came from the release leak test itself: a black new tab traced to the experiment system (D-157-31), and a local-network check that ran one step too late (D-157-16). Builds 22 to 26 closed the proxy route to the local network, gave Gorilla.Satellite mode its button and Settings switch, made its disk cache actually keep pages, and fixed an unreadable menu. Build 27 fixed what the release leak test found on build 26. The full account, with every number and how it was counted, is in **STORY-157.md** in this folder.

---

*Not affiliated with Mozilla. "Firefox" is a trademark of the Mozilla Foundation; this is an unofficial modified build. Free and open source.*
