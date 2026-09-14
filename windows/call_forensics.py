"""First sixty seconds of a "calls don't work" report: collect the evidence.

WHY THIS EXISTS
  2026-09-14 began with "you claim webrtc works. It does not ... unless you
  forgot to delete the previous binary and install the new one". Answering
  that honestly took an hour of hand-typed PowerShell and inline Python, and
  every piece of it is reusable:

    which firefox.exe files exist, and which one the profile last ran
    what the INSTALLED package resolves for the call prefs (not the source)
    whether the profile overrides any of them
    whether the site is allowed the camera and microphone
    whether Windows itself allows them, and when this exe last used them
    whether the network has IPv6 (WhatsApp offers IPv6-only relay legs)
    whether Windows recorded a crash

  Each answer ruled out a hypothesis that was genuinely on the table: a stale
  binary, a profile user.js, a blocked permission, a crash. None of them was
  the cause - dom.workers.maxPerDomain was - but each had to be excluded with
  evidence rather than assumed away.

  Read-only. Starts nothing, changes nothing, sends nothing.

USAGE
    python "working scripts/call_forensics.py"
    python "working scripts/call_forensics.py" --site web.whatsapp.com --firewall
"""
import argparse
import datetime
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import profile_prefs as pp          # noqa: E402
import verify_address_bar as vab    # noqa: E402

# pref -> (what the build must resolve, why). A callable returns True when OK.
CALL_PREFS = {
    "media.peerconnection.dtls.version.max":
        (lambda v: v == "771", "771 - Meta's relays drop DTLS 1.3 traffic"),
    "dom.workers.maxPerDomain":
        (lambda v: v.isdigit() and int(v) >= 64,
         ">= 64 (upstream 512) - at 8 WhatsApp's call worker was queued"),
    "media.webm.enabled":
        (lambda v: v == "true", "true - WebCodecs checks VP8 against WebM"),
    "media.ogg.enabled":
        (lambda v: v == "true", "true - WebCodecs checks Opus against Ogg"),
    "media.peerconnection.enabled":
        (lambda v: v == "true", "true - WebRTC itself"),
    "media.navigator.enabled":
        (lambda v: v == "true", "true - getUserMedia"),
    "permissions.default.camera":
        (lambda v: v != "2", "not 2 (2 blocks every site)"),
    "permissions.default.microphone":
        (lambda v: v != "2", "not 2 (2 blocks every site)"),
}


def ps(cmd, timeout=120):
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                           capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "").strip()
    except Exception as exc:
        return "(could not run: %s)" % exc


def section(title):
    print("")
    print("=== %s ===" % title)


def filetime(v):
    try:
        return (datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=v // 10)
                ).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return "-"


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", default="web.whatsapp.com")
    ap.add_argument("--firewall", action="store_true",
                    help="also list firewall rules for the exe (slow, ~30 s)")
    args = ap.parse_args()
    install = vab.find_install()

    section("installed build")
    if not install:
        print("  no installed Gorilla Unleashed found")
        return 2
    ai = install / "application.ini"
    bid = next((l.split("=", 1)[1] for l in ai.read_text(errors="replace").splitlines()
                if l.startswith("BuildID=")), "?") if ai.is_file() else "?"
    print("  %s   BuildID %s   firefox.exe %s"
          % (install, bid, datetime.datetime.fromtimestamp(
              (install / "firefox.exe").stat().st_mtime).strftime("%Y-%m-%d %H:%M")))
    print("  running: %s" % (ps("Get-Process firefox -ErrorAction SilentlyContinue | "
                                "ForEach-Object { $_.Path } | Sort-Object -Unique")
                             or "none"))
    others = ps("foreach ($r in @($env:LOCALAPPDATA, $env:USERPROFILE, 'C:\\Program Files', "
                "'C:\\Program Files (x86)')) { Get-ChildItem $r -Filter firefox.exe -Recurse "
                "-Depth 4 -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName } }")
    for line in sorted(set(others.splitlines())):
        if line.strip() and line.strip().lower() != str(install / "firefox.exe").lower():
            print("  OTHER firefox.exe on disk: %s" % line.strip())

    section("profile")
    profile = pp.find_profile(install)
    if not profile:
        print("  no profile has run this install")
    else:
        prefs = profile / "prefs.js"
        print("  %s   prefs.js %s" % (profile, datetime.datetime.fromtimestamp(
            prefs.stat().st_mtime).strftime("%Y-%m-%d %H:%M") if prefs.is_file() else "absent"))
        print("  user.js: %s" % ("PRESENT" if (profile / "user.js").is_file() else "absent"))

    section("call prefs: installed package vs profile")
    d = pp.installed_defaults(install)
    up = pp.user_prefs(profile) if profile else {}
    for k, (ok, why) in CALL_PREFS.items():
        build = pp.norm(d[k]) if k in d else "(built-in default)"
        prof = pp.norm(up[k][0]) if k in up else None
        effective = prof if prof is not None else build
        flag = "ok " if k not in d and prof is None else ("ok " if ok(effective) else "BAD")
        print("  [%s] %-40s build=%-8s%s  needs %s"
              % (flag, k, build, (" profile=%s" % prof) if prof is not None else "", why))
    if profile:
        o = pp.overrides(install, profile, pp.CALL_PREFIXES)
        print("  profile overrides of watched prefs: %d%s"
              % (len(o), "" if not o else " -> " + ", ".join(sorted(o))[:200]))

    section("site permissions for %s" % args.site)
    if profile and (profile / "permissions.sqlite").is_file():
        tmp = Path(tempfile.mkdtemp())
        for suf in ("", "-wal", "-shm"):
            src = profile / ("permissions.sqlite" + suf)
            if src.is_file():
                shutil.copy2(src, tmp / src.name)
        rows = sqlite3.connect(str(tmp / "permissions.sqlite")).execute(
            "select origin, type, permission from moz_perms where origin like ? "
            "and type in ('camera','microphone','screen')", ("%" + args.site + "%",)).fetchall()
        for o, t, p in rows:
            print("  %-34s %-11s %s" % (o, t, {1: "allow", 2: "BLOCK"}.get(p, p)))
        if not rows:
            print("  none recorded (the site will prompt)")
        shutil.rmtree(tmp, ignore_errors=True)

    section("Windows camera / microphone access")
    try:
        import winreg
        exe_key = str(install / "firefox.exe").replace("\\", "#")
        for cap in ("microphone", "webcam"):
            base = r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\%s" % cap
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, base) as k:
                    allowed = winreg.QueryValueEx(k, "Value")[0]
            except OSError:
                allowed = "?"
            last = "never used by this exe"
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, base + r"\NonPackaged\\" + exe_key) as k:
                    s = winreg.QueryValueEx(k, "LastUsedTimeStart")[0]
                    e = winreg.QueryValueEx(k, "LastUsedTimeStop")[0]
                    last = "last used %s -> %s" % (filetime(s), filetime(e))
            except OSError:
                pass
            print("  %-10s %-6s %s" % (cap, allowed, last))
    except ImportError:
        print("  (winreg unavailable)")

    section("network")
    print("  " + (ps("Get-NetConnectionProfile | ForEach-Object { \"$($_.Name): IPv4 "
                     "$($_.IPv4Connectivity), IPv6 $($_.IPv6Connectivity)\" }") or "?"))
    print("  (no IPv6 means WhatsApp's IPv6-only relay legs fail - harmless, "
          "a working call has them too)")
    if args.firewall:
        section("firewall rules for this exe")
        print(ps("Get-NetFirewallApplicationFilter | Where-Object { $_.Program -like '*%s*' } "
                 "| ForEach-Object { $r = $_ | Get-NetFirewallRule; \"  $($r.Direction) "
                 "$($r.Action) $($r.Profile) enabled=$($r.Enabled)\" }" % install.name,
                 timeout=300) or "  none")

    section("crashes and hangs recorded by Windows, last 3 days")
    print(ps("Get-WinEvent -FilterHashtable @{LogName='Application'; Id=1000,1001,1002; "
             "StartTime=(Get-Date).AddDays(-3)} -ErrorAction SilentlyContinue | "
             "Where-Object { $_.Message -match 'firefox.exe|plugin-container' } | "
             "ForEach-Object { \"  $($_.TimeCreated)  id=$($_.Id)  \" + "
             "(($_.Message -split \"`n\" | Select-String 'Event Name|P1:' | "
             "ForEach-Object { $_.Line.Trim() }) -join ' ') }") or "  none")
    print("")
    print("Next: python \"working scripts/webrtc_selftest.py\" (hidden, no data), then a "
          "logged call with capture_call_log.py. RUNBOOK PART E has the full order.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
