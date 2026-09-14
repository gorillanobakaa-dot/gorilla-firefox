"""Run the same media test page in Gorilla and in Edge, and show what differs.

WHY THIS EXISTS
  A WhatsApp video call from Gorilla sat on "Connecting..." at both ends. The
  capture showed two legs reaching Meta's IPv4 relays with DTLS and data
  channels up - and then nothing but keepalive traffic for two minutes. The
  call's own camera preview was black although the camera light was on.

  Minutes later, on the same machine and network with nothing changed,
  web.whatsapp.com in Edge made the call with video both ways.

  So the network carries WhatsApp calls, and the analyzer's "IPv6 relays"
  verdict, true as a description of seven failed legs, was not the reason the
  call failed. What Gorilla failed to do was produce media. The question is no
  longer "which layer of the network" but "what can Edge do with a camera that
  Gorilla cannot" - and that is answered by asking both the same questions.

WHAT IT ASKS EACH BROWSER
  - which WebCodecs encoders and decoders it supports (H.264, VP8, VP9, AV1,
    Opus at 48 kHz and 16 kHz, AAC) - WhatsApp's call audio has been seen
    using WebCodecs and a 16 kHz pipeline
  - which RTP codecs WebRTC offers
  - whether the frame-processing APIs a web call app may depend on exist, in
    the page and in a worker (MediaStreamTrackProcessor, VideoTrackGenerator,
    RTCRtpScriptTransform, SharedArrayBuffer, AudioWorklet...) - served with
    COOP/COEP so cross-origin isolation matches what WhatsApp requests
  - with the real camera (unless --no-camera): does a <video> element get
    frames, are they not black, and does a local WebRTC loop encode and decode
    them

WHAT IT DOES NOT TOUCH
  Throwaway profiles for both browsers; your Gorilla profile, your Edge
  profile and WhatsApp are not involved. Web traffic goes to a dead local
  proxy, so no data allowance is used. No microphone. The camera is opened for
  about five seconds per browser, one browser at a time. Only processes whose
  command line names this run's throwaway profile are stopped - your own Edge
  and Gorilla windows are left alone.

USAGE
    python "working scripts/compare_browsers_media.py"
    python "working scripts/compare_browsers_media.py" --no-camera
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
import verify_address_bar as vab    # noqa: E402  find_install(), build_id()
import webrtc_selftest as wst       # noqa: E402  USER_JS for a quiet throwaway profile

EDGE_CANDIDATES = [
    Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    / "Microsoft" / "Edge" / "Application" / "msedge.exe",
    Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    / "Microsoft" / "Edge" / "Application" / "msedge.exe",
]

NOTICE = """
  MEDIA COMPARISON - Gorilla vs Edge
  Opens a HIDDEN copy of each browser, one after the other, with a throwaway
  profile, and runs the same local test page in both.

    - no window appears, nothing is typed, the mouse is not used
    - your own Gorilla and Edge profiles, tabs and WhatsApp are not touched
    - no microphone; the camera is %s
    - web traffic goes to a dead local proxy - no data allowance used
    - only processes started by this run are stopped at the end
"""

PAGE = r"""<!doctype html>
<meta charset="utf-8"><title>gorilla media compare</title>
<body>
<script>
const out = {ua: navigator.userAgent};
const sleep = ms => new Promise(r => setTimeout(r, ms));
const within = (p, ms, what) => Promise.race([p, new Promise((_, rej) =>
  setTimeout(() => rej(new Error("timeout: " + what)), ms))]);
const S = async fn => { try { return await fn(); }
                        catch (e) { return "ERR " + ((e && (e.name + ": " + e.message)) || e); } };

async function codecs() {
  const r = {};
  const vc = {"H.264 baseline": "avc1.42E01F", "H.264 constrained": "avc1.42001f",
              "VP8": "vp8", "VP9": "vp09.00.10.08", "AV1": "av01.0.04M.08"};
  r.video_encode = {}; r.video_decode = {};
  for (const [n, c] of Object.entries(vc)) {
    r.video_encode[n] = await S(async () => typeof VideoEncoder === "undefined" ? "no API" :
      (await VideoEncoder.isConfigSupported({codec: c, width: 640, height: 480,
                                             bitrate: 500000, framerate: 30})).supported);
    r.video_decode[n] = await S(async () => typeof VideoDecoder === "undefined" ? "no API" :
      (await VideoDecoder.isConfigSupported({codec: c, codedWidth: 640, codedHeight: 480})).supported);
  }
  const ac = {"Opus 48k": ["opus", 48000], "Opus 16k": ["opus", 16000], "AAC": ["mp4a.40.2", 48000]};
  r.audio_encode = {}; r.audio_decode = {};
  for (const [n, [c, sr]] of Object.entries(ac)) {
    r.audio_encode[n] = await S(async () => typeof AudioEncoder === "undefined" ? "no API" :
      (await AudioEncoder.isConfigSupported({codec: c, sampleRate: sr, numberOfChannels: 1,
                                             bitrate: 32000})).supported);
    r.audio_decode[n] = await S(async () => typeof AudioDecoder === "undefined" ? "no API" :
      (await AudioDecoder.isConfigSupported({codec: c, sampleRate: sr, numberOfChannels: 1})).supported);
  }
  r.rtp = {
    video: await S(async () => [...new Set(RTCRtpSender.getCapabilities("video").codecs
                                  .map(x => x.mimeType))].sort().join(" ")),
    audio: await S(async () => [...new Set(RTCRtpSender.getCapabilities("audio").codecs
                                  .map(x => x.mimeType))].sort().join(" ")),
  };
  r.page_apis = {
    MediaStreamTrackProcessor: typeof MediaStreamTrackProcessor,
    MediaStreamTrackGenerator: typeof MediaStreamTrackGenerator,
    VideoTrackGenerator: typeof VideoTrackGenerator,
    RTCRtpScriptTransform: typeof RTCRtpScriptTransform,
    createEncodedStreams: typeof RTCRtpSender !== "undefined" ?
      typeof RTCRtpSender.prototype.createEncodedStreams : "no RTCRtpSender",
    AudioWorkletNode: typeof AudioWorkletNode,
    SharedArrayBuffer: typeof SharedArrayBuffer,
    crossOriginIsolated: String(self.crossOriginIsolated),
    OffscreenCanvas: typeof OffscreenCanvas,
    requestVideoFrameCallback: typeof HTMLVideoElement.prototype.requestVideoFrameCallback,
    canvasCaptureStream: typeof HTMLCanvasElement.prototype.captureStream,
  };
  r.worker_apis = await S(() => new Promise(res => {
    const src = "postMessage({MediaStreamTrackProcessor: typeof MediaStreamTrackProcessor," +
                " VideoTrackGenerator: typeof VideoTrackGenerator, VideoEncoder: typeof VideoEncoder," +
                " AudioEncoder: typeof AudioEncoder, SharedArrayBuffer: typeof SharedArrayBuffer})";
    const w = new Worker(URL.createObjectURL(new Blob([src], {type: "text/javascript"})));
    w.onmessage = e => res(e.data);
    w.onerror = e => res("worker error: " + e.message);
    setTimeout(() => res("worker timeout"), 5000);
  }));
  r.audiocontext_16k = await S(async () => {
    const a = new AudioContext({sampleRate: 16000}); const v = a.sampleRate; a.close(); return v; });
  return r;
}

async function camera() {
  const r = {};
  let stream;
  try {
    stream = await within(navigator.mediaDevices.getUserMedia({video: true}), 15000, "getUserMedia");
  } catch (e) {
    r.error = "getUserMedia " + (e.name || "") + ": " + (e.message || e);
    return r;
  }
  const track = stream.getVideoTracks()[0];
  // WHICH camera matters: this laptop has "Integrated IR Camera" (Windows
  // Hello infrared) as well as "Integrated Camera". An IR sensor gives a dark
  // picture, and a browser that picks it by default shows a black preview.
  r.opened_camera = track.label;
  r.video_inputs = await S(async () => (await navigator.mediaDevices.enumerateDevices())
    .filter(d => d.kind === "videoinput").map(d => d.label).join(" | "));
  const set = Object.assign({}, track.getSettings());
  delete set.deviceId; delete set.groupId;
  r.settings = set;
  r.track_state = track.readyState;

  const v = document.createElement("video");
  v.muted = true; v.playsInline = true; v.srcObject = stream;
  document.body.appendChild(v);
  try { await within(v.play(), 5000, "video.play"); } catch (e) { r.play_error = String(e); }
  let frames = 0;
  if (v.requestVideoFrameCallback) {
    const cb = () => { frames++; v.requestVideoFrameCallback(cb); };
    v.requestVideoFrameCallback(cb);
  }

  // The real camera through a local WebRTC loop: does it encode and decode?
  const pc1 = new RTCPeerConnection(), pc2 = new RTCPeerConnection();
  pc1.onicecandidate = e => { if (e.candidate) pc2.addIceCandidate(e.candidate).catch(() => {}); };
  pc2.onicecandidate = e => { if (e.candidate) pc1.addIceCandidate(e.candidate).catch(() => {}); };
  pc1.addTrack(track, stream);
  try {
    await pc1.setLocalDescription();
    await pc2.setRemoteDescription(pc1.localDescription);
    await pc2.setLocalDescription();
    await pc1.setRemoteDescription(pc2.localDescription);
  } catch (e) { r.negotiate_error = String(e); }

  const cv = document.createElement("canvas"); cv.width = 64; cv.height = 48;
  const cx = cv.getContext("2d", {willReadFrequently: true});
  const luma = [];
  for (let i = 0; i < 20; i++) {
    await sleep(250);
    try {
      cx.drawImage(v, 0, 0, 64, 48);
      const d = cx.getImageData(0, 0, 64, 48).data;
      let s = 0;
      for (let j = 0; j < d.length; j += 4) s += 0.299 * d[j] + 0.587 * d[j + 1] + 0.114 * d[j + 2];
      luma.push(Math.round(s / (d.length / 4)));
    } catch (e) { r.canvas_error = String(e); }
  }
  r.video_element = {width: v.videoWidth, height: v.videoHeight,
                     frame_callbacks: frames, luma_samples: luma};
  const st1 = await pc1.getStats(), st2 = await pc2.getStats();
  const mimes = {};
  st1.forEach(s => { if (s.type === "codec") mimes[s.id] = s.mimeType; });
  st1.forEach(s => { if (s.type === "outbound-rtp" && s.kind === "video")
    r.loop_outbound = {framesEncoded: s.framesEncoded, packets: s.packetsSent,
                       encoder: s.encoderImplementation || "n/a", codec: mimes[s.codecId] || "?"}; });
  st2.forEach(s => { if (s.type === "inbound-rtp" && s.kind === "video")
    r.loop_inbound = {framesDecoded: s.framesDecoded, packets: s.packetsReceived,
                      decoder: s.decoderImplementation || "n/a"}; });
  r.loop_ice = pc1.iceConnectionState;
  pc1.close(); pc2.close();
  track.stop();
  return r;
}

async function run() {
  try { out.codecs = await codecs(); } catch (e) { out.codecs_error = String(e); }
  if (location.search.includes("camera=1")) {
    try { out.camera = await camera(); } catch (e) { out.camera_error = String(e); }
  }
  await fetch("/result", {method: "POST", headers: {"Content-Type": "application/json"},
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

        def _isolation_headers(self):
            # WhatsApp Web asks for cross-origin isolation; so does this page,
            # so SharedArrayBuffer availability is compared like for like.
            self.send_header("Cross-Origin-Opener-Policy", "same-origin")
            self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
            self.send_header("Cache-Control", "no-store")

        def do_GET(self):
            if self.path.split("?")[0] not in ("/", "/index.html"):
                self.send_response(404)
                self.end_headers()
                return
            body = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._isolation_headers()
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
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


def stop_run(proc, image, marker):
    """Stop the launched process tree, then anything still naming our profile."""
    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                   capture_output=True, text=True)
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='%s'\" | "
          "Where-Object { $_.CommandLine -like '*%s*' } | "
          "Select-Object -ExpandProperty ProcessId" % (image, marker))
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=60)
        for pid in (r.stdout or "").split():
            if pid.strip().isdigit():
                subprocess.run(["taskkill", "/PID", pid.strip(), "/T", "/F"],
                               capture_output=True, text=True)
    except Exception:
        pass


def parse_pref(text):
    """name=value -> (name, python value), for --gorilla-pref experiments."""
    name, _, raw = text.partition("=")
    raw = raw.strip()
    if raw.lower() in ("true", "false"):
        return name.strip(), raw.lower() == "true"
    try:
        return name.strip(), int(raw)
    except ValueError:
        return name.strip(), raw


def run_one(name, exe, profile, use_camera, timeout, extra_prefs=None):
    srv, st = serve(PAGE)
    url = "http://127.0.0.1:%d/%s" % (srv.server_address[1],
                                      "?camera=1" if use_camera else "")
    if name == "gorilla":
        prefs = dict(wst.USER_JS)
        prefs["media.navigator.streams.fake"] = False      # the REAL camera
        prefs["media.navigator.permission.disabled"] = True
        # Experiments: test a pref change in a throwaway profile before anyone
        # rebuilds on a theory.
        prefs.update(dict(extra_prefs or []))
        (profile / "user.js").write_text(
            "".join("user_pref(%s, %s);\n" % (json.dumps(k), json.dumps(v))
                    for k, v in prefs.items()), encoding="utf-8")
        cmd = [str(exe), "--headless", "--wait-for-browser", "-no-remote",
               "-profile", str(profile), url]
        image = "firefox.exe"
    else:
        cmd = [str(exe), "--headless=new", "--user-data-dir=%s" % profile,
               "--no-first-run", "--no-default-browser-check",
               "--use-fake-ui-for-media-stream", "--proxy-server=http://127.0.0.1:9",
               "--disable-background-networking", "--disable-component-update",
               "--disable-sync", url]
        image = "msedge.exe"
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("  %-8s started (pid %d), waiting up to %ds..." % (name, proc.pid, timeout))
    got = st["event"].wait(timeout)
    stop_run(proc, image, profile.name)
    srv.shutdown()
    print("  %-8s %s in %.0fs" % (name, "reported" if got else "NO REPORT", time.time() - t0))
    return st["result"] if got else {"error": "no report within %ds" % timeout}


def flatten(d, prefix=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flatten(v, "%s%s." % (prefix, k)))
    else:
        out[prefix[:-1]] = d
    return out


def verdict_lines(res):
    """Plain-language reading of the camera results, per browser."""
    lines = []
    for name, r in res.items():
        cam = (r or {}).get("camera")
        if not cam:
            continue
        if cam.get("error"):
            lines.append("%s: camera did not open - %s" % (name, cam["error"]))
            continue
        ve = cam.get("video_element") or {}
        luma = ve.get("luma_samples") or []
        bright = [x for x in luma if x > 8]
        enc = (cam.get("loop_outbound") or {}).get("framesEncoded")
        dec = (cam.get("loop_inbound") or {}).get("framesDecoded")
        lines.append("%s: %dx%d, %s frame callbacks, %d/%d samples not black, "
                     "loop encoded %s / decoded %s frames"
                     % (name, ve.get("width", 0), ve.get("height", 0),
                        ve.get("frame_callbacks"), len(bright), len(luma), enc, dec))
    return lines


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--yes", action="store_true",
                    help="skip the confirmation (only once the user has agreed)")
    ap.add_argument("--no-camera", action="store_true")
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--only", choices=("gorilla", "edge"), default=None,
                    help="run one browser only")
    ap.add_argument("--gorilla-pref", action="append", default=[], metavar="NAME=VALUE",
                    help="set a pref in Gorilla's throwaway profile (repeatable) - "
                         "tests a fix before anyone rebuilds on a theory")
    args = ap.parse_args()
    extra = [parse_pref(p) for p in args.gorilla_pref]

    gorilla = vab.find_install()
    edge = next((p for p in EDGE_CANDIDATES if p.is_file()), None)
    if not gorilla or not edge:
        print("need both browsers: gorilla=%s edge=%s" % (gorilla, edge))
        return 2

    print(NOTICE % ("NOT used" if args.no_camera else
                    "opened for about 5 seconds in each browser, one at a time"))
    if not args.yes:
        if not sys.stdin.isatty():
            print("refusing: no terminal to confirm in. Pass --yes only after the "
                  "user has agreed.")
            return 2
        if input("Run it? [y/N] ").strip().lower() not in ("y", "yes"):
            print("not run")
            return 1

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    res = {}
    if extra:
        print("  gorilla test prefs: %s" % ", ".join("%s=%s" % kv for kv in extra))
    for name, exe in (("gorilla", gorilla / "firefox.exe"), ("edge", edge)):
        if args.only and name != args.only:
            continue
        profile = ROOT / "state" / ("compare-profile-%s-%s" % (name, stamp))
        profile.mkdir(parents=True)
        try:
            res[name] = run_one(name, exe, profile, not args.no_camera, args.timeout,
                                extra if name == "gorilla" else None)
        finally:
            time.sleep(2)
            shutil.rmtree(profile, ignore_errors=True)

    fg, fe = flatten(res.get("gorilla") or {}), flatten(res.get("edge") or {})
    keys = sorted(set(fg) | set(fe), key=lambda k: (k.split(".")[0], k))
    print("")
    print("%-52s %-22s %-22s" % ("", "GORILLA", "EDGE"))
    for k in keys:
        if k == "ua":
            continue
        a, b = fg.get(k, "-"), fe.get(k, "-")
        sa = json.dumps(a) if not isinstance(a, str) else a
        sb = json.dumps(b) if not isinstance(b, str) else b
        mark = "  <<" if sa != sb and not k.endswith("luma_samples") else ""
        print("%-52s %-22s %-22s%s" % (k[:52], sa[:22], sb[:22], mark))
    print("")
    for line in verdict_lines(res):
        print("  " + line)

    out = ROOT / "state" / ("media_compare%s.json" % ("_experiment" if extra else ""))
    out.write_text(json.dumps({
        "when": datetime.datetime.now().isoformat(timespec="seconds"),
        "gorilla_build_id": vab.build_id(gorilla),
        "edge": str(edge),
        "camera": not args.no_camera,
        "gorilla_test_prefs": dict(extra),
        "results": res,
    }, indent=2) + "\n", encoding="utf-8")
    print("")
    print("recorded: %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
