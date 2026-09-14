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

  It is the Linux handover's PART 6.3 turned into a tool, with the Firefox 155
  corrections described in analyze_call_log.py.

WHAT IT LEARNED IN USE (2026-09-14)
  - It used to REFUSE while Firefox was running and tell the user to close it.
    The user: "make sure you kill every instance of the firefox and stop
    asking ME to do that." It now closes Firefox itself (gracefully first),
    unless --no-kill.
  - The first call that worked had three prefs hand-set in the PROFILE. That
    was recorded as a pass for a build that did not carry them. It now reads
    the profile, compares it with the installed package, and records every
    watched override in profile_overrides - which publish_gate.py refuses.
  - The cause was found only in the page's own warnings, so console and
    PageMessages are logged by default.

WHAT IT ASKS OF YOU
  1. say yes
  2. place ONE short call. 30 seconds is enough; voice-only uses the least data
  3. close the browser completely
  4. answer two questions: did it connect, could you both hear each other

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
import profile_prefs as pp          # noqa: E402  find_profile(), overrides(), stop_firefox()
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
    ap.add_argument("--no-kill", action="store_true",
                    help="refuse instead of closing a running Firefox")
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
        if args.no_kill:
            print("REFUSED: firefox.exe is running (pid %s) and --no-kill was given."
                  % ", ".join(pids))
            return 1
        print("Closing Firefox (pid %s): a browser that is already running never "
              "sees the logging switch, and the capture would be empty." % ", ".join(pids))
        pp.stop_firefox()
        if running_firefox():
            print("could not close Firefox - close it, then run this again")
            return 1

    profile = pp.find_profile(install)
    before = pp.overrides(install, profile, pp.CALL_PREFIXES) if profile else {}
    if before:
        print("")
        print("NOTE: the profile overrides %d watched pref(s) the build does not ship:" % len(before))
        for k, v in before.items():
            print("   %-44s profile=%s build=%s" % (k, v["profile"], v["build"]))
        print("A call that passes like this proves the PROFILE, not the installer.")
        print('Remove them with: python "working scripts/profile_prefs.py" --unset <name>')

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
            print("microphone or speaker device, or a codec. Look at the AUDIO and PAGE")
            print("lines above and at cubeb / MediaManager lines in the log.")

    overrides = pp.overrides(install, profile, pp.CALL_PREFIXES) if profile else {}
    passed = bool(r["passed"] and connected and audio)
    record = {
        "passed": passed,
        "layer": r["layer"],
        "detail": r["detail"],
        "dtls_cap": r["dtls_cap"],
        "data_flowed": r["data_flowed"],
        "user_connected": connected,
        "user_audio_both_ways": audio,
        "build_id": vab.build_id(install),
        "install": str(install),
        "profile": str(profile) if profile else None,
        "profile_overrides": overrides,
        "ships_in_build": not overrides,
        "when": datetime.datetime.now().isoformat(timespec="seconds"),
        "minutes": round((time.time() - t0) / 60, 1),
        "log_dir": str(logdir),
        "counts": r["counts"],
        "legs": r["legs"],
        "page_problems": r.get("page_problems", []),
    }
    out = ROOT / "state" / "call_test_result.json"
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("")
    print("RESULT: %s   (recorded: %s)" % ("PASS" if passed else "FAIL", out))
    if passed and overrides:
        print("        but it depended on %d profile override(s) - the publish gate will"
              % len(overrides))
        print("        refuse it until they are in the build and the call is repeated")
    if not passed and connected is None:
        print("        not confirmed by a person, so it cannot count as a pass")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
