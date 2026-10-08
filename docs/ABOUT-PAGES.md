# 🦍 Every `about:` page in Gorilla 157, opened and checked

**Measured on 8 October 2026 on the Gorilla 157.0 (build 28) candidate for Windows. Every page was opened in a
fresh, throwaway copy of the browser with its network cut off, so that any attempt to reach the internet was
recorded and none could get out.**

This page is written twice: once in plain language, once with the details. Read either; they cover the same
ground.

---

## In plain words

Type `about:about` in the address bar and Gorilla lists its own built-in pages: settings, memory reports, network
internals, licences, error pages. Most people never open them. The people who check a privacy browser before
trusting it open them first, because they show what the browser really does underneath the marketing.

So we opened every one of them, the way a careful reviewer would, and wrote down what each page shows, what it
draws, what goes wrong on it, and whether it tries to talk to anyone. This is what we found and what we did.

**What we fixed:**

- **The Studies page was blank.** It is meant to say that Gorilla runs no studies (no experiments on its users).
  It was waiting for an experiment system that Gorilla never starts, and so it waited for ever. It now says so at
  once.
- **A blocked page showed Mozilla's artwork.** The telemetry page is switched off by policy, and the page that
  says so drew Mozilla's illustration instead of the Gorilla. It now shows the Gorilla.
- **Four Settings items had no text:** the "Keyboard shortcuts" heading and its link, the "Manage colors" button
  and the Containers "Delete" button. Their words had been lost when our changes were moved to Firefox 157. They
  are back, and our build tools now refuse any build where this happens again.
- **Nine pieces of text were defined twice,** which made pages log errors. The extra copies are gone.

**What we removed, and why:**

- **`about:glean`**: the test bench of Glean, Mozilla's data-collection library. Gorilla never starts Glean, so
  the page was a control panel for something that does not run. Its "submit" button did nothing: we pressed it and
  watched; no connection was attempted. Gone.
- **`about:logging` and `about:profiling`**: tools that record what the browser is doing and then open
  **profiler.firefox.com**, Mozilla's website, with that recording (your open tabs, the addresses you visited,
  timings), with an offer to upload it. Gorilla does not hand your data to a website, so both pages are gone, the
  "record" buttons on the process manager are gone, and the hand-over itself is refused inside the browser's code.
  A recording can only be opened in a viewer running on your own computer.
- **`about:windows-messages`**: a diagnostics page for Mozilla's engineers. To feed it, the browser kept copies
  of its own window events (moving, resizing, switching) the whole time. The page and that bookkeeping are gone.

**What it costs you:** no built-in profiler or logging page. If you are a developer who needs them, the browser's
logging still works through the standard `MOZ_LOG` setting, which writes to a file on your own computer.

**What it does not do:** none of the pages we kept tried to reach the internet. The only connections recorded
while we walked through all of them were uBlock Origin, the one built-in add-on, downloading its own blocking
lists, which is how it works.

**Still to do:** some pages still draw Mozilla's artwork (kittens, a fox, logos). These are listed at the end and
will be replaced.

**And one more thing you can see:** Help → About Gorilla Unleashed now says when your copy was built, for example
`157.0 (64-bit) built 26:10:08:10:37:25` (year, month, day, hour, minute, second). Two people comparing notes can
tell at a glance whether they run the same build.

---

## The details

### How it was measured

- The maintainer's build tools (Fieldkit, `build-harness about-pages`) copy the browser to a throwaway folder,
  start it with a new, empty profile, and set a dead proxy (`127.0.0.1:9`) before the first page opens.
- Every page the browser registers is opened, not only those `about:about` lists. Pages that crash the browser on
  purpose (`about:crash*`) are skipped.
- For each page the tools record:
  - where it ended up (a page blocked by policy lands on the error page);
  - the text it shows, including text inside web components;
  - every picture it draws and at what size;
  - its controls;
  - script errors, and promises rejected with nobody handling them, with where they were made;
  - text labels that name a translation string no file defines;
  - every network request opened while it was showing, and who opened it: the page, an add-on or the browser.
- A second mode does it the way a person does: a visible window opens `about:about` and clicks each link in turn.
- The same check now runs **before** every build (the planned changes applied to a copy of the installed
  browser), **after** every build (the browser that came out, before anyone installs it) and **after** every
  install. A build that leaves a page blank, a label empty or a request where none belongs does not pass.

### Results, page by page

Pages listed by `about:about`, as walked by clicking each link (40 links). "Requests" counts connections the page
itself attempted; there were none on any page. The process column says whether the page runs inside the browser's
privileged main process or in a sandboxed content process.

| Page | What it is | Process | Gorilla status |
|---|---|---|---|
| `about:about` | The list of built-in pages. | main | Kept. |
| `about:addons` | The add-ons manager. uBlock Origin is built in; installing anything else is blocked. | main | Kept. Draws Mozilla's kitten (`kit-addons.svg`): open, artwork sweep. |
| `about:buildconfig` | How this copy was compiled: compiler, target, options. | main | Kept: it is how you check what you run. |
| `about:cache` | Statistics of the network cache in memory and on disk. | main | Kept. |
| `about:certificate` | The certificate viewer: the certificate authorities your copy trusts. | content | Kept. |
| `about:checkerboard` | A recorder for scrolling glitches, for graphics debugging. Off unless switched on. | main | Kept. |
| `about:compat` | The site-specific fixes Firefox ships for broken websites, each with a link to its bug report. Local; nothing is fetched. | content | Kept. |
| `about:config` | Every preference, with a warning page first. | main | Kept. |
| `about:credits`, `about:license`, `about:rights` | Licences of the code in the browser (Mozilla Public License and others). | main | Kept. Draws Mozilla's licence banner (`about-license.svg`): open. |
| `about:debugging` | Remote debugging set-up. USB debugging is off. | main | Kept. Draws a 16 px Firefox logo: open. |
| `about:downloads` | The download list ("There are no Gorilla downloads." when empty). | main | Kept. |
| `about:firefoxview` | Recent browsing: open tabs, recently closed tabs, history. | main | Kept. Draws Mozilla's kitten (`kit-page-history.svg`): open. |
| `about:home`, `about:newtab`, `about:welcome` | The new tab page, with the Gorilla. `about:welcome` opens it too. | content | Kept. |
| `about:keyboard` | The keyboard shortcuts editor. | content | Kept. |
| `about:logins` | Saved passwords. | content | Kept. Draws Mozilla's fox (`cpm-fox-illustration.svg`): open. |
| `about:loginsimportreport` | The report shown after importing passwords. | content | Kept. |
| `about:memory` | Memory reports: measure, save, compare, free memory. | main | Kept: it is how our memory savings were measured. |
| `about:mozilla` | The "Book of Gorilla" passage (a Firefox tradition, in Gorilla's voice). | main | Kept. |
| `about:networking` | Live connections, DNS, WebSockets, a DNS lookup tool. | main | Kept. Its "Logging" entry pointed to the removed `about:logging` and is gone. |
| `about:pdf` | The built-in PDF tool. | content | Kept. Draws Mozilla's kitten (`kit-in-circle.svg`): open. |
| `about:policies` | The policies this copy enforces: studies off, telemetry off. | main | Kept. |
| `about:preferences` | Gorilla Settings. | main | Kept. Four empty items fixed. Draws Mozilla's "concerned kitten" (`kit-concerned.svg`): open. |
| `about:privatebrowsing` | The private-window page. | content | Kept. |
| `about:processes` | The process manager: memory and CPU per process. | main | Kept. Its per-process "record a profile" buttons are gone. |
| `about:profiles` | The classic profile manager. | main | Kept. |
| `about:protections` | The tracking-protection dashboard. | content | Kept. Draws Mozilla product logos: open. |
| `about:robots` | A Firefox joke page, in Gorilla's voice. | main | Kept. |
| `about:serviceworkers` | The background scripts websites install (offline caches, push messages), with a button to remove each. | main | Kept: it shows you what sites left behind. |
| `about:studies` | Studies (experiments on users): "We do not do studies… No studies have run, no studies will run." | content | Fixed: was blank. |
| `about:support` | Troubleshooting information. | main | Kept. |
| `about:sync-log` | Diagnostic logs written by Sync, on your computer. | main | Kept. |
| `about:telemetry` | Telemetry viewer. | main | Blocked by policy; the blocked page now shows the Gorilla instead of Mozilla's illustration. |
| `about:third-party` | Programs from other vendors that injected themselves into the browser (Windows). | main | Kept: useful against unwanted software. |
| `about:unloads` | How the browser unloads tabs when memory runs short. | main | Kept. |
| `about:url-classifier` | The lists used to classify addresses (tracking, cryptomining, fingerprinting, and so on). | main | Kept. |
| `about:webrtc` | Internals of calls and video chat. | main | Kept. Its "Enable logging" button opened the removed `about:logging` and is gone. |

**Removed:** `about:glean`, `about:logging`, `about:profiling`, `about:windows-messages` (this release);
`about:logo`, `about:translations` and `about:inference` (earlier). DevTools has no Performance panel either: its
recording ended by opening Mozilla's hosted profiler, which Gorilla now refuses.

**Pages `about:about` does not list** (error pages, crash pages, the new-profile wizard, developer previews) were
opened as well. Their only script errors come from opening them by address instead of through the event they
belong to (an error page with no error to show, an import report with no import). None attempted a connection.

### Where it is in the source

| Change | Where |
|---|---|
| Studies page answers at once | `toolkit/components/normandy/content/AboutPages.sys.mjs` |
| Gorilla on blocked and error pages | `toolkit/content/errors/net-error-illustrations.mjs` |
| Pages removed | `docshell/base/nsAboutRedirector.cpp`, `docshell/build/components.conf`, `browser/components/about/AboutRedirector.cpp`, `browser/components/about/components.conf` |
| Profile hand-off refused unless the viewer is on this computer | `devtools/client/performance-new/shared/browser.js` |
| No profiler buttons, no Performance panel | `modules/libpref/init/all.js`, `browser/app/profile/firefox.js` |
| No window-event bookkeeping | `widget/windows/nsWindowDbg.cpp` |
| No links to removed pages | `toolkit/content/aboutNetworking.html`, `toolkit/content/aboutwebrtc/aboutWebrtc.mjs` |
| Lost and doubled Settings strings | `browser/locales/en-US/browser/preferences/preferences.ftl` and five other `.ftl` files |
| Build stamp in Help → About | `browser/base/content/aboutDialog.js`, `browser/locales/en-US/browser/aboutDialog.ftl` |

The patches are in [`patches/21.PORT.FIXES.157`](../patches/21.PORT.FIXES.157) and
[`patches/22.EGRESS.LOCKDOWN.157`](../patches/22.EGRESS.LOCKDOWN.157).
