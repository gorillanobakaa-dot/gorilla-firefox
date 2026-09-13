"""Prove a bundled extension is present AND VISIBLE, not merely loaded.

WHY THE DISTINCTION MATTERS
  A bundled extension can be in one of three states, and two of them look like
  success from the wrong angle:

    absent      not in the build at all
    hidden      loads, runs, blocks ads, has a toolbar button - and does not
                appear in about:addons, so the user cannot reach its settings
                or turn it off
    visible     loads, runs, AND is listed in about:addons

  The middle state is the dangerous one. It was reached first, and it looked
  entirely fine from the toolbar: uBlock Origin was blocking on YouTube, its
  dashboard opened, its filter lists had downloaded. Only the Add-ons Manager
  told the truth, and nothing in any log mentioned it.

  So this checks the LOCATION, not merely presence.

    app-builtin          hidden() -> false   VISIBLE      what you want
    app-builtin-addons   hidden() -> true    invisible    silently wrong

THE OTHER THING IT REFUSES TO DO
  It does not verify headless. `firefox -headless -screenshot` does not run
  BrowserGlue's _onFirstWindowLoaded, so the registration never fires and the
  extension appears absent even when the build is perfect. That produced a
  completely wrong diagnosis once already. This launches a real window.

USAGE
    python "working scripts/verify_builtin_extension.py"
    python "working scripts/verify_builtin_extension.py" --install "C:/path"
    python "working scripts/verify_builtin_extension.py" --source-only
    python "working scripts/verify_builtin_extension.py" --quiet
"""
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(os.environ.get("GORILLA_ROOT")
            or Path(__file__).resolve().parent.parent)


def state(root):
    p = root / "state" / "builtin_extensions.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8")).get("extensions", [])
    return []


def objdir(root):
    m = root / "config" / "mozconfig.win64"
    if m.is_file():
        for line in m.read_text(encoding="utf-8", errors="replace").splitlines():
            t = line.strip()
            if not t.startswith("#") and "MOZ_OBJDIR=" in t:
                return Path(t.split("MOZ_OBJDIR=", 1)[1].strip()
                            .replace("@TOPSRCDIR@", str(root / "src")))
    # Linux default: in-tree objdir
    for c in (root / "src").glob("obj-*"):
        if c.is_dir():
            return c
    return None


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
    c = Path(os.environ.get("USERPROFILE", "")) / "Gorilla Unleashed"
    return c if (c / "firefox.exe").is_file() else None


def check_source(root, exts, say):
    """The five pieces must all be present in the tree."""
    src = root / "src"
    bad = []
    say("")
    say("1. SOURCE TREE")
    for e in exts:
        d = src / "browser" / "extensions" / e["dir"]
        rows = [
            ("unpacked",     (d / "manifest.json").is_file()),
            ("jar.mn",       (d / "jar.mn").is_file()),
            ("moz.build",    (d / "moz.build").is_file()),
            ("in DIRS",      ('"%s"' % e["dir"]) in
                             (src / "browser" / "extensions" / "moz.build")
                             .read_text(encoding="utf-8", errors="replace")),
            ("registered",   e["id"] in
                             (src / "browser" / "modules" /
                              "GorillaBuiltinExtensions.sys.mjs")
                             .read_text(encoding="utf-8", errors="replace")
                             if (src / "browser" / "modules" /
                                 "GorillaBuiltinExtensions.sys.mjs").is_file()
                             else False),
        ]
        say("   %s" % e["dir"])
        for label, ok in rows:
            say("     %s %s" % ("+" if ok else "!", label))
            if not ok:
                bad.append("%s: %s" % (e["dir"], label))

    # The jar.mn must NOT target builtin-addons/ - that is the hidden location.
    for e in exts:
        j = src / "browser" / "extensions" / e["dir"] / "jar.mn"
        if j.is_file():
            body = j.read_text(encoding="utf-8", errors="replace")
            if re.search(r"^\s+builtin-addons/", body, re.M):
                say("     ! jar.mn packages under builtin-addons/ - that forces")
                say("       the HIDDEN location (gen_built_in_addons.py globs it)")
                bad.append("%s: packaged under builtin-addons/" % e["dir"])
    return bad


def check_build(root, exts, say):
    od = objdir(root)
    say("")
    say("2. BUILD OUTPUT")
    if not od or not od.is_dir():
        say("   objdir not found - skipping")
        return []
    binroot = od / "dist" / "bin"
    bad = []
    for e in exts:
        d = binroot / "browser" / "chrome" / "browser" / "gorilla-addons" / e["dir"]
        n = sum(1 for _ in d.rglob("*") if _.is_file()) if d.is_dir() else 0
        say("   %s %-22s %d packaged file(s)"
            % ("+" if n else "!", e["dir"], n))
        if not n:
            bad.append("%s: not in the build output" % e["dir"])

    bia = (binroot / "browser" / "chrome" / "browser" / "content" / "browser"
           / "built_in_addons.json")
    if bia.is_file():
        ids = [b["addon_id"] for b in
               json.loads(bia.read_text(encoding="utf-8")).get("builtins", [])]
        for e in exts:
            leaked = e["id"] in ids
            say("   %s %-22s %s"
                % ("!" if leaked else "+", e["dir"],
                   "IS in built_in_addons.json - it will be HIDDEN" if leaked
                   else "correctly absent from built_in_addons.json"))
            if leaked:
                bad.append("%s: routed to the hidden location" % e["dir"])
    return bad


def check_runtime(install, exts, say, seconds):
    """Launch a REAL window and read the location the browser assigned."""
    say("")
    say("3. RUNNING BROWSER  (a real window - headless does not run the hook)")
    exe = install / "firefox.exe"
    if not exe.is_file():
        exe = install / "firefox"
    if not exe.is_file():
        say("   no firefox binary at %s - skipping" % install)
        return []
    prof = Path(tempfile.mkdtemp(prefix="verifyext_"))
    bad = []
    try:
        p = subprocess.Popen([str(exe), "-profile", str(prof), "-no-remote",
                              "about:addons"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(seconds)
        try:
            p.terminate()
        except Exception:
            pass
        time.sleep(2)
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-Process firefox -ErrorAction SilentlyContinue |"
                        " Stop-Process -Force"],
                       capture_output=True)
        j = prof / "extensions.json"
        if not j.is_file():
            say("   the browser wrote no extensions.json")
            return ["no extensions.json"]
        addons = json.loads(j.read_text(encoding="utf-8")).get("addons", [])
        by_id = {a.get("id"): a for a in addons}
        for e in exts:
            a = by_id.get(e["id"])
            if not a:
                say("   ! %-22s NOT PRESENT" % e["dir"])
                bad.append("%s: absent at runtime" % e["dir"])
                continue
            loc = a.get("location")
            vis = loc == "app-builtin"
            say("   %s %-22s location=%-20s active=%s"
                % ("+" if vis and a.get("active") else "!", e["dir"],
                   loc, a.get("active")))
            if not vis:
                say("       ^ %s is the HIDDEN location - it will not appear"
                    % loc)
                say("         in about:addons. See docs/HOWTO-BUNDLE-AN-EXTENSION.md")
                bad.append("%s: hidden location (%s)" % (e["dir"], loc))
            elif not a.get("active"):
                bad.append("%s: present but not active" % e["dir"])
    finally:
        shutil.rmtree(prof, ignore_errors=True)
    return bad


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--install", default=None)
    ap.add_argument("--source-only", action="store_true")
    ap.add_argument("--seconds", type=int, default=25,
                    help="how long to let the browser start (default 25)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    root = Path(args.root)
    say = (lambda *a: None) if args.quiet else print
    exts = state(root)
    if not exts:
        print("no bundled extensions recorded "
              "(state/builtin_extensions.json) - nothing to verify")
        return 0

    say("bundled: %s" % ", ".join("%s %s" % (e["dir"], e["version"]) for e in exts))
    bad = []
    bad += check_source(root, exts, say)
    bad += check_build(root, exts, say)
    if not args.source_only:
        install = Path(args.install) if args.install else find_install()
        if install:
            bad += check_runtime(install, exts, say, args.seconds)
        else:
            say("")
            say("3. RUNNING BROWSER - no install found, skipped")

    say("")
    say("=" * 68)
    if bad:
        print("FAIL: %d problem(s)" % len(bad))
        for b in bad:
            print("  - %s" % b)
        return 1
    say("OK: every bundled extension is packaged, registered, and VISIBLE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
