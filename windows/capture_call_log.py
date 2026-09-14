"""Record one real call in the installed browser, then say which layer failed.

WHY THIS EXISTS
  2026-09-13: "WhatsApp and WebRTC calls now work" was published without a
  call ever being placed on Windows. 2026-09-14: calls still failed, and there
  was nothing to tell the browser, the phone-hotspot network and WhatsApp
  apart.

  webrtc_selftest.py answers "does this browser's WebRTC work at all" with no
  one involved. It cannot answer "does a WhatsApp call work from here": that
  needs WhatsApp's relays, a real network and a second person. This makes that
  one call count. The browser starts with WebRTC logging, and when it is closed
  the log is read for you.

  It is the Linux handover's PART 6.3 turned into a tool, with the two
  Firefox 155 corrections described in analyze_call_log.py.

WHAT IT ASKS OF YOU
  1. close every Gorilla Unleashed window first. It refuses otherwise: MOZ_LOG
     never reaches a browser that is already running (handover trap 1)
  2. say yes
  3. place ONE short call. 30 seconds is enough; voice-only uses the least data
  4. close the browser completely
  5. answer two questions: did it connect, could you both hear each other

  Nothing is typed or clicked for you. The log stays on this machine.

USAGE
    python "working scripts/capture_call_log.py"
    python "working scripts/capture_call_log.py" --analyze state/call_logs/<stamp>
"""
import argparse
import csv
import datetime
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(os.environ.get("GORILLA_ROOT")
            or Path(__file__).resolve().parent.parent)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_call_log as acl      # noqa: E402
import verify_address_bar as vab    # noqa: E402  find_install(), build_id()

# mtransport at 5, not the handover's 4: Firefox 155 writes the SCTP INIT lines
# at Verbose. MediaManager and cubeb so a device or audio failure shows too.
#
# console and PageMessages: the WEB PAGE's own voice. 2026-09-14, two captures
# in a row: the relay legs came up, a dozen data-channel messages went back and
# forth, and then WhatsApp's page simply stopped progressing - a decision made
# in its JavaScript, invisible to every transport log. "console" is the MOZ_LOG
# module for console.* calls (dom/console/Console.cpp:915) and "PageMessages"
# receives everything sent to the console service, uncaught script errors
# included (xpcom/base/nsConsoleService.cpp:58). No pref, no stdout needed.
LOG_MODULES = ("timestamp,mtransport:5,signaling:4,DataChannel:5,MediaManager:4,"
               "cubeb:4,console:5,PageMessages:5")

BANNER = """
  ==================================================================
   THIS STARTS YOUR BROWSER WITH CALL LOGGING SWITCHED ON.

   It uses your normal profile, so WhatsApp stays logged in.
   Nothing is typed for you and nothing is clicked for you.

     1. it opens Gorilla Unleashed
     2. YOU place one short call - 30 seconds is plenty,
        and voice-only uses the least data
     3. YOU close the browser completely when the call ends
     4. it reads the log, says which layer failed, and asks
        you two questions

   The log stays on this machine, under state/call_logs/.
  ==================================================================
"""


def running_firefox():
    try:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq firefox.exe",
                            "/FO", "CSV", "/NH"],
                           capture_output=True, text=True, timeout=60)
    except Exception:
        return []
    return [row[1] for row in csv.reader(io.StringIO(r.stdout or ""))
            if len(row) >= 2 and row[0].lower() == "firefox.exe"]


def ask(question):
    try:
        return input(question).strip().lower() in ("y", "yes")
    except EOFError:
        return False


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--analyze", metavar="DIR", default=None,
                    help="only read an existing capture")
    ap.add_argument("--yes", action="store_true", help="skip the start confirmation")
    ap.add_argument("--install", default=None)
    args = ap.parse_args()

    if args.analyze:
        r = acl.analyze(args.analyze)
        print("\n".join(acl.render(r)))
        return 0 if r["passed"] else 1

    install = Path(args.install) if args.install else vab.find_install()
    if not install or not (install / "firefox.exe").is_file():
        print("no installed Gorilla Unleashed found")
        return 2

    pids = running_firefox()
    if pids:
        print("REFUSED: firefox.exe is still running (pid %s)." % ", ".join(pids))
        print("Close every Gorilla Unleashed window and check Task Manager shows no")
        print("firefox.exe, then run this again. A browser that is already running")
        print("never sees the logging switch, and the capture would be empty.")
        return 1

    print(BANNER)
    if not args.yes:
        if not sys.stdin.isatty():
            print("refusing: this needs a person to make the call - run it in a terminal.")
            return 2
        if not ask("Start the browser with call logging? [y/N] "):
            print("not started")
            return 1

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    logdir = ROOT / "state" / "call_logs" / stamp
    logdir.mkdir(parents=True)
    env = dict(os.environ)
    env["MOZ_LOG"] = LOG_MODULES
    env["MOZ_LOG_FILE"] = str(logdir / "call.log")

    t0 = time.time()
    proc = subprocess.Popen([str(install / "firefox.exe"), "--wait-for-browser"],
                            env=env)
    print("")
    print("Browser started. Make your call now.")
    print("When it is over, CLOSE THE BROWSER COMPLETELY. Waiting...")
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("")
        print("stopped waiting. Close the browser, then run:")
        print('   python "working scripts/capture_call_log.py" --analyze "%s"' % logdir)
        return 1
    for _ in range(30):
        if not running_firefox():
            break
        time.sleep(2)

    r = acl.analyze(logdir)
    print("")
    print("=" * 70)
    print("\n".join(acl.render(r)))
    print("=" * 70)

    connected = audio = None
    if sys.stdin.isatty():
        print("")
        connected = ask("Did the call connect - answered on both ends? [y/N] ")
        audio = ask("Could you BOTH hear each other? [y/N] ") if connected else False
        if connected and audio and not r["passed"]:
            print("")
            print("You say it worked but the log disagrees - keep this capture; the")
            print("analysis may be missing a pattern. Do not record it as a pass.")
        if r["passed"] and not audio:
            print("")
            print("The network path was healthy, so the fault is in media: the")
            print("microphone or speaker device, or a codec. Look at the AUDIO line")
            print("above and at cubeb / MediaManager lines in the log.")

    passed = bool(r["passed"] and connected and audio)
    record = {
        "passed": passed,
        "layer": r["layer"],
        "detail": r["detail"],
        "dtls_cap": r["dtls_cap"],
        "user_connected": connected,
        "user_audio_both_ways": audio,
        "build_id": vab.build_id(install),
        "install": str(install),
        "when": datetime.datetime.now().isoformat(timespec="seconds"),
        "minutes": round((time.time() - t0) / 60, 1),
        "log_dir": str(logdir),
        "counts": r["counts"],
        "local_candidate_types": r["local_candidate_types"],
        "remote_candidate_types": r["remote_candidate_types"],
        "pair_states": r["pair_states"],
    }
    out = ROOT / "state" / "call_test_result.json"
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("")
    print("RESULT: %s   (recorded: %s)" % ("PASS" if passed else "FAIL", out))
    if not passed and connected is None:
        print("        not confirmed by a person, so it cannot count as a pass")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
