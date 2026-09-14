<!-- Version: 1.0.0 · written 26-09-14 · from the Windows build machine -->

# HANDOVER TO THE LINUX SIDE: what Windows found about WhatsApp calls

**Written 2026-09-14 on the Windows machine (Lenovo, i7-1255U). For whoever
maintains Gorilla Firefox on Linux. It answers
`firefox-whatsapp-call-handover-to-windows-26-09-13.md`.**

Read the whole file before running anything. Every command is complete. Where
something is inference rather than measurement, it says so.

---

## PART 0: THE SHORTEST POSSIBLE VERSION

1. **Your DTLS 1.2 cap was correct and necessary.** It is in the Windows build
   and proven live in real call logs. Thank you.
2. **It was not enough on Windows.** Calls still failed. The remaining cause was
   one pref in the shared Gorilla pref block:

   ```
   pref("dom.workers.maxPerDomain", 8);
   ```

   Upstream Firefox sets **512**. WhatsApp Web's call engine needs a worker, the
   worker was **queued** by that limit, and the call never started.
3. **Linux ships the same value of 8**, and Linux calls work. **Nobody knows why
   yet.** That is the one question this handover asks you to answer, with
   measurement. It takes one logged call. See PART 4.
4. **Nothing in the Linux build was changed.** `patches/05.PREFS/` is untouched.
   All Windows changes are in `patches/17.WINDOWS.FIXES.2026-09-09/` and
   `windows/`.

Windows release **v155.0.1-win64.4** (BuildID `20260914135622`) has working
calls, verified with real logged WhatsApp calls on that exact build, and again
after downloading the published installer from GitHub.

---

## PART 1: WHAT WAS ACTUALLY WRONG ON WINDOWS

### 🧸 LAYMAN

A website is allowed to run a number of helper programs in the background,
called workers. WhatsApp Web uses several at once. Gorilla had lowered the
allowance to 8. Firefox's normal allowance is 512.

When WhatsApp started a call, it asked for one more helper to run the call. The
browser said "you already have your 8, wait in the queue". The helper never
started. So your side played a ringing sound, but nothing was ever sent to the
other phone. It showed "Connecting…" and never rang. The camera light came on,
but no picture was ever used.

Raising the allowance back to 512 fixed it on the very next call.

### 💻 DEVELOPER

The page's own warning, captured through the MOZ_LOG `PageMessages` module:

```
W/PageMessages [JavaScript Warning: "A Worker could not be started immediately
because other documents in the same origin are already using the maximum number
of workers. The Worker is now queued and will be started after some of the
other workers have completed."]
```

Timeline of the decisive failed call, UTC:

| time | event |
|---|---|
| 09:12:28.256 | worker queued |
| 09:12:28.272 | first PeerConnection configured, 16 ms later |
| 09:12:39–40 | five more workers queued |
| — | 11 data-channel messages in total, then only keepalives |

The same call with only `dom.workers.maxPerDomain` raised to 512: **0 workers
queued, 793 data-channel messages in 21 seconds**, connected with audio and
video.

The limit is read once, at `RuntimeService` init
(`dom/workers/RuntimeService.cpp`, `PREF_WORKERS_MAX_PER_DOMAIN`), so it needs
a browser restart to take effect.

**Every transport log was clean from the very first capture.** ICE up, DTLS 1.2
up, SCTP up, data channels open. The defect was never in the transport. That
is why it took four logged calls: the logs being read were the wrong logs.

---

## PART 2: THE WRONG TURNS, SO YOU DO NOT REPEAT THEM

Each of these looked right and was measured and dropped.

1. **"The DTLS cap is the whole fix."** Your handover said so, and flagged that
   it had never been tested on Windows. The Windows side then published release
   notes saying calls worked without making a call. That was wrong, and the .3
   release page now says so. **A pref present in a file is not a working call.**
2. **"It's the network."** The failed calls each had several connection legs
   that were offered only IPv6 relay addresses (`2a03:2880:…:face:b00c`), on a
   phone hotspot with no IPv6. They can never connect. But **the working call
   had the same failing IPv6 legs.** They are harmless side legs. Edge on the
   same hotspot made the call fine.
3. **"It's the camera."** A hidden test opened the real camera in Gorilla and
   in Edge. Right device, bright frames, local encode and decode fine.
4. **"It's the codecs."** Partly real. `media.webm.enabled` and
   `media.ogg.enabled` were false (the "H.264 hard-lock"). Firefox's WebCodecs
   decides VP8 support by checking the WebM container, and Opus by checking Ogg
   (`dom/media/webcodecs/WebCodecsUtils.cpp`, `GuessContainers`). So Gorilla
   Windows could not WebCodecs-decode VP8 or Opus. Flipping both fixed WebCodecs
   in a throwaway profile. **A real call still failed.** Right about a defect,
   wrong about the cause. The Windows build now ships both as true anyway.
5. **"It's the 48 kHz AudioContext bug."** Your PART 3 was right: it cannot
   occur on Windows. Measured twice: `new AudioContext({sampleRate: 16000})`
   returns 16000.
6. **"Platform audio processing breaks the Windows mic."** Suspected, then
   withdrawn after reading further. cubeb opens every input stream with
   processing NONE, and WASAPI's setter always returns NOT_SUPPORTED. The pref
   is inert on Windows.

---

## PART 3: CORRECTIONS TO YOUR PART 6.3, FOR FIREFOX 155

Checked against the 155 source, not assumed.

1. **`Wrote 28 bytes to SSL Layer` needs `mtransport:5`, not `:4`.** It is
   logged at `ML_DEBUG`, and `dom/media/webrtc/transport/logging.h` maps
   `ML_DEBUG` to `LogLevel::Verbose`. At `:4` the line is never written, so
   "no long runs of 28-byte writes" passes on the very blackhole it describes.
2. **`Setting DTLS1.3 supported_versions workaround` proves something only on
   the DTLS client side.** It is written on the client path only
   (`transportlayerdtls.cpp:489-506`). When Firefox is the DTLS server, the line
   never appears, whatever the cap. Check for `Setting up DTLS as client`
   alongside it.
3. **A 28-byte write is not necessarily an SCTP INIT.** An SCTP SACK plus the
   common header is also 28 bytes. The working Windows call had 327 of them.
   Judge by whether data flowed (`OnMessageReceived` count), not by 28-byte
   writes.
4. **Log the page, not just the transport.** Add `console:5,PageMessages:5`.
   `console` carries the page's `console.*` calls
   (`dom/console/Console.cpp:915`). `PageMessages` carries everything sent to
   the console service, including uncaught script errors and the worker warning
   above (`xpcom/base/nsConsoleService.cpp:58`). This is what found the cause.

---

## PART 4: WHAT TO DO ON LINUX, STEP BY STEP

### Step 1: Get the repository up to date, safely

Do **not** use `reset --hard` if you have uncommitted work. Your own handover
warned about that, and it nearly destroyed a day of Windows work.

```
git -C <your repo folder> status --short
git -C <your repo folder> fetch origin
git -C <your repo folder> log --oneline -3 origin/master
```

The last command must show `ccf373d` or newer. If you have local commits, merge:

```
git -C <your repo folder> merge origin/master
```

What changed since your `ddc2319`:

| commit | what |
|---|---|
| `86f0fcd` | patch group 17 only: `dom.workers.maxPerDomain` 512, `media.ogg.enabled` true, `media.webm.enabled` true; Windows call-verification tools in `windows/` |
| `ccf373d` | docs: `windows/WHATSAPP-CALLS-ON-WINDOWS.md`, `windows/README.md`, `windows/WORKING-SCRIPTS.md`, root README link, group 17 README |

`patches/05.PREFS/` still has, as before:

```
browser_app_profile_firefox.js.patch:920   pref("dom.workers.maxPerDomain", 8);
browser_app_profile_firefox.js.patch:956   pref("media.ogg.enabled", false);
browser_app_profile_firefox.js.patch:974   pref("media.peerconnection.dtls.version.max", 771);
modules_libpref_init_all.js.patch:47       pref("media.webm.enabled", false);
```

### Step 2: Capture one logged WhatsApp call on Linux, with the page's messages

Close the browser **completely** first (your trap 1: MOZ_LOG never reaches a
browser that is already running). Then:

```
mkdir -p /tmp/wa-call-linux
export MOZ_LOG=timestamp,mtransport:5,signaling:4,DataChannel:5,MediaManager:4,cubeb:4,console:5,PageMessages:5
export MOZ_LOG_FILE=/tmp/wa-call-linux/call.log
gorilla-unleashed
```

Use whatever command starts your installed Gorilla browser in place of
`gorilla-unleashed`. Place one short WhatsApp call to a real person. Close the
browser completely. Then:

```
cat /tmp/wa-call-linux/* | grep -c "Worker could not be started immediately"
cat /tmp/wa-call-linux/* | grep -c "OnMessageReceived"
```

### Step 3: Read it with the analyzer (pure standard-library Python)

`windows/analyze_call_log.py` has no Windows dependencies. It reads any MOZ_LOG
capture directory:

```
python3 <your repo folder>/windows/analyze_call_log.py /tmp/wa-call-linux
```

It prints each layer (legs, ICE, DTLS, the DTLS cap evidence, SCTP, data flow,
workers queued) and the first layer that failed. Its regression test also runs
on Linux:

```
python3 <your repo folder>/windows/test_analyze_call_log.py
```

It must print `14/14 passed`.

Do not use `capture_call_log.py` or `webrtc_selftest.py` on Linux as they are.
They call Windows-only commands (`tasklist`, `taskkill`, PowerShell).

### Step 4: Decide, from the numbers

- **Workers queued > 0 on Linux, but the call still works:** the limit is being
  hit and tolerated. Still raise it to 512. Upstream's value is the safe one.
- **Workers queued = 0:** WhatsApp starts fewer workers on Linux. Possible
  reasons, not measured: the Linux user agent, or the 01.MEDIA patches changing
  WhatsApp's media path. Raising to 512 is still harmless and removes the
  platform difference. Your call.

To raise it on Linux, edit **only** `patches/05.PREFS/browser_app_profile_firefox.js.patch`.
Group 17 is a separate full copy and is already 512 (your trap 5, from the
other direction).

### Step 5: Optional, WebCodecs on Linux

In the Linux browser's web console (F12) on any `https://` page:

```javascript
[(await AudioDecoder.isConfigSupported({codec: "opus", sampleRate: 48000, numberOfChannels: 1})).supported,
 (await VideoDecoder.isConfigSupported({codec: "vp8", codedWidth: 640, codedHeight: 480})).supported]
```

On Windows before the fix this printed `[false, false]`. Your 01.MEDIA
WebCodecs override (2026-08-11) forces VP8 support under
`media.gorilla.hardware_only_mode`, so Linux probably prints `[false, true]`.
Linux calls work that way, so **do not change it on this evidence alone.** It
is recorded so the two platforms' behaviour is understood.

---

## PART 5: TRAPS LEARNED ON WINDOWS THAT APPLY TO YOU TOO

1. **Do not write "calls work" anywhere until a real logged call passed on that
   exact build.** On Windows this is now enforced: the publish gate refuses
   release notes that mention calls unless a call result is recorded for the
   build's hash, with no profile-only prefs.
2. **A pass that needs a hand-edited profile is not a pass for the installer.**
   The first working Windows call used three prefs set in the tester's profile.
   It was rebuilt with them in the build, the profile overrides were removed,
   and the call was repeated.
3. **One leg up is not a working call, and one leg down is not a failed call.**
   WhatsApp opens many PeerConnections. The first version of the analyzer said
   "healthy" when 4 of 11 connected, then blamed the harmless IPv6 legs. Judge
   by data flow.
4. **Marionette and the remote agent are physically locked out of this build**
   (`remote/components/Marionette.sys.mjs`, "PHYSICAL LOCK"). Any scripted test
   has to work another way. The Windows self-test serves a page from 127.0.0.1
   that reports its result back over HTTP.
5. **Release pages must be corrected when a later build supersedes them.** The
   older Windows banners pointed at .3, which also had broken calls. They now
   point at .4. The Linux `v154.0a1-1` release still serves the pre-DTLS-fix
   `.deb` under the same version string (your trap 7). That is still true and
   still yours to decide.

---

## PART 6: WHAT TO REPORT BACK

Answer these explicitly rather than "done":

1. How many `Worker could not be started immediately` lines the Linux call log
   contained. The actual number.
2. How many `OnMessageReceived` lines. The actual number.
3. What `analyze_call_log.py` printed for `LAYER` and `DATA`.
4. Whether the call connected with audio both ways.
5. What the console check in Step 5 printed.
6. Whether you raised `dom.workers.maxPerDomain` on Linux, and the commit if so.

Send the capture directory, or the analyzer's full output, rather than a
summary of it.

---

## PART 7: PROVENANCE

- **Measured on Windows, 2026-09-14:** the worker-queue warning and its timing,
  the before/after message counts, working calls on BuildID `20260914135622`
  with no profile overrides, the WebCodecs results in Gorilla and in Edge, the
  IPv6-only legs failing in both failed and working calls, DTLS 1.2 proven live
  in every capture, and AudioContext 16000.
- **Inference:** that WhatsApp starts fewer workers on Linux. **Not measured.
  Linux was not touched from the Windows side.**
- **Not verified from Windows:** anything about the Linux build, the Linux
  profile, or the Linux 01.MEDIA code paths beyond reading the patch files.
- Full Windows account, in the repository:
  `windows/WHATSAPP-CALLS-ON-WINDOWS.md`.
