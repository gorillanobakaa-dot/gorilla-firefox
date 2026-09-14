"""Read a Firefox MOZ_LOG capture of a WebRTC call and name the layer that failed.

WHY THIS EXISTS
  A Windows release of this build said "WhatsApp and WebRTC calls now work".
  What had actually been verified was that
  media.peerconnection.dtls.version.max = 771 sat inside the installed
  omni.ja. No call had been placed, and calls did not work. With nothing but
  "it doesn't connect" to go on, the browser, the network and WhatsApp could
  not be told apart.

  A pref in a file is evidence about a file. A call connecting is evidence
  about a browser. This reads the second kind.

TWO LOGGING TRAPS IN FIREFOX 155, CHECKED AGAINST THE SOURCE
  1. "Wrote 28 bytes to SSL Layer" is logged at ML_DEBUG, and
     dom/media/webrtc/transport/logging.h maps ML_DEBUG to LogLevel::Verbose.
     A capture with mtransport at 4 never writes that line - so "no long runs
     of 28-byte writes" passes on the very blackhole it is meant to catch.
     Capture mtransport at 5. This tool refuses to call a below-5 capture with
     no open data channel healthy: it says "unverified".

  2. "Setting DTLS1.3 supported_versions workaround" is written only on the
     DTLS CLIENT path (transportlayerdtls.cpp:489-506). A DTLS server never
     writes it, whatever the cap. Its absence proves the cap only when
     "Setting up DTLS as client" is present too.

WHAT REAL CAPTURES TAUGHT IT
  - An early version said HEALTHY about a call that never connected, because
    2 of 11 PeerConnections came up. Every leg is now counted.
  - All the failed legs had been offered only IPv6 relays, on a network with
    no IPv6, so the tool blamed that. It was WRONG as a cause: a call that
    worked had IPv6-only legs failing too. The difference was elsewhere -
    WhatsApp's page had its workers queued by dom.workers.maxPerDomain = 8
    (upstream 512), at the moment the call started. With the limit at 512: no
    worker queued, 793 data-channel messages within 21 seconds, against 11-12
    in the failed calls.

  So a leg's failure is not the verdict; whether the call's data FLOWED is.
  Failed legs are reported, but they only fail the call when nothing flowed.
  And the page's own warnings - where the cause actually was - are summarised
  under PAGE, because they were the last place anyone looked.

THE LADDER - the first layer that failed, in the order a call is built
    capture       no log at all
    signaling     no PeerConnection gathered candidates or changed ICE state
    gathering     PeerConnections exist but produced no local candidates
    ICE           candidates exchanged, no connectivity check succeeded
    DTLS          ICE connected, no handshake completed
    DTLS cap      Firefox offered DTLS 1.3: the 771 cap is not in effect
    SCTP          handshakes done, no data channel opened, SCTP INITs unanswered
                  (the DTLS 1.3 blackhole signature)
    unverified    handshakes done, no data channel, and the capture was below
                  mtransport:5 - the SCTP layer cannot be judged from it
    worker limit  data never flowed and the page had workers QUEUED by the
                  per-site worker limit (dom.workers.maxPerDomain)
    IPv6 relays   data never flowed; the legs that failed were offered only
                  IPv6 relay addresses and this machine has no IPv6
    partial       data never flowed; some legs connected, others failed ICE
    healthy       the call's data flowed. Failed side legs are noted, not fatal

  Regression test: test_analyze_call_log.py

USAGE
    python analyze_call_log.py <capture-dir>
    python analyze_call_log.py <dir-or-file> --json out.json
"""
import argparse
import collections
import json
import re
import sys
import textwrap
from pathlib import Path

# The integers PeerConnectionImpl.cpp logs are WebIDL enum positions, in
# declaration order (dom/webidl/RTCIceTransport.webidl). "closed" is 0, not
# "new" - reading them in the spec's prose order gets every state wrong.
ICE_STATES = ["closed", "failed", "disconnected", "new", "checking",
              "completed", "connected"]
GATHER_STATES = ["new", "gathering", "complete"]

# Data-channel messages received that mean the call really carried data.
# Measured 2026-09-14: failed WhatsApp calls 11 and 12 in two minutes; the
# working calls 793 in 21 seconds and 620 in about a minute.
MEDIA_FLOW_MESSAGES = 100

RX_WRITE = re.compile(r"Wrote (\d+) bytes to SSL Layer")
RX_ICE = re.compile(r"IceConnectionStateChange: (\S+) (\d+) \(((?:0x)?[0-9A-Fa-f]+)\)")
RX_GATHER = re.compile(r"IceGatheringStateChange: (\S+) (\d+)")
RX_TYP = re.compile(r" typ (\w+)")
RX_CHECKS = re.compile(r"all checks completed success=(\d+) fail=(\d+)")
RX_PAIR = re.compile(r"setting pair to state (\w+)")
# One PeerConnection per uuid in the socket process's mtransport lines.
RX_PC = re.compile(r"PC:\{([0-9a-fA-F-]{36})\}")
RX_CAND_ADDR = re.compile(r"candidate:\S+ \d+ (?:udp|tcp|UDP|TCP) \d+ (\S+) \d+ typ (\w+)")
# nsConsoleService -> MOZ_LOG "PageMessages" carries the browser's own chrome
# errors as well as the web page's. These are the browser's, not the page's.
CHROME_NOISE = re.compile(r"resource://|chrome://|moz-src://|\.ftl\b|"
                          r"Attempt to override an existing")

# Plain substring tests. A two-minute call at mtransport:5 is hundreds of
# thousands of lines; they must not each go through a dozen regexes.
#   needle                                              counter
SIMPLE = [
    ("Setting up DTLS as client",                       "dtls_client"),
    ("Setting up DTLS as server",                       "dtls_server"),
    ("Setting DTLS1.3 supported_versions workaround",   "dtls13_offered"),
    ("SSL handshake completed",                         "handshakes"),
    ("Calling AnnounceOpen on RTCDataChannel",          "dc_open"),
    ("OnSctpPacketReceived",                            "sctp_rx"),
    ("SendPacketWithStatus",                            "sctp_tx"),
    ("OnMessageReceived",                               "dc_messages_in"),
    ("Worker could not be started immediately",         "worker_queued"),
    ("nominated candidate pairs",                       "nominated"),
    ("Consent refresh failed",                          "consent_failed"),
    ("nr_turn_allocated_cb failed",                     "turn_failed"),
    ("Blocking local UDP candidate",                    "blocked_local"),
    ("Blocking remote UDP candidate",                   "blocked_remote"),
    ("Could not get init stream",                       "audio_errors"),
    ("Invalid combination of input processing params",  "audio_errors"),
    ("/mtransport",                                     "mtransport_lines"),
    ("/signaling",                                      "signaling_lines"),
    ("/DataChannel",                                    "datachannel_lines"),
]
NO_SAMPLE = {"mtransport_lines", "signaling_lines", "datachannel_lines",
             "sctp_rx", "sctp_tx", "dc_messages_in"}


def log_files(path):
    p = Path(path)
    if p.is_file():
        return [p]
    if not p.is_dir():
        return []
    return sorted(f for f in p.rglob("*")
                  if f.is_file() and ("moz_log" in f.name or f.suffix == ".log"))


def family(addr):
    return "v6" if ":" in addr else "v4"


def analyze(path):
    files = log_files(path)
    c = collections.Counter()
    writes = collections.Counter()
    local_types = collections.Counter()
    remote_types = collections.Counter()
    pairs = collections.Counter()
    page = collections.Counter()
    ice = collections.defaultdict(list)
    pc_remote = collections.defaultdict(set)     # PC uuid -> {"v4", "v6"}
    pc_checks = {}                                # PC uuid -> [best success, last fail]
    local_families = set()
    checks, samples, per_file = [], {}, []
    gather_complete, total = 0, 0

    for f in files:
        size = f.stat().st_size
        total += size
        n = 0
        with open(f, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                n += 1
                for needle, key in SIMPLE:
                    if needle in line:
                        c[key] += 1
                        if key not in samples and key not in NO_SAMPLE:
                            samples[key] = line.strip()[:240]
                # The web page's own warnings and errors. On 2026-09-14 the cause
                # of the broken calls was in here and nowhere else. Browser-chrome
                # noise (chrome://, resource://, .ftl) is left out.
                # Filtered on the WHOLE line: messages quote their own subject
                # ("sidebar-resize-splitter") so a quote-delimited parse of the
                # text or the {file: ...} part breaks, and the first version
                # ranked the browser's own .ftl and GenAI noise above the
                # worker warning that was the real cause.
                if ("E/PageMessages [JavaScript " in line
                        or "W/PageMessages [JavaScript " in line) and not CHROME_NOISE.search(line):
                    body = line.split("PageMessages [JavaScript ", 1)[1]
                    kind, _, text = body.partition(": ")
                    text = text.lstrip('"')
                    cut = text.find('" {file:')
                    text = text[:cut] if cut >= 0 else text.rstrip().rstrip("]").rstrip('"')
                    page[("%s: %s" % (kind, re.sub(r"\d{2,}", "N", text)))[:180]] += 1
                # Cipher-suite lines are ML_DEBUG (Verbose) and written on every
                # DTLS setup, so they show whether the capture reached level 5
                # without depending on the log line's level letter.
                if "Enabling: " in line and "mtransport" in line:
                    c["mtransport_verbose"] += 1
                if "bytes to SSL Layer" in line:
                    m = RX_WRITE.search(line)
                    if m:
                        writes[int(m.group(1))] += 1
                elif "IceConnectionStateChange:" in line:
                    m = RX_ICE.search(line)
                    if m:
                        st = int(m.group(2))
                        name = ICE_STATES[st] if 0 <= st < len(ICE_STATES) else str(st)
                        ice[m.group(3)].append(name)
                        c["ice_state"] += 1
                elif "IceGatheringStateChange:" in line:
                    m = RX_GATHER.search(line)
                    if m:
                        c["gather_state"] += 1
                        if m.group(2) == "2":
                            gather_complete += 1
                elif "Passing local candidate to content:" in line:
                    m = RX_TYP.search(line)
                    if m:
                        local_types[m.group(1)] += 1
                    a = RX_CAND_ADDR.search(line)
                    if a:
                        local_families.add(family(a.group(1)))
                elif "AddIceCandidate:" in line:
                    m = RX_TYP.search(line)
                    if m:
                        remote_types[m.group(1)] += 1
                elif "all checks completed" in line:
                    m = RX_CHECKS.search(line)
                    if m:
                        s, fl = int(m.group(1)), int(m.group(2))
                        checks.append([s, fl])
                        p = RX_PC.search(line)
                        if p:
                            prev = pc_checks.get(p.group(1), [0, 0])
                            pc_checks[p.group(1)] = [max(prev[0], s), fl]
                elif "setting pair to state" in line:
                    m = RX_PAIR.search(line)
                    if m:
                        pairs[m.group(1)] += 1
                elif "parsing" in line and "candidate:" in line:
                    a = RX_CAND_ADDR.search(line)
                    p = RX_PC.search(line)
                    if a and p:
                        pc_remote[p.group(1)].add(family(a.group(1)))
        per_file.append({"name": f.name, "bytes": size, "lines": n})

    c["mtransport_verbose"] += sum(writes.values())
    connected = sorted(k for k, v in pc_checks.items() if v[0] > 0)
    failed = sorted(k for k, v in pc_checks.items() if v[0] == 0)
    v6only = [k for k in failed if pc_remote.get(k) == {"v6"}]

    r = {
        "path": str(path),
        "files": per_file,
        "bytes": total,
        "counts": dict(c),
        "ssl_writes_by_size": {str(k): v for k, v in sorted(writes.items())},
        "local_candidate_types": dict(local_types),
        "remote_candidate_types": dict(remote_types),
        "pair_states": dict(pairs),
        "ice_states_by_pc": dict(ice),
        "gathering_complete": gather_complete,
        "checks_completed": checks,
        "legs": {
            "connected": len(connected),
            "failed": len(failed),
            "failed_ipv6_only": len(v6only),
            "local_families": sorted(local_families),
            "remote_families_by_leg": {k[:8]: sorted(v) for k, v in pc_remote.items()},
        },
        "data_flowed": c["dc_messages_in"] >= MEDIA_FLOW_MESSAGES,
        "page_problems": [[n, t] for t, n in page.most_common(8)],
        "samples": samples,
    }
    r["ice_up"] = bool(
        connected
        or any(s in ("connected", "completed") for v in ice.values() for s in v)
        or pairs.get("SUCCEEDED", 0) > 0 or c["nominated"] > 0)
    r["dtls_cap"] = cap_evidence(c)
    r["layer"], r["detail"] = ladder(r)
    r["passed"] = r["layer"] == "healthy"
    return r


def cap_evidence(c):
    if c["dtls13_offered"]:
        return ("NOT IN EFFECT - %d DTLS client setup(s) offered 1.3"
                % c["dtls13_offered"])
    if c["dtls_client"]:
        return ("PROVEN live - %d DTLS client setup(s), none offered 1.3"
                % c["dtls_client"])
    if c["dtls_server"]:
        return ("unprovable from this log - Firefox was the DTLS server on all %d "
                "connection(s), and only a client writes the 1.3 offer"
                % c["dtls_server"])
    if not c["mtransport_lines"]:
        return ("no mtransport lines at all - logged below level 4, or the "
                "socket process wrote no log file")
    return "no DTLS setup logged"


def fmt(counter):
    return ", ".join("%s %d" % (k, v) for k, v in sorted(counter.items())) or "none"


def ladder(r):
    c = collections.Counter(r["counts"])
    legs = r["legs"]
    if not r["files"] or r["bytes"] == 0:
        return "capture", (
            "No log was written. MOZ_LOG only reaches a browser started AFTER it "
            "is set; if a window was already open, the launch just handed over to "
            "it.")
    local = sum(r["local_candidate_types"].values())
    if c["ice_state"] == 0 and c["gather_state"] == 0 and local == 0:
        return "signaling", (
            "No PeerConnection gathered candidates or changed ICE state. The call "
            "never reached WebRTC: the page did not start one, or microphone or "
            "camera access stopped it first. Read the PAGE lines.")
    if not r["ice_up"]:
        if local == 0:
            return "gathering", (
                "PeerConnections were created but produced no local ICE candidates "
                "(%d blocked). No usable network interface, or every candidate was "
                "filtered out." % c["blocked_local"])
        remote = r["remote_candidate_types"]
        extra = ""
        if legs["failed_ipv6_only"] and "v6" not in legs["local_families"]:
            extra += ("; %d leg(s) were offered only IPv6 addresses and this machine "
                      "has no IPv6" % legs["failed_ipv6_only"])
        if c["turn_failed"]:
            extra += "; %d TURN allocation failure(s)" % c["turn_failed"]
        if c["consent_failed"]:
            extra += "; consent lost %d time(s)" % c["consent_failed"]
        return "ICE", (
            "Candidates were exchanged but no connectivity check ever succeeded. "
            "Local: %s. Remote: %s. Pair states: %s%s. Usual cause: no path between "
            "the two sides - carrier-grade NAT (common on mobile data) without a working "
            "TURN relay, or UDP blocked on the network."
            % (fmt(r["local_candidate_types"]),
               fmt(remote) if remote else "none trickled (may be inside the SDP)",
               fmt(r["pair_states"]), extra))
    if c["handshakes"] == 0:
        return "DTLS", (
            "ICE connected but no DTLS handshake completed (%d client / %d server "
            "setups)." % (c["dtls_client"], c["dtls_server"]))
    if c["dtls13_offered"]:
        return "DTLS cap", (
            "Firefox offered DTLS 1.3 on %d client setup(s). The 771 cap is NOT in "
            "effect in the running browser, whatever omni.ja says - check "
            "about:config, and the profile's user.js and prefs.js."
            % c["dtls13_offered"])
    init28 = int(r["ssl_writes_by_size"].get("28", 0))
    if c["dc_open"] == 0 and init28 >= 20:
        return "SCTP", (
            "%d DTLS handshake(s) completed, then %d 28-byte SCTP INIT writes and "
            "not one data channel opened. This is the 2026-08-26 Linux blackhole "
            "signature: the tunnel is up and carries nothing."
            % (c["handshakes"], init28))
    if c["dc_open"] == 0 and not c["mtransport_verbose"]:
        return "unverified", (
            "%d DTLS handshake(s) completed but no data channel opened, and "
            "mtransport was not captured at level 5 - so the SCTP INIT writes that "
            "would reveal a blackhole are invisible. Capture again at mtransport:5 "
            "(capture_call_log.py does)." % c["handshakes"])
    if not r["data_flowed"]:
        if c["worker_queued"]:
            return "worker limit", (
                "The connections came up but the call's data never flowed (%d "
                "data-channel messages in), and the page had %d worker(s) QUEUED by "
                "the per-site worker limit. The call engine waits for a worker that "
                "never starts. Check dom.workers.maxPerDomain - Gorilla shipped 8, "
                "upstream is 512 - and raise it; confirmed as the cause on "
                "2026-09-14." % (c["dc_messages_in"], c["worker_queued"]))
        if legs["failed"]:
            if legs["failed_ipv6_only"] and "v6" not in legs["local_families"]:
                return "IPv6 relays", (
                    "The call's data never flowed (%d data-channel messages in). %d "
                    "leg(s) connected; the %d that failed were offered only IPv6 relay "
                    "addresses and this machine has no IPv6. That is NOT proven to be "
                    "the cause - on 2026-09-14 a working call had the same failed "
                    "legs. Read the PAGE lines first."
                    % (c["dc_messages_in"], legs["connected"], legs["failed"]))
            return "partial", (
                "The call's data never flowed; %d leg(s) connected and %d failed ICE. "
                "Read the PAGE lines." % (legs["connected"], legs["failed"]))
    note = "" if c["dc_open"] else (
        " No data channel opened - fine if the page does not use one.")
    if legs["failed"]:
        note += (" %d side leg(s) failed ICE%s - harmless here, the call's data "
                 "flowed." % (legs["failed"], " (IPv6-only relays)"
                              if legs["failed"] == legs["failed_ipv6_only"] else ""))
    return "healthy", (
        "%d DTLS handshake(s), %d data channel(s) opened, %d data-channel messages "
        "in.%s If there was still no sound or picture, the fault is in media "
        "(devices, codecs) or at the far end, not in this machine's network path."
        % (c["handshakes"], c["dc_open"], c["dc_messages_in"], note))


def render(r):
    c = collections.Counter(r["counts"])
    legs = r["legs"]
    out = ["log files: %d, %.1f MB   (%s)" % (len(r["files"]), r["bytes"] / 1e6,
                                               r["path"])]
    for f in r["files"]:
        if f["bytes"]:
            out.append("   %-52s %9.1f KB %9d lines" % (f["name"][:52], f["bytes"] / 1e3,
                                                       f["lines"]))
    out.append("")
    out.append("LEGS      %d connected, %d failed ICE (%d offered IPv6 only); "
               "local address families: %s"
               % (legs["connected"], legs["failed"], legs["failed_ipv6_only"],
                  "/".join(legs["local_families"]) or "?"))
    out.append("ICE       local %s" % fmt(r["local_candidate_types"]))
    out.append("          remote %s" % fmt(r["remote_candidate_types"]))
    out.append("          pairs %s" % fmt(r["pair_states"]))
    out.append("DTLS      %d handshake(s), %d client / %d server setup(s)"
               % (c["handshakes"], c["dtls_client"], c["dtls_server"]))
    out.append("DTLS cap  %s" % r["dtls_cap"])
    out.append("SCTP      %d data channel(s) opened, %d packets in / %d out, "
               "%s 28-byte write(s)%s"
               % (c["dc_open"], c["sctp_rx"], c["sctp_tx"],
                  r["ssl_writes_by_size"].get("28", 0),
                  "" if c["mtransport_verbose"] else
                  "  (capture below mtransport:5 - INIT writes not visible)"))
    out.append("DATA      %d data-channel messages in (flowing needs %d)   "
               "workers queued by the per-site limit: %d"
               % (c["dc_messages_in"], MEDIA_FLOW_MESSAGES, c["worker_queued"]))
    if c["audio_errors"]:
        out.append("AUDIO     %d audio stream error(s): %s"
                   % (c["audio_errors"], r["samples"].get("audio_errors", "")))
    if r.get("page_problems"):
        out.append("PAGE      what the web pages themselves reported, most frequent first:")
        for n, t in r["page_problems"]:
            out.append("          %4dx %s" % (n, t[:110]))
    out.append("")
    out.append("LAYER     %s" % r["layer"].upper())
    for line in textwrap.wrap(r["detail"], 66):
        out.append("          %s" % line)
    return out


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="a capture directory or a single .moz_log file")
    ap.add_argument("--json", default=None, help="also write the full analysis here")
    args = ap.parse_args()
    r = analyze(args.path)
    print("\n".join(render(r)))
    if args.json:
        Path(args.json).write_text(json.dumps(r, indent=2) + "\n", encoding="utf-8")
    if r["layer"] == "capture":
        return 2
    return 0 if r["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
