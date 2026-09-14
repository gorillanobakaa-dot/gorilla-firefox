"""Prove this build's WebRTC works - no network, no keyboard, no second person.

WHY THIS EXISTS
  2026-09-13: "WhatsApp and WebRTC calls now work" went into the release notes
  because media.peerconnection.dtls.version.max = 771 was found inside the
  installed omni.ja. Nothing had made a call. On 2026-09-14 calls still failed,
  and nobody could say whether the browser, the network or WhatsApp was at
  fault.

  This answers the half a machine can answer alone: does THIS binary, with its
  shipped defaults, complete ICE, a DTLS handshake, an SCTP data channel and
  RTP audio and video - and is the DTLS 1.2 cap in effect in the RUNNING
  browser, not merely present in a file?

WHY NOT MARIONETTE
  The Gorilla build physically locks out Marionette and the remote agent
  (remote/components/Marionette.sys.mjs and RemoteAgent.sys.mjs, marked
  "PHYSICAL LOCK"). That is deliberate hardening; this tool does not weaken it.

  Instead: a throwaway profile, the installed firefox.exe run --headless, and a
  page served from 127.0.0.1 that calls itself with two RTCPeerConnections and
  POSTs the result back. MOZ_LOG is captured and read by analyze_call_log.py.

  A loopback call makes the cap provable. One side is always the DTLS client,
  and only a client writes "Setting DTLS1.3 supported_versions workaround". A
  client setup with no such line proves max < 1.3 in the live process.

WHAT IT CANNOT PROVE
  That a WhatsApp call works from here. That needs WhatsApp's relays, a real
  network and a second person - capture_call_log.py is for that. Passing this
  and failing a real call points at the network path or the far end.

USAGE
    python "working scripts/webrtc_selftest.py"
    python "working scripts/webrtc_selftest.py" --keep     keep the test profile
"""
import argparse
import datetime
import http.server
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(os.environ.get("GORILLA_ROOT")
            or Path(__file__).resolve().parent.parent)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_call_log as acl      # noqa: E402
import verify_address_bar as vab    # noqa: E402  find_install(), build_id()

# sync: this tool stops the browser rather than waiting for it to exit, so
# nothing may sit in a write buffer.
LOG_MODULES = "sync,timestamp,mtransport:5,signaling:4,DataChannel:5"

# Throwaway-profile prefs. Everything NOT listed is the build's shipped default -
# which is the point: the DTLS cap, default_address_only and the rest are tested
# exactly as they ship.
USER_JS = {
    # fake camera and microphone: no hardware opened, no permission prompt
    "media.navigator.streams.fake": True,
    "media.navigator.permission.disabled": True,
    # A fresh profile would pull filter lists and remote settings over a metered
    # connection. Send web traffic to a dead local proxy. Loopback - the test
    # page - is never proxied, and WebRTC does not use this proxy.
    "network.proxy.type": 1,
    "network.proxy.http": "127.0.0.1",
    "network.proxy.http_port": 9,
    "network.proxy.ssl": "127.0.0.1",
    "network.proxy.ssl_port": 9,
    "network.proxy.allow_hijacking_localhost": False,
    # no first-run furniture
    "browser.shell.checkDefaultBrowser": False,
    "browser.startup.homepage_override.mstone": "ignore",
    "startup.homepage_welcome_url": "",
    "startup.homepage_welcome_url.additional": "",
    "browser.aboutwelcome.enabled": False,
    "datareporting.policy.firstRunURL": "",
    "browser.startup.page": 0,
    "browser.sessionstore.resume_from_crash": False,
    "extensions.update.enabled": False,
}

NOTICE = """
  WEBRTC SELF-TEST
  Starts a HIDDEN copy of the browser at
      %s
  with a throwaway profile, makes a call between two connections inside one
  test page, and reads the result.

    - no window appears, nothing is typed, the mouse is not used
    - your profile, tabs and WhatsApp session are not touched
    - fake camera and microphone: your real devices are not opened
    - the throwaway profile's web traffic goes to a dead local proxy, so it
      cannot use your data allowance; the test call stays on this PC
    - only the processes this test started are stopped at the end
"""

PAGE = r"""<!doctype html>
<meta charset="utf-8"><title>gorilla webrtc selftest</title>
<script>
const out = {ua: navigator.userAgent, steps: [], ok: false};
const step = s => out.steps.push([Math.round(performance.now()), s]);
const note = e => { out.notes = (out.notes || []).concat(String(e)); };
const within = (p, ms, what) => Promise.race([p, new Promise((_, rej) =>
  setTimeout(() => rej(new Error("timeout: " + what)), ms))]);
const typ = c => (/ typ (\w+)/.exec(c) || [])[1] || "?";

async function run() {
  try {
    try {
      const ac = new AudioContext({sampleRate: 16000});
      out.audiocontext_rate = ac.sampleRate;
      ac.close();
    } catch (e) { out.audiocontext_error = String(e); }

    step("getUserMedia");
    const stream = await within(
      navigator.mediaDevices.getUserMedia({audio: true, video: true}), 15000,
      "getUserMedia");
    out.tracks = stream.getTracks().map(t => t.kind + ":" + t.readyState);

    const pc1 = new RTCPeerConnection(), pc2 = new RTCPeerConnection();
    out.cands = {pc1: [], pc2: []};
    const pending = {to1: [], to2: []};
    let ready = false;
    pc1.onicecandidate = e => {
      if (!e.candidate || !e.candidate.candidate) return;
      out.cands.pc1.push(typ(e.candidate.candidate));
      if (ready) pc2.addIceCandidate(e.candidate).catch(note);
      else pending.to2.push(e.candidate);
    };
    pc2.onicecandidate = e => {
      if (!e.candidate || !e.candidate.candidate) return;
      out.cands.pc2.push(typ(e.candidate.candidate));
      if (ready) pc1.addIceCandidate(e.candidate).catch(note);
      else pending.to1.push(e.candidate);
    };

    stream.getTracks().forEach(t => pc1.addTrack(t, stream));
    const dc = pc1.createDataChannel("gorilla-selftest");
    const opened = new Promise(r => { dc.onopen = r; });
    const echoed = new Promise(r => {
      pc2.ondatachannel = ev => { ev.channel.onmessage = m => r(m.data); };
    });
    const kinds = new Set();
    const tracks = new Promise(r => {
      pc2.ontrack = ev => { kinds.add(ev.track.kind); if (kinds.size >= 2) r(); };
    });

    step("negotiate");
    await pc1.setLocalDescription();
    await pc2.setRemoteDescription(pc1.localDescription);
    await pc2.setLocalDescription();
    await pc1.setRemoteDescription(pc2.localDescription);
    ready = true;
    for (const c of pending.to2) await pc2.addIceCandidate(c).catch(note);
    for (const c of pending.to1) await pc1.addIceCandidate(c).catch(note);

    step("data channel");
    await within(opened, 20000, "data channel open");
    out.datachannel_open = true;
    dc.send("gorilla-ping");
    out.datachannel_echo = await within(echoed, 10000, "data channel message");

    step("media");
    await within(tracks, 10000, "remote audio and video tracks");
    await new Promise(r => setTimeout(r, 4000));
    const stats = await pc2.getStats();
    out.inbound = {};
    stats.forEach(s => {
      if (s.type === "inbound-rtp") {
        out.inbound[s.kind] = {packets: s.packetsReceived, bytes: s.bytesReceived};
      }
    });
    out.ice = {pc1: pc1.iceConnectionState, pc2: pc2.iceConnectionState};
    out.connection = {pc1: pc1.connectionState, pc2: pc2.connectionState};
    const a = out.inbound.audio || {}, v = out.inbound.video || {};
    out.ok = out.datachannel_echo === "gorilla-ping" &&
             (a.packets || 0) > 0 && (v.packets || 0) > 0;
    pc1.close(); pc2.close();
    stream.getTracks().forEach(t => t.stop());
  } catch (e) {
    out.error = String((e && e.message) || e);
  }
  step("report");
  await fetch("/result", {method: "POST",
                          headers: {"Content-Type": "application/json"},
                          body: JSON.stringify(out)});
}
run();
</script>
"""


def serve(page):
    state = {"result": None, "event": threading.Event()}

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.path.split("?")[0] not in ("/", "/index.html"):
                self.send_response(404)
                self.end_headers()
                return
            body = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n)
            try:
                state["result"] = json.loads(raw.decode("utf-8"))
            except Exception as exc:
                state["result"] = {"error": "unparseable result: %s" % exc}
            self.send_response(204)
            self.end_headers()
            state["event"].set()

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, state


def stop_tree(proc, profile):
    """Stop what THIS test started, and nothing else.

    --wait-for-browser keeps the launcher alive as the browser's parent, so
    killing its tree takes the browser and its children. As a backstop, any
    firefox.exe whose command line names our throwaway profile is stopped too.
    The user's own browser never has that profile on its command line.
    """
    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                   capture_output=True, text=True)
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='firefox.exe'\" | "
          "Where-Object { $_.CommandLine -like '*%s*' } | "
          "Select-Object -ExpandProperty ProcessId" % profile.name)
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=60)
        for pid in (r.stdout or "").split():
            if pid.strip().isdigit():
                subprocess.run(["taskkill", "/PID", pid.strip(), "/T", "/F"],
                               capture_output=True, text=True)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--yes", action="store_true",
                    help="skip the confirmation (only once the user has agreed)")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--keep", action="store_true", help="keep the throwaway profile")
    ap.add_argument("--install", default=None)
    args = ap.parse_args()

    install = Path(args.install) if args.install else vab.find_install()
    if not install or not (install / "firefox.exe").is_file():
        print("no installed Gorilla Unleashed found")
        return 2

    print(NOTICE % install)
    if not args.yes:
        if not sys.stdin.isatty():
            print("refusing: no terminal to confirm in. Pass --yes only after the "
                  "user has agreed to the run.")
            return 2
        if input("Run it? [y/N] ").strip().lower() not in ("y", "yes"):
            print("not run")
            return 1

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    state_dir = ROOT / "state"
    profile = state_dir / ("selftest-profile-" + stamp)
    logdir = state_dir / "selftest_logs" / stamp
    profile.mkdir(parents=True)
    logdir.mkdir(parents=True)
    (profile / "user.js").write_text(
        "".join("user_pref(%s, %s);\n" % (json.dumps(k), json.dumps(v))
                for k, v in USER_JS.items()), encoding="utf-8")

    srv, st = serve(PAGE)
    url = "http://127.0.0.1:%d/" % srv.server_address[1]
    env = dict(os.environ)
    env["MOZ_LOG"] = LOG_MODULES
    env["MOZ_LOG_FILE"] = str(logdir / "selftest.log")
    t0 = time.time()
    proc = subprocess.Popen(
        [str(install / "firefox.exe"), "--headless", "--wait-for-browser",
         "-no-remote", "-profile", str(profile), url],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("hidden browser started (pid %d); waiting up to %ds for the page..."
          % (proc.pid, args.timeout))
    got = st["event"].wait(args.timeout)
    elapsed = time.time() - t0
    stop_tree(proc, profile)
    srv.shutdown()
    time.sleep(2)

    page = st["result"] if got else {
        "error": "the page never reported back within %ds" % args.timeout}
    log = acl.analyze(logdir)
    c = log["counts"]
    inbound = page.get("inbound") or {}
    a = (inbound.get("audio") or {}).get("packets") or 0
    v = (inbound.get("video") or {}).get("packets") or 0
    ice = page.get("ice") or {}
    rate = page.get("audiocontext_rate")

    def st3(ok):
        return "PASS" if ok else "FAIL"

    checks = [
        ("page completed", st3(got and not page.get("error")),
         page.get("error") or "%.0fs" % elapsed),
        ("ICE connected", st3(ice.get("pc1") in ("connected", "completed")),
         "pc1=%s pc2=%s, candidates %s" % (ice.get("pc1"), ice.get("pc2"),
                                           (page.get("cands") or {}).get("pc1"))),
        ("data channel round-trip", st3(page.get("datachannel_echo") == "gorilla-ping"),
         "echo=%r" % page.get("datachannel_echo")),
        ("audio RTP received", st3(a > 0), "%d packets" % a),
        ("video RTP received", st3(v > 0), "%d packets" % v),
        ("DTLS handshake", st3(c.get("handshakes", 0) > 0),
         "%d completed" % c.get("handshakes", 0)),
        ("DTLS 1.2 cap live",
         st3(c.get("dtls_client", 0) > 0 and not c.get("dtls13_offered")),
         log["dtls_cap"]),
    ]
    # Handover PART 6.2. 01.MEDIA, which forced 48000 on Linux, is disabled on
    # Windows, so 16000 is expected. A headless run may be unable to build an
    # AudioContext at all; that is "n/a", not a pass and not a failure.
    if rate is not None:
        checks.append(("AudioContext 16000 Hz", st3(rate == 16000), "got %s" % rate))
    else:
        checks.append(("AudioContext 16000 Hz", "n/a",
                       page.get("audiocontext_error") or "not reported"))
    passed = all(s != "FAIL" for _, s, _ in checks)

    result = {
        "passed": passed,
        "build_id": vab.build_id(install),
        "install": str(install),
        "when": datetime.datetime.now().isoformat(timespec="seconds"),
        "checks": [[n, s, d] for n, s, d in checks],
        "page": page,
        "log": {k: log[k] for k in ("layer", "detail", "dtls_cap", "counts",
                                    "local_candidate_types", "pair_states", "files")},
        "log_dir": str(logdir),
        "test_profile_prefs": USER_JS,
    }
    out = state_dir / "webrtc_selftest.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    if not args.keep:
        shutil.rmtree(profile, ignore_errors=True)

    print("")
    for n, s, d in checks:
        print("  [%-4s] %-26s %s" % (s, n, d))
    print("")
    print("RESULT: %s   (recorded: %s)" % ("PASS" if passed else "FAIL", out))
    print("logs:   %s" % logdir)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
