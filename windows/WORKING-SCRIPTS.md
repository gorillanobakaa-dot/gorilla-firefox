# Tools in this folder

These scripts were written while porting Gorilla Firefox to Windows. Each one
exists because something went wrong that no existing check caught, and each
carries a docstring explaining that bug. `python <tool> --help` works on all of
them.

They were written for the project's own Windows build kit, which is not
published. Tools that read the installed browser or a running one work on
their own; tools that inspect a source tree or build output expect that kit's
folder layout (`src/`, `state/`, `harness/`), so read `--help` first.

## Video decoding

| tool | what it does |
|---|---|
| `make_decode_profile.py` | detects the graphics chip and writes `defaults/pref/gorilla-decode.js` into the install, enabling exactly the codecs it can decode in hardware. `--verify` proves the file is read |
| `test_decode_detection.py` | 14 real adapter strings. Run it after changing any detection pattern |

## Privacy

| tool | what it does |
|---|---|
| `audit_privacy_claims.py` | reads the preferences out of the **installed package** and checks them against the privacy claims in the release notes |
| `verify_no_phone_home.py` | starts the browser on a throwaway profile, touches nothing, and records every host it contacts |
| `fix_prefs_last_wins.py` | finds preferences defined twice, where a later definition silently overrides the intended value |

## The browser actually working

| tool | what it does |
|---|---|
| `verify_address_bar.py` / `.ps1` | types into a real window and reads the window title, to prove the address bar navigates — not just that it renders |
| `fix_theme_dead_selectors.py` | finds theme rules whose selector matches no element, so the style silently never applies |
| `add_builtin_extension.py` | bundles a WebExtension inside the browser — see [`../docs/HOWTO-BUNDLE-AN-EXTENSION.md`](../docs/HOWTO-BUNDLE-AN-EXTENSION.md) |
| `verify_builtin_extension.py` | checks a bundled extension is present **and visible** in about:addons, in a real window |

## Calls

See [WHATSAPP-CALLS-ON-WINDOWS.md](WHATSAPP-CALLS-ON-WINDOWS.md) for what was
wrong and how it was found.

| tool | what it does |
|---|---|
| `call_forensics.py` | read-only evidence in 10 seconds: installed build, profile, call settings, camera/mic access, IPv6, crashes |
| `webrtc_selftest.py` | hidden browser, throwaway profile, fake camera and mic, no network: ICE, DTLS with the 1.2 cap proven live, data channel, RTP |
| `capture_call_log.py` | starts the real browser with call logging, including the page's own console and `PageMessages`; reads the log when it closes |
| `analyze_call_log.py` | names the first failing layer, judging the call by whether data flowed |
| `test_analyze_call_log.py` | 14 fixtures from real log strings, one per verdict |
| `compare_browsers_media.py` | the same test page in Gorilla and Edge; `--gorilla-pref` tests a setting in a throwaway profile before a rebuild |
| `profile_prefs.py` | stops Firefox, backs up `prefs.js`, sets or removes settings, lists real overrides |

## Releasing

| tool | what it does |
|---|---|
| `publish_gate.py` | refuses a release unless the recorded tests passed on that exact build, and refuses release notes that claim what was not tested |
| `verify_published_release.py` | compares GitHub's installer digest with the local file and a fresh download, then unpacks the installer and compares it byte-for-byte with the installed browser |
| `watch_thermals.py` | samples CPU temperature during a build and can pause it at a limit |

## Lessons they encode

Each of these produced a confident wrong answer once:

- **Firefox pref files take the LAST definition.** Reading the first match
  inverts the answer for every preference that is overridden further down.
- **Firefox ships two `omni.ja` archives.** `browser/omni.ja` holds chrome
  content and themes; the core one holds `moz-src/`, including the address bar
  providers. Search both.
- **`-headless -screenshot` does not run first-window startup code**, so
  anything registered there looks absent. Verify with a real window.
- **`^(...|127\.|::1)$` cannot match `127.0.0.1`.** An anchored localhost filter
  made the browser's own local sockets look like unknown external connections.
- **A preference in a file is evidence about a file.** Only a call proves a
  call works; only a download proves the published file is the tested one.
