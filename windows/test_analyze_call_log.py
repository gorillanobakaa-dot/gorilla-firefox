"""Regression test for analyze_call_log.py - every rung of the ladder.

WHY
  The analyzer decides which layer of a call failed. If it misreads a log, the
  next session chases the wrong layer with complete confidence - the exact
  failure this tool family exists to stop.

  Every fixture line below uses the log strings as they appear in the Firefox
  155 source (file and line cited in analyze_call_log.py). Five cases are traps
  found along the way:
    - a DTLS server never writes the 1.3 line, so its absence proves nothing
    - ICE state integers are WebIDL positions: 0 is "closed", not "new"
    - below mtransport:5 the SCTP blackhole is invisible, so "no data channel
      and no errors" must not read as healthy
    - 2026-09-14, first real capture: the analyzer said HEALTHY about a call
      that never connected, because two of eleven legs came up. A failed leg
      must be reported whatever else worked
    - the legs that failed had been offered only IPv6 relays on a machine with
      no IPv6 - a different conclusion from "ICE failed", so a different rung

USAGE
    python "working scripts/test_analyze_call_log.py"
"""
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_call_log as acl      # noqa: E402

PARENT = "2026-09-14 10:00:00.000000 UTC - [Parent 1111: Main Thread]: "
SOCKET = "2026-09-14 10:00:00.000000 UTC - [Socket 4242: Socket Thread]: "


def sig(msg):
    return PARENT + "D/signaling [main|PeerConnectionImpl] PeerConnectionImpl.cpp:1: " + msg


def mt(level, msg):
    return SOCKET + level + "/mtransport " + msg


LOCAL = sig("Passing local candidate to content: candidate:0 1 UDP 2122252543 "
            "172.22.82.10 50000 typ host")
LOCAL_SRFLX = sig("Passing local candidate to content: candidate:1 1 UDP 1686052863 "
                  "100.64.1.2 50000 typ srflx raddr 172.22.82.10 rport 50000")
REMOTE_RELAY = sig("AddIceCandidate: candidate:2 1 UDP 41885439 57.144.63.57 3478 "
                   "typ relay raddr 0.0.0.0 rport 0 abcd")
GATHER_DONE = sig("IceGatheringStateChange: transport_0 2 (000001F2A3B4C5D6)")


def ice(n):
    return sig("IceConnectionStateChange: transport_0 %d (000001F2A3B4C5D6)" % n)


def leg(uuid, remote_addr, success):
    """One PeerConnection as the socket process logs it: a trickled remote
    candidate, then its ICE verdict (ice_media_stream / ice_peer_ctx)."""
    pc = "PC:{%s} 1789375340803000 (id=17179869185 url=https://web.whatsapp.com/)" % uuid
    return [
        mt("I", "NrIceCtx(%s)/STREAM(%s transport-id=transport_0) : parsing trickle "
                "candidate candidate:2 1 udp 2122262783 %s 3478 typ host generation 0"
           % (pc, pc, remote_addr)),
        mt("D", "(ice/INFO) ICE-PEER(%s:default): all checks completed success=%d fail=%d"
           % (pc, success, 0 if success else 1)),
    ]


PAIR_OK = mt("D", "ICE-PEER(PC:1)/CAND-PAIR(x): setting pair to state SUCCEEDED: x")
PAIR_FAIL = mt("D", "ICE-PEER(PC:1)/CAND-PAIR(x): setting pair to state FAILED: x")
CLIENT = mt("D", "Setting up DTLS as client")
SERVER = mt("D", "Setting up DTLS as server")
DTLS13 = mt("D", "Setting DTLS1.3 supported_versions workaround")
CIPHER = mt("V", "Flow[x:1]; Layer[dtls]: Enabling: 49195")
HANDSHAKE = mt("I", "Flow[x:1]; Layer[dtls]: ****** SSL handshake completed ******")
WRITE28 = mt("V", "Flow[x:1]; Layer[dtls]: Wrote 28 bytes to SSL Layer")
OPEN = PARENT + "I/DataChannel Calling AnnounceOpen on RTCDataChannel."
MSG = PARENT + "V/DataChannel 1c6e3fd2f00: OnMessageReceived channel 1c6911d8340, binary"
WORKERQ = (PARENT + 'W/PageMessages [JavaScript Warning: "A Worker could not be started '
           'immediately because other documents in the same origin are already using '
           'the maximum number of workers. The Worker is now queued"]')

CONNECTED = [LOCAL, GATHER_DONE, ice(4), PAIR_OK, ice(6)]
WORKING = CONNECTED + [CLIENT, CIPHER, HANDSHAKE, WRITE28, OPEN]
V4_OK = leg("4288336b-30e6-472b-b795-a4563e7a4cd0", "157.240.225.133", 1)
V6_FAIL = leg("1eda7e37-32bc-4336-af1b-f3336fe5b9a5", "2a03:2880:f266:db:face:b00c:0:6749", 0)
V4_FAIL = leg("9f0b2644-ce72-4d7b-8709-26365d314a72", "31.13.64.1", 0)

#  name                                   lines                                    layer          cap prefix
CASES = [
    ("empty capture",                     None,                                    "capture",      None),
    ("page never started a call",         [PARENT + "D/MediaManager enumerate"],   "signaling",    None),
    ("ICE never connects",                [LOCAL, LOCAL_SRFLX, REMOTE_RELAY, GATHER_DONE,
                                           ice(4), PAIR_FAIL, PAIR_FAIL, ice(1)],   "ICE",          None),
    ("state 0 is closed, not connected",  [LOCAL, GATHER_DONE, ice(0)],            "ICE",          None),
    ("handshake never completes",         CONNECTED + [CLIENT, CIPHER],            "DTLS",         "PROVEN"),
    ("cap not in effect",                 CONNECTED + [CLIENT, DTLS13, CIPHER,
                                                       HANDSHAKE, OPEN],            "DTLS cap",     "NOT IN EFFECT"),
    ("linux blackhole signature",         CONNECTED + [CLIENT, CIPHER, HANDSHAKE]
                                          + [WRITE28] * 30,                        "SCTP",         "PROVEN"),
    ("below level 5 hides the blackhole", CONNECTED + [CLIENT, HANDSHAKE],         "unverified",   "PROVEN"),
    ("server-only: cap unprovable",       CONNECTED + [SERVER, HANDSHAKE, OPEN],   "healthy",      "unprovable"),
    ("healthy call",                      WORKING + [OPEN],                        "healthy",      "PROVEN"),
    ("one leg up is not a working call",  WORKING + V4_OK + V4_FAIL,               "partial",      "PROVEN"),
    ("IPv6-only relays, no local IPv6",   WORKING + V4_OK + V6_FAIL + V6_FAIL,     "IPv6 relays",  "PROVEN"),
    # 2026-09-14 10:12 vs 10:18: same failed IPv6 legs both times. What differed
    # was the worker queue, and whether data flowed.
    ("worker limit stalls the call",      WORKING + V4_OK + V6_FAIL + [WORKERQ],   "worker limit", "PROVEN"),
    ("IPv6 legs fail, call data flows",   WORKING + V4_OK + V6_FAIL + [MSG] * 120, "healthy",      "PROVEN"),
]


def main():
    tmp = Path(tempfile.mkdtemp(prefix="acl-test-"))
    failures = 0
    try:
        for i, (name, lines, want_layer, want_cap) in enumerate(CASES):
            d = tmp / ("case%02d" % i)
            d.mkdir()
            if lines is not None:
                (d / "call.log-main.1111.moz_log").write_text(
                    "\n".join(lines) + "\n", encoding="utf-8")
            r = acl.analyze(d)
            ok = (r["layer"] == want_layer
                  and (want_cap is None or r["dtls_cap"].startswith(want_cap)))
            print("  [%s] %-36s layer=%-11s cap=%s"
                  % ("PASS" if ok else "FAIL", name, r["layer"], r["dtls_cap"][:30]))
            if not ok:
                failures += 1
                print("         wanted layer=%s, cap starting %r" % (want_layer, want_cap))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("")
    print("%d/%d passed" % (len(CASES) - failures, len(CASES)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
