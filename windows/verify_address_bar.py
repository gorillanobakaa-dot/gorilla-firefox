"""Prove the address bar WORKS - not that it renders.

WHY THIS EXISTS
  2026-09-13: a build shipped where typing into the address bar or the search
  field did nothing.

  Every check in this project passed at the time. The build was green, the
  installed browser carried every tracked fix, the theme rendered, the search
  configuration was valid JSON with 122 engines and google as the global
  default. None of that is the same as being able to type an address and go
  somewhere, and nothing in the harness had ever tried.

  A browser whose address bar does not navigate is not a browser. This runs
  before publishing.

WHAT IT DOES
  Launches the installed build with a real window and a throwaway profile,
  then for each case: Ctrl+L, select all, type, Enter, wait, and read the
  WINDOW TITLE.

  The title is the signal because it changes only when a navigation actually
  completed. A screenshot shows pixels; a title proves the browser went
  somewhere.

THE THREE CASES
  about   about:robots    - the type -> parse -> navigate path, NO NETWORK.
                            If this fails the address bar itself is broken.
  url     www.google.com  - a bare hostname: fixup, DNS, load. Needs network.
  search  "gorilla test"  - not a URL, so it must reach the default SEARCH
                            ENGINE. This is the one that breaks when the
                            search configuration is missing or unreachable,
                            and it fails independently of the other two.

  Network cases are reported but do not fail the run when the machine is
  offline - being on a train is not a browser defect. `about` always counts.

USAGE
    python "working scripts/verify_address_bar.py"
    python "working scripts/verify_address_bar.py" --install "C:/path/to/dir"
    python "working scripts/verify_address_bar.py" --quiet
"""
import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(os.environ.get("GORILLA_ROOT")
            or Path(__file__).resolve().parent.parent)

# what the window title must contain for each case to count as a navigation
EXPECT = {
    "about":  (["robot", "gort", "klaatu"],
               "about:robots did not load - the address bar never navigated"),
    "url":    (["google"],
               "typing a bare hostname did not reach the site"),
    "search": (["gorilla test", "google", "search"],
               "a non-URL search term did not reach a search engine"),
}
NEEDS_NET = {"url", "search"}


def build_id(install):
    """Identify the BUILD being tested, so a stale pass cannot vouch for a new one.

    Hashes the files a rebuild always changes. If any byte of these differs, the
    recorded result belongs to a different browser and must not count.
    """
    h = hashlib.sha256()
    for rel in ("firefox.exe", "browser/omni.ja", "omni.ja", "xul.dll"):
        p = install / rel
        if p.is_file():
            h.update(rel.encode())
            h.update(str(p.stat().st_size).encode())
            with open(p, "rb") as fh:          # head+tail is enough to pin identity
                h.update(fh.read(1 << 20))
                if p.stat().st_size > (1 << 21):
                    fh.seek(-(1 << 20), 2)
                    h.update(fh.read())
    return h.hexdigest()


def record(root, install, ok, titles, skipped):
    out = root / "state" / "address_bar_result.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "passed": bool(ok),
        "build_id": build_id(install),
        "install": str(install),
        "when": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "skipped_offline": sorted(skipped),
        "titles": {k: v for k, v in titles.items() if not k.startswith("__")},
    }, indent=2) + chr(10), encoding="utf-8")
    return out


BANNER = """
  ==================================================================
   STOP. THIS TAKES OVER YOUR KEYBOARD FOR ABOUT 60 SECONDS.

   It opens a browser window, presses Ctrl+L and types into it. If
   you touch the keyboard or mouse while it runs, your keystrokes
   and its keystrokes interleave and the result is GARBAGE - it will
   report failures that are not real.

   That happened on 2026-09-13 and produced a false alarm about the
   address bar being broken when it was fine.

   Do not type. Do not click. Do not move the mouse.
  ==================================================================
"""


def online(host="1.1.1.1", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False


def find_install():
    lnk = Path(os.environ.get("USERPROFILE", "")) / "Desktop" / "Gorilla Unleashed.lnk"
    if lnk.is_file():
        ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut("
              + repr(str(lnk)).replace('"', "'") + ");Write-Output $s.TargetPath")
        try:
            r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                               capture_output=True, text=True, timeout=60)
            t = (r.stdout or "").strip()
            if t and Path(t).is_file():
                return Path(t).parent
        except Exception:
            pass
    for c in (Path(os.environ.get("LOCALAPPDATA", "")) / "Gorilla Unleashed",
              Path(os.environ.get("USERPROFILE", "")) / "Gorilla Unleashed"):
        if (c / "firefox.exe").is_file():
            return c
    return None


def run(install, scratch, say):
    exe = install / "firefox.exe"
    ps1 = ROOT / "working scripts" / "verify_address_bar.ps1"
    if not ps1.is_file():
        say("driver missing: %s" % ps1)
        return None
    say("driving a real window - this takes about a minute, do not touch the")
    say("keyboard or move the mouse while it runs.")
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-File", str(ps1), str(scratch), str(exe)],
                       capture_output=True, text=True, timeout=600)
    out = (r.stdout or "") + (r.stderr or "")
    titles, shot = {}, None
    for line in out.splitlines():
        if line.startswith("RESULT|"):
            parts = line.split("|", 2)
            if parts[1] == "NOWINDOW":
                return {"__nowindow__": parts[2]}
            titles[parts[1]] = parts[2].strip()
        elif line.startswith("SHOT|"):
            shot = line.split("|", 1)[1].strip()
    if shot:
        titles["__shot__"] = shot
    return titles


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--install", default=None)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--yes", action="store_true",
                    help="skip the keyboard warning prompt (for unattended runs)")
    args = ap.parse_args()
    say = (lambda *a: None) if args.quiet else print

    install = Path(args.install) if args.install else find_install()
    if not install or not (install / "firefox.exe").is_file():
        print("no installed build found - install one first, then re-run")
        return 2

    if not args.yes:
        print(BANNER)
        try:
            if input("  Ready? nothing else touching the keyboard? [y/N]: "
                     ).strip().lower() not in ("y", "yes"):
                print("  aborted - nothing was run")
                return 2
        except EOFError:
            print("  no terminal to confirm at; pass --yes if you really mean it")
            return 2

    net = online()
    say("install : %s" % install)
    say("network : %s" % ("up" if net else "DOWN - network cases will be skipped"))

    scratch = Path(tempfile.mkdtemp(prefix="addrbar_"))
    titles = run(install, scratch, say)
    if titles is None:
        return 2
    if "__nowindow__" in titles:
        print("FAIL: %s" % titles["__nowindow__"])
        return 1

    say("")
    bad, skipped = [], []
    for case, (needles, why) in EXPECT.items():
        title = titles.get(case)
        if title is None:
            bad.append("%s: the driver reported nothing" % case)
            say("   ! %-7s no result" % case)
            continue
        hit = any(n.lower() in title.lower() for n in needles)
        if hit:
            say("   + %-7s navigated  title=%r" % (case, title[:56]))
            continue
        if case in NEEDS_NET and not net:
            skipped.append(case)
            say("   . %-7s skipped (offline)" % case)
            continue
        say("   ! %-7s DID NOT NAVIGATE  title=%r" % (case, title[:56]))
        say("       %s" % why)
        bad.append("%s: %s (title was %r)" % (case, why, title[:56]))

    shot = titles.get("__shot__")
    if shot:
        say("")
        say("   screenshot: %s" % shot)

    say("")
    say("=" * 68)
    rec = record(ROOT, install, not bad, titles, skipped)
    say("   recorded: %s" % rec)
    say("")
    if bad:
        print("FAIL: the address bar does not work")
        for b in bad:
            print("  - %s" % b)
        print("")
        print("  This is the defect a green build cannot see. Do not publish.")
        return 1
    if skipped:
        print("OK: the address bar navigates (%d network case(s) skipped, offline)"
              % len(skipped))
        return 0
    say("OK: the address bar navigates - typed URL, bare hostname and search.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
