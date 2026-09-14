# WhatsApp Web calls on Windows — what was wrong

## Short version

Voice and video calls on web.whatsapp.com work from **v155.0.1-win64.4**
(BuildID `20260914135622`). That was verified with a real, logged WhatsApp call
on that exact build, with every setting at its default.

In every earlier Windows build, calls fail the same way: you hear ringing, the
other phone never rings and shows "Connecting…", and the call drops.

The release notes for v155.0.1-win64.3 said calls worked. That had not been
tested and was wrong; that page now carries a correction.

---

## What was changed

| setting | was | now | why | fixed in |
|---|---|---|---|---|
| `media.peerconnection.dtls.version.max` | 772 (DTLS 1.3) | **771** (DTLS 1.2) | Meta's call relays silently drop DTLS 1.3 traffic | .3 |
| `dom.workers.maxPerDomain` | 8 | **512** (Firefox's own default) | WhatsApp Web runs more than 8 background workers; the one its call engine needs was left waiting in a queue | .4 |
| `media.webm.enabled`, `media.ogg.enabled` | false | **true** | WebCodecs checks VP8 support against the WebM container and Opus against Ogg, so with both off it could decode neither | .4 |

The DTLS cap was necessary but not enough. The worker limit was the cause
that remained. The WebM/Ogg change is correct for WebCodecs, but was not shown
to be needed for calls on its own.

---

## How the worker limit was found

Every transport log was clean: relay connections up, DTLS 1.2 negotiated, data
channels open — and then almost nothing. The cause was only visible in the
**web page's own warnings**, which a WebRTC log does not include by default.
Adding the `console` and `PageMessages` log modules showed:

> A Worker could not be started immediately because other documents in the
> same origin are already using the maximum number of workers.

It appeared 16 ms before the call's first PeerConnection, and five more times
in the next 12 seconds. Raising only `dom.workers.maxPerDomain` to 512 removed
the warning, and the call carried 793 data-channel messages in 21 seconds,
against 11–12 in the failed calls.

Two things looked like the cause and were not:

- **Failed IPv6-only relay connections.** WhatsApp opens many connections at
  once. On a network with no IPv6, the ones offered only IPv6 relays always
  fail — in working calls too. Judge a call by whether its data flowed, not by
  whether every connection came up.
- **The network.** A Chromium-based browser on the same machine and network
  made the same call with video both ways, which ruled it out.

---

## Logging notes for Firefox 155

If you capture a call log yourself:

1. **`Wrote 28 bytes to SSL Layer` needs `mtransport:5`, not `:4`.** It is
   logged at `ML_DEBUG`, which `dom/media/webrtc/transport/logging.h` maps to
   `LogLevel::Verbose`. At `:4` the line is never written, so a check for "no
   long runs of 28-byte writes" passes on the very fault it is meant to catch.
2. **The `Setting DTLS1.3 supported_versions workaround` line only means
   something when Firefox was the DTLS client.** It is written only on the
   client path (`transportlayerdtls.cpp:489-506`). A DTLS server never writes
   it, whatever the cap.
3. **`Wrote 28 bytes` is not necessarily an SCTP INIT.** A SACK chunk plus the
   common header is also 28 bytes, and working calls have hundreds of them.

A useful capture:

```
MOZ_LOG=timestamp,sync,webrtc_trace:5,mtransport:5,jsep:5,signaling:5,console:5,PageMessages:5
```

---

## If calls fail for you

1. Check you are on BuildID `20260914135622` or later (`about:support`).
2. In `about:config`, the four settings above should show the values in the
   "now" column. If one is **bold**, it was changed in your profile — reset it.
3. The tools below narrow it down further.

## Tools in this folder

| tool | what it does |
|---|---|
| `call_forensics.py` | read-only, 10 seconds: installed build, profile, call settings in the package vs the profile, camera/mic access, IPv6, crashes |
| `webrtc_selftest.py` | hidden browser, fake camera and mic, no network: proves ICE, DTLS with the cap live, a data channel and RTP audio/video in the installed build |
| `capture_call_log.py` | starts the browser with call logging (including the page's own messages), then reads the log when you close it |
| `analyze_call_log.py` | names the first layer that failed: signaling, gathering, ICE, DTLS, DTLS cap, SCTP, worker limit, IPv6 relays, or healthy. 14 regression cases in `test_analyze_call_log.py` |
| `compare_browsers_media.py` | runs the same test page in Gorilla and Edge and shows every difference: codecs, APIs, camera frames |
| `profile_prefs.py` | lists the settings your profile overrides, and sets or removes them with the browser closed |
| `publish_gate.py` | refuses a release unless the self-test passed, and refuses notes that mention calls unless a real call passed on that build with no profile-only settings |
