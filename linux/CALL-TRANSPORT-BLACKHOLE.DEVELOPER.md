<!-- Version: 1.1.0 · updated 26-08-26-11-46 -->
# WhatsApp call transport blackhole: DTLS 1.3 vs Meta relays. Audit record

**Dates:** 2026-08-25 evening (diagnosis), 2026-08-26 morning (fix proven).
**Prequels:** WEBCODECS-CALL-PATH.DEVELOPER.md, WEBCODECS-VP8-GATE.DEVELOPER.md.
**Binary under test:** installed deb, BuildID 20260811184252 (the verified
2026-08-11 20:10 libxul). Profile: ff154-main, gate prefs active.

## Symptoms (owner report, live call, callee answered)

Perpetual ring, self-view never initializes, hang-up button dead. Callee
answered, heard nothing, was not heard, call self-terminated after ~3 min.
UI later showed "Check your internet connection or try switching networks."

## Layer-by-layer verdicts (all measured on the real binary)

| Layer | Verdict | Evidence |
|---|---|---|
| Camera/mic (OS + gUM) | CLEAN | headless probe: 640x480 frames, luma 52, tracks live; permissions Allowed |
| WebCodecs video | CLEAN, and changed | WhatsApp self-test now uses avc1.42001f, NOT vp8: encode 1 keyframe (910 B) then decode it, real frame out. The "reject the promise for flush 1" that follows is their own close() racing their flush(), benign |
| WebCodecs audio | HOLE (parked, now active blocker) | AudioDecoder.isConfigSupported opus resolves {supported:false}; encoder true. Opus/Vorbis decode excised browser-wide with AgnosticDecoderModule; mp3/aac/pcm fine; libwebrtc private Opus unaffected (why the 08-14 WebRTC voice call worked) |
| Signaling | CLEAN | 19 PCs, every one completed negotiation, application m-section sending=1 receiving=1 |
| ICE | CLEAN (bookkeeping noise aside) | host-only local (default_address_only), remote = Meta edges 57.144.{63,17,245}.57:3478 typ host; prflx pairs (local 31.205.107.200:port) SUCCEEDED + nominated on 5 PCs. Host-pair FAILED entries are the same flow recorded before the reflexive discovery |
| DTLS | Handshake CLEAN, then poisoned | "SSL handshake completed" x7; log shows "Setting DTLS1.3 supported_versions workaround" x17 |
| SCTP over DTLS | **BLACKHOLE (the killer)** | 223x "Wrote 28 bytes to SSL Layer" (SCTP INIT size) into open tunnels, zero replies, zero channel opens, EnsureDataConnection x38/19 PCs, one lonely DataChannelConnection destroy. 17-PC churn for ~3 min, then app gives up |
| Network | EXONERATED | scripted STUN Binding to the same three relays: 100% responses, incl. flood (3 rounds x 60 parallel = 100%). Public IP 31.205.107.200 identical to the working 08-12 session (ASK4) |

## Root cause (proven by fix)

Firefox 154 negotiates DTLS 1.3 for WebRTC. Meta's call relays complete the
1.3 handshake but never respond to any application-data record (SCTP INIT
retransmitted forever). DTLS 1.3 changed the record layer (unified header);
a relay demuxing STUN/DTLS/SRTP with 1.2-era parsing drops 1.3 data records
silently. Chromium's working call of 2026-08-11 used DTLS 1.2. (Mechanism
inside Meta's box is inference; everything else is measured.)

**Fix (per-profile, one line, ff154-main user.js):**

    user_pref("media.peerconnection.dtls.version.max", 771);  // cap at DTLS 1.2

**Proof (2026-08-26 ~09:43 UTC, live call, wa-call3 capture):** the 1.3
workaround log line disappears, 5 DTLS handshakes, 4x "Calling AnnounceOpen
on RTCDataChannel" (channels OPEN to the page), sustained bidirectional
flow: ~10 msg/s inbound (OnMessageReceived, binary, dispatched) and steady
SendPacketWithStatus outbound, minutes long. Blackhole gone.

Consider shipping the cap as a build default until Meta handles 1.3; revisit
on Firefox updates.

## Remaining blocker: CONVICTED 2026-08-26 late morning

With transport up, media flowed BOTH WAYS (7 MB down / 8 MB up in 116 s,
~100 pkt/s each way) yet both ends stayed deaf and the UI sat on
"Connecting...". Wire arithmetic: the large packets are ~2 fragmented VIDEO
messages/s each way; the small ones are SACKs. AUDIO was never produced by
EITHER side.

Cause, each link measured:
1. WhatsApp requests a 16 kHz audio engine: wa-call6 live capture,
   `D/WebAudioAPI AudioContext sampleRate=16000` (their WASM voice pipeline;
   WebCodecs audio is never asked for, so the Opus hole is NOT in this path).
2. The 2026-08-11 audio-cascade patch to AudioContext.cpp ("GORILLA TWEAK:
   Force 48000Hz native playback to match ALC269 clock rate") silently
   returns 48000 for EVERY realtime context under hardware_only_mode,
   discarding the page's explicit request. Measured on the installed binary:
   asked 16000 -> got 48000; asked 44100 -> got 48000; no error thrown;
   offline contexts honored.
3. Spec says honor-or-throw. We do neither; the page is silently lied to.
   Their pipeline detects the mismatch and shuts the audio leg down, both
   directions; video (no AudioContext involvement) flows regardless.
4. Chromium honors 16000: their calls work. The 2026-08-14 voice call used
   classic WebRTC (libwebrtc audio, no page AudioContext in the media path).

Fix (rebuild, 3 lines): in GetSampleRateForAudioContext, return the page's
rate whenever explicitly requested (`aIsOffline || aSampleRate != 0.0`),
apply the 48000 steer ONLY to no-preference contexts. The tweak's intent
survives (default contexts match the ALC269 clock); cubeb resampling covers
explicit-rate contexts exactly as stock Firefox always has. This tweak is a
web-compat landmine beyond WhatsApp: anything WASM-audio with a fixed rate
(speech recognition, other call apps) hits the same wall.

NOT the blocker: the excised Opus decode (real hole, documented above, but
WhatsApp call audio is WASM over the DataChannel and never consults it).
Re-admitting it is now optional hardening, not the call fix. A
hardware_only_mode=false master-flip test on 2026-08-26 was CONFOUNDED (the
switch changes many behaviors and is inconsistently honored per the
2026-08-12 lesson; the call died earlier in that mixed state) and was
reverted; do not rerun it as evidence either way.

Rebuild path is GitHub master, which was found stale (see below).

## Repo finding (same evening)

GitHub master (the ONLY rebuild path since the 2026-08-12 decommission)
carried 3 stale patch masters: StaticPrefList.yaml.patch missing BOTH gate
prefs (build dies at compile: C++ references the pref), WebCodecsUtils.cpp
patch missing the vp8-iff-pref clause, one cosmetic ftl. Found by content-
diffing all 319 patch pairs, after `git grep webcodecs_software_vp8
origin/master` hit C++ patches but not the yaml that defines it. Repair:
commit e24a62e on branch fix/stale-patch-masters, unpushed, awaiting owner.
Also: the Aug-4 GitHub release still serves a pre-fix deb under the SAME
version string 154.0a1-1; dpkg cannot distinguish them.

## Diagnostic traps recorded (do not re-learn)

- **Env vars do not reach an already-running instance.** `MOZ_LOG=... ff154`
  with the browser open remotes into the old process; the log file appears,
  0 bytes, no children. Close fully first (pgrep to verify).
- **MOZ_LOG level 3 hides D/ lines.** WebCodecs:3 silences the codec Debug
  logging; absence of audio lines proved nothing. Use :5 when the question
  is "did the site call this API".
- **No timestamps unless the "timestamp" module is listed.** The 08-25
  captures cannot be sequenced; the 08-26 one can.
- **ff154 launcher pointed at the decommissioned build tree** (~/firefox-main
  obj dir, deleted 08-12). Repointed to /usr/lib/gorilla-unleashed/firefox,
  stamped 1.0.0.
- The wedge triple (ring forever + no camera + dead controls) = early abort
  in WhatsApp's setup, NOT a camera bug and NOT the slow-script watchdog
  (which is off on this machine).
- prflx pairs SUCCEEDING while their host twins show FAILED is normal nICEr
  bookkeeping under default_address_only, not a contradiction.

## MOZ_LOG recipes that produced this record

    # codec question (level 5 or you see nothing):
    MOZ_LOG="timestamp,WebCodecs:5" MOZ_LOG_FILE=/tmp/x.log ff154
    # transport question:
    MOZ_LOG="timestamp,mtransport:4,signaling:4,DataChannel:5" MOZ_LOG_FILE=/tmp/x.log ff154

Captures live in /tmp/wa-call{,2,3}.log.* (session artifacts, not committed:
they carry PC ids and addresses). STUN probe scripts: session scratchpad
(stunprobe.py, stunflood.py), method described here: minimal RFC 5389
Binding Request, XOR-MAPPED-ADDRESS parse.

## Not verified yet

- A call with audible audio (needs the rebuilt AudioContext.cpp).
- ANSWERED 2026-08-26: the callee heard NOTHING on the fixed transport, and
  the cause was later convicted as the AudioContext sample-rate force (see
  the Remaining blocker section), not the Opus hole.
- Whether WhatsApp also requires VP8 WebCodecs anywhere once audio works
  (today it probed H.264 only).
- dom.max_script_run_time=30 adequacy on other 2012-class CPUs (unchanged).
