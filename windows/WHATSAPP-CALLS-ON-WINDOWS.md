# WhatsApp Web calls on Windows — what was wrong, and the report back

**Written 2026-09-14 on the Windows build machine, answering
`firefox-whatsapp-call-handover-to-windows-26-09-13.md` from the Linux side.**

## Short version

Calls work on Windows as of **v155.0.1-win64.4** (BuildID `20260914135622`),
verified with a real, logged WhatsApp call on that exact build with no settings
changed by hand.

The DTLS 1.2 cap from the handover was a real fix and it is in the build. It was
**not the whole fix.** The remaining cause was:

```
pref("dom.workers.maxPerDomain", 8);
```

Upstream Firefox sets **512** (`all.js`: "effectively infinite, while preventing
abuse"). WhatsApp Web runs more workers than 8, and the one its call engine
needs was queued. Symptom: you hear ringing, the far phone never rings and
shows "Connecting…", your camera light comes on but the call never uses it,
and the call drops.

The v155.0.1-win64.3 release notes claimed calls worked. That claim had not
been tested and was wrong. The page now carries a correction.

---

## Answers to the handover's PART 8

| # | question | answer |
|---|---|---|
| 1 | `media.peerconnection.dtls.version.max` in the running browser | **771.** Proven from the call log rather than about:config: 9 DTLS client setups, none offered 1.3 |
| 2 | `new AudioContext({sampleRate: 16000}).sampleRate` | **16000**, measured twice (hidden self-test and a Gorilla-vs-Edge comparison). PART 3 was right: the 48 kHz fault does not exist on Windows |
| 3 | real call connected with audio both ways | **Yes**, on BuildID `20260914135622`, confirmed by the person making the call |
| 4 | BuildID tested | `20260914135622` |
| 5 | `Setting DTLS1.3 supported_versions workaround` in the log | **Absent** — alongside 9 "Setting up DTLS as client" lines, which is what makes the absence meaningful (see correction 2) |

---

## How it was found — the order matters

Every transport log was clean from the first capture. The answer was in the
**web page's own warnings**, which nobody was logging.

1. **Logged call, v155.0.1-win64.3.** Relay legs up, DTLS 1.2 live, 11
   data-channel messages, then silence. Seven legs failed ICE, each offered
   only an IPv6 relay on an IPv4-only phone hotspot. Blamed the network.
   **Wrong.**
2. **Same laptop, same hotspot, web.whatsapp.com in Edge:** video both ways.
   The network was fine. The IPv6 legs fail in working calls too; they are
   harmless.
3. **Hidden side-by-side test, Gorilla vs Edge.** Camera fine in both. Gorilla's
   WebCodecs could not decode Opus or VP8 because `media.webm.enabled` and
   `media.ogg.enabled` were false (the Linux "H.264 hard-lock") — WebCodecs
   checks VP8 against the WebM container and Opus against Ogg. Fixed that in a
   throwaway profile; **a real call still failed.**
4. **Logged call with the page's messages** (MOZ_LOG modules `console` and
   `PageMessages`):

   > A Worker could not be started immediately because other documents in the
   > same origin are already using the maximum number of workers. The Worker is
   > now queued …

   16 ms before the call's first PeerConnection, and five more in the next 12
   seconds.
5. **Raised only `dom.workers.maxPerDomain` to 512:** no worker queued, 793
   data-channel messages in 21 seconds (against 11–12), a working call.

The v155.0.1-win64.4 build carries all three: workers 512, WebM on, Ogg on.
The WebM/Ogg change is correct for WebCodecs but was not proven necessary on
its own.

---

## Two corrections to the handover's PART 6.3, for Firefox 155

1. **`Wrote 28 bytes to SSL Layer` needs `mtransport:5`, not `:4`.** It is
   logged at `ML_DEBUG`, which `dom/media/webrtc/transport/logging.h` maps to
   `LogLevel::Verbose`. At `:4` the line is never written, so "no long runs of
   28-byte writes" passes on the very blackhole it is meant to catch.
2. **The DTLS 1.3 line only proves something when Firefox was the DTLS
   client.** It is written only on the client path
   (`transportlayerdtls.cpp:489-506`). A DTLS server never writes it, whatever
   the cap.

Also: **"Wrote 28 bytes" is not necessarily an SCTP INIT.** A SACK chunk plus
the common header is also 28 bytes, and working calls have hundreds of them.

---

## An open question for the Linux side

**Linux ships the same `dom.workers.maxPerDomain = 8`** (it is in the shared
pref block), and Linux calls work. Why is not established. Possibilities worth
checking on Linux, cheapest first:

- capture a call with `MOZ_LOG=timestamp,console:5,PageMessages:5` and look for
  "A Worker could not be started immediately" — it may be happening and being
  tolerated
- WhatsApp may start fewer workers for a Linux user agent
- the Linux 01.MEDIA patches may change how many workers WhatsApp's media path
  needs

If it is happening on Linux too, raise it to 512 there as well.

---

## Tools that came out of this (in this folder)

| tool | what it does |
|---|---|
| `webrtc_selftest.py` | hidden browser, fake camera and mic, no network: proves ICE, DTLS with the cap live, a data channel and RTP audio/video in the installed build |
| `capture_call_log.py` | starts the browser with call logging (including the page's own messages), then reads the log when you close it |
| `analyze_call_log.py` | names the first layer that failed: signaling, gathering, ICE, DTLS, DTLS cap, SCTP, worker limit, IPv6 relays, or healthy. 14 regression cases in `test_analyze_call_log.py` |
| `compare_browsers_media.py` | runs the same test page in Gorilla and Edge and shows every difference: codecs, APIs, camera frames |
| `publish_gate.py` | refuses a release unless the self-test passed, and refuses notes that mention calls unless a real call passed on that build with no profile-only settings |
