"""Read and change prefs in the Gorilla profile - the mechanical part, done safely.

WHY THIS EXISTS
  2026-09-14, while chasing broken WhatsApp calls, the same steps were typed by
  hand six times: stop every firefox.exe, back up prefs.js, add or remove
  user_pref lines, confirm what landed. Twice the command was blocked by a
  shell safety check over a Remove-Item, and once a pass was recorded that
  quietly depended on three hand-set prefs the installer did not carry. The
  user, fairly: "stop asking ME to do this."

  Two facts make this worth a tool rather than a one-liner:
    - Firefox REWRITES prefs.js on exit. Edit it while the browser runs and
      your change is overwritten. So this stops the browser first.
    - A user pref that differs from the build's default is invisible in every
      source-tree check, and it can make a broken build look fixed. --overrides
      compares the profile against the INSTALLED package, not the source.

WHICH PROFILE
  The one whose compatibility.ini says it was last run by the installed
  Gorilla (LastPlatformDir) - not "the default profile", which on this machine
  was an old Mozilla Firefox profile.

USAGE
    python "working scripts/profile_prefs.py" --list --match media.
    python "working scripts/profile_prefs.py" --overrides
    python "working scripts/profile_prefs.py" --set dom.workers.maxPerDomain=512
    python "working scripts/profile_prefs.py" --unset dom.workers.maxPerDomain
"""
import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_address_bar as vab    # noqa: E402  find_install()

# Prefixes where a profile override can change whether calls, media or privacy
# behave as the build intends. Used by --overrides and by capture_call_log.py.
WATCH = ("media.", "dom.workers.", "dom.ipc.", "network.", "security.",
         "privacy.", "javascript.options.", "permissions.default.")

RX_USER = re.compile(r'^\s*user_pref\("([^"]+)"\s*,\s*(.+?)\);\s*$')
RX_PREF = re.compile(r'^\s*pref\("([^"]+)"\s*,\s*(.+?)(?:\s*,\s*locked)?\);')


def find_profile(install):
    """The profile last run by this install, per compatibility.ini."""
    base = Path(os.environ.get("APPDATA", "")) / "Mozilla" / "Firefox" / "Profiles"
    want = str(install).rstrip("\\/").lower()
    hits = []
    for prof in base.glob("*"):
        ci = prof / "compatibility.ini"
        if not ci.is_file():
            continue
        text = ci.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^LastPlatformDir=(.+)$", text, re.M)
        if m and m.group(1).strip().rstrip("\\/").lower() == want:
            prefs = prof / "prefs.js"
            hits.append((prefs.stat().st_mtime if prefs.is_file() else 0, prof))
    return max(hits)[1] if hits else None


def norm(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v.lower() if v.lower() in ("true", "false") else v


def user_prefs(profile):
    out = {}
    for name in ("prefs.js", "user.js"):
        p = profile / name
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            m = RX_USER.match(line)
            if m:
                out[m.group(1)] = (m.group(2), name)
    return out


def installed_defaults(install):
    """Last definition wins, in Firefox's load order: greprefs.js, then the
    app's defaults/preferences/*.js. Packaged files are already preprocessed,
    so there are no #if blocks to skip."""
    out = {}
    sources = [(install / "omni.ja", ["greprefs.js"])]
    bo = install / "browser" / "omni.ja"
    if bo.is_file():
        names = sorted(n for n in zipfile.ZipFile(bo).namelist()
                       if re.fullmatch(r"defaults/preferences/[^/]+\.js", n))
        sources.append((bo, names))
    for jar, names in sources:
        z = zipfile.ZipFile(jar)
        for n in names:
            for line in z.read(n).decode("utf-8", "replace").splitlines():
                m = RX_PREF.match(line)
                if m:
                    out[m.group(1)] = m.group(2)
    return out


# The prefixes that can decide whether a CALL works. capture_call_log.py and
# the publish gate use these, not WATCH: a changed privacy or cookie setting is
# the user's business and says nothing about whether calls work in the build.
CALL_PREFIXES = ("media.", "dom.workers.", "permissions.default.",
                 "javascript.options.", "network.proxy.")

# Firefox writes its own bookkeeping into prefs.js - update-check timestamps,
# migration flags, "last seen" build ids. Nobody chose them. Measured
# 2026-09-14: 14 such entries in an ordinary profile, which made the first
# version of this report every call as hand-tuned - and would have made the
# publish gate refuse every call forever.
BOOKKEEPING = re.compile(r"(lastCheck|lastEmptyCheck|last_|\.last[A-Z]|[Mm]igrat|"
                         r"\.buildID$|observed$|pending$|date|Epoch|failed$)")


def overrides(install, profile, prefixes=WATCH):
    """User prefs under the given prefixes whose value differs from the
    installed build's default, ignoring Firefox's own bookkeeping."""
    d = installed_defaults(install)
    res = {}
    for k, (v, src) in sorted(user_prefs(profile).items()):
        if not k.startswith(prefixes) or BOOKKEEPING.search(k):
            continue
        if k in d and norm(d[k]) == norm(v):
            continue
        res[k] = {"profile": norm(v), "build": norm(d[k]) if k in d else None, "file": src}
    return res


def running_firefox():
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq firefox.exe", "/NH"],
                       capture_output=True, text=True)
    return "firefox.exe" in (r.stdout or "").lower()


def stop_firefox(say=print):
    """Graceful close first (so logs and prefs flush), force after 15 s."""
    if not running_firefox():
        return
    say("stopping Firefox...")
    subprocess.run(["taskkill", "/IM", "firefox.exe"], capture_output=True)
    for _ in range(30):
        if not running_firefox():
            return
        time.sleep(0.5)
    for image in ("firefox.exe", "plugin-container.exe", "private_browsing.exe"):
        subprocess.run(["taskkill", "/IM", image, "/F"], capture_output=True)
    time.sleep(1)


def js_literal(raw):
    r = raw.strip()
    if r.lower() in ("true", "false"):
        return r.lower()
    if re.fullmatch(r"-?\d+", r):
        return r
    if len(r) >= 2 and r[0] == r[-1] == '"':
        return r
    return '"%s"' % r.replace("\\", "\\\\").replace('"', '\\"')


def rewrite(profile, set_pairs, unset_keys):
    p = profile / "prefs.js"
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = p.with_name("prefs.js.bak-%s" % stamp)
    shutil.copy2(p, backup)
    drop = set(unset_keys) | {k for k, _ in set_pairs}
    lines = [l for l in p.read_text(encoding="utf-8", errors="replace").splitlines()
             if not (RX_USER.match(l) and RX_USER.match(l).group(1) in drop)]
    lines += ['user_pref("%s", %s);' % (k, js_literal(v)) for k, v in set_pairs]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return backup


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--match", default="", help="filter --list by substring")
    ap.add_argument("--overrides", action="store_true")
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    ap.add_argument("--unset", action="append", default=[], metavar="NAME")
    args = ap.parse_args()

    install = vab.find_install()
    if not install:
        print("no installed Gorilla Unleashed found")
        return 2
    profile = find_profile(install)
    if not profile:
        print("no profile has been run by %s yet" % install)
        return 2
    print("install: %s\nprofile: %s" % (install, profile))

    if args.set or args.unset:
        stop_firefox()
        pairs = [tuple(s.split("=", 1)) for s in args.set]
        backup = rewrite(profile, pairs, args.unset)
        print("backup : %s" % backup)
        now = user_prefs(profile)
        for k, _ in pairs:
            print("  set    %-44s %s" % (k, now.get(k, ("MISSING",))[0]))
        for k in args.unset:
            print("  unset  %-44s %s" % (k, "gone" if k not in now else "STILL PRESENT"))
    if args.list:
        for k, (v, src) in sorted(user_prefs(profile).items()):
            if args.match in k:
                print("  %-56s %-20s %s" % (k, v[:20], src))
    if args.overrides:
        o = overrides(install, profile)
        if not o:
            print("no watched pref in the profile differs from the installed build")
        for k, v in o.items():
            print("  %-48s profile=%-10s build=%-10s (%s)"
                  % (k, v["profile"], v["build"], v["file"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
