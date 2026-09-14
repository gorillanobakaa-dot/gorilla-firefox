"""Repair hardening that a later pref file silently undoes.

THE BUG THIS FIXES
  Firefox loads preference files in order and THE LAST DEFINITION WINS:

      greprefs.js              <- built from modules/libpref/init/all.js
      browser/.../firefox.js   <- application defaults, loaded AFTER

  A pref hardened in all.js is undone by any later definition in firefox.js.
  Nothing fails. Nothing logs. The browser ships with the opposite value.

  2026-09-13: eight privacy prefs did, in a browser whose release notes say
  telemetry and sponsored content are removed - captive-portal polling of
  detectportal.firefox.com, Google Safe Browsing for malware and phishing,
  Firefox Accounts, two sponsored-content settings, urlbar weather and group
  labels. It was noticed because the Firefox Accounts icon was visible in a
  screenshot, not by any check.

  The fix is to restate them at the END of firefox.js, where they win.

THREE MISTAKES THIS SCRIPT EXISTS TO PREVENT
  The first two were made by the throwaway version of it, within ten minutes.
  The third shipped.

  1. IT READ PREFS FROM INSIDE #if BLOCKS.
     security.sandbox.content.level appears four times in firefox.js, each in a
     platform guard: 9 Windows, 3 macOS, 6 Linux, 1 OpenBSD. A naive
     "last definition wins" scan returns 1 - the OpenBSD value - and concludes
     Windows ships sandbox level 1.

  2. IT TREATED THE all.js VALUE AS AUTHORITATIVE.
     Acting on that reading would have set the Windows content sandbox from 4
     to 1. HIGHER IS STRONGER. It would have shipped a materially weaker
     sandbox in the name of hardening the browser.

  3. IT TREATED EVERY all.js DIFFERENCE AS HARDENING.
     The 2026-09-13 run "repaired" nine prefs. One of them,
     javascript.options.mem.max, is a JavaScript heap cap, not a privacy
     setting. firefox.js's 2048 is what every Linux build and Windows .2
     shipped; the repair copied all.js's 1024 over it and halved the cap on
     Windows .3 alone, in a build whose release notes then called all nine
     "privacy settings". Found 2026-09-14 while auditing why WhatsApp calls
     still failed on that build. Not proven to be the cause - but a change
     nobody decided, to a value the working Linux setup does not have.

  So preprocessor blocks are skipped entirely, anything in DO_NOT_WEAKEN is
  refused with an explanation, and anything in NOT_HARDENING is left alone.

  Same class as the 2026-09-11 GPU-process regression: a value that is correct
  on Linux is not automatically correct on Windows - and a value in all.js is
  not automatically a hardening decision.

USAGE
    python "working scripts/fix_prefs_last_wins.py" --check
    python "working scripts/fix_prefs_last_wins.py" --apply
"""
import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("GORILLA_ROOT")
            or Path(__file__).resolve().parent.parent)

MARK = "GORILLA: hardening that all.js could not deliver"

# Prefs a user must not be able to re-enable at runtime.
LOCK = {
    "network.captive-portal-service.enabled",
    "browser.safebrowsing.malware.enabled",
    "browser.safebrowsing.phishing.enabled",
    "identity.fxaccounts.enabled",
    "browser.newtabpage.activity-stream.discoverystream.spocs-endpoint",
    "browser.newtabpage.activity-stream.discoverystream.spoc-positions",
}

# Never repair these by copying the all.js value over the application value.
# Each is a case where the application default is deliberately STRONGER.
DO_NOT_WEAKEN = {
    "security.sandbox.content.level":
        "on Windows HIGHER IS STRONGER; firefox.js sets 4 (the Windows "
        "default) and all.js has 1. Copying all.js would gut the content "
        "sandbox. It is also platform-gated, so any reading of it from "
        "outside a guard is meaningless.",
}

# Set in all.js by the patch set, but NOT hardening. firefox.js winning is the
# intended, shipped behaviour; "repairing" it changes the browser for no reason.
NOT_HARDENING = {
    "javascript.options.mem.max":
        "a JavaScript heap cap in MB (nsJSEnvironment.cpp, JSGC_MAX_BYTES), not "
        "a privacy setting. firefox.js sets 2048, which every Linux build and "
        "Windows .2 shipped. Copying all.js's 1024 over it (2026-09-13) halved "
        "the cap on Windows .3 only. Reverted 2026-09-14.",
}


def defs(path):
    """Last definition wins, as Firefox does - but ignore #if blocks.

    A pref inside #if defined(XP_OPENBSD) is not this platform's value, and
    reading it as one is how the sandbox nearly got downgraded.
    """
    out, depth = {}, 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        t = line.strip()
        if t.startswith("#if"):
            depth += 1
            continue
        if t.startswith("#endif"):
            depth = max(0, depth - 1)
            continue
        if t.startswith("#el") or depth:
            continue
        m = re.match(r'pref\("([^"]+)"\s*,\s*([^,)]+)', t)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def hardened_by_patchset(root):
    """Only prefs the project deliberately hardens in all.js.

    Comparing every pref reports 61 differences - upstream's own two files
    disagree on purpose in many places - which buries the real ones and trains
    people to ignore the result.
    """
    ours = set()
    for p in (root / "gorilla-patchset" / "patches").glob(
            "*/modules_libpref_init_all.js.patch"):
        for m in re.finditer(r'^\+\s*pref\("([^"]+)"',
                             p.read_text(encoding="utf-8", errors="replace"),
                             re.M):
            ours.add(m.group(1))
    return ours


def analyse(root):
    src = root / "src"
    allj = src / "modules" / "libpref" / "init" / "all.js"
    ffj = src / "browser" / "app" / "profile" / "firefox.js"
    if not allj.is_file() or not ffj.is_file():
        raise SystemExit("pref files not found under %s" % src)
    a, f = defs(allj), defs(ffj)
    ours = hardened_by_patchset(root)
    if not ours:
        raise SystemExit("no all.js hardening patch found - nothing to compare")

    beaten, refused, ignored = [], [], []
    for k in sorted(ours):
        if k not in a or k not in f or a[k].lower() == f[k].lower():
            continue
        if k in NOT_HARDENING:
            ignored.append((k, a[k], f[k], NOT_HARDENING[k]))
        elif k in DO_NOT_WEAKEN:
            refused.append((k, a[k], f[k], DO_NOT_WEAKEN[k]))
        else:
            beaten.append((k, a[k], f[k]))
    return ffj, beaten, refused, ignored, len(ours)


def block(beaten):
    bar = "// " + "=" * 73
    L = ["", "", bar,
         "// " + MARK + "   (written by fix_prefs_last_wins.py)",
         bar,
         "// greprefs.js (built from modules/libpref/init/all.js) loads BEFORE",
         "// this file, and the LAST definition wins. Every pref below was",
         "// hardened in all.js and then quietly undone by an upstream default",
         "// later in this same file, so the shipped browser carried the",
         "// opposite value with nothing logged and nothing failing.",
         "//",
         "// Preflight check prefs-last-wins refuses to build if this drifts.",
         "//",
         "// These are at the END of the file ON PURPOSE. Do not move them up.",
         bar]
    for k, want, _ in beaten:
        L.append('pref("%s", %s%s);' % (k, want, ", locked" if k in LOCK else ""))
    L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    root = Path(args.root)

    ffj, beaten, refused, ignored, total = analyse(root)
    print("prefs the patch set sets in all.js       : %d" % total)
    print("hardening overridden later by firefox.js : %d" % len(beaten))
    print("")
    for k, want, had in beaten:
        print("   %-56s ships=%-6s -> %s%s"
              % (k, had, want, "  (locked)" if k in LOCK else ""))
    if refused:
        print("")
        print("REFUSED - repairing these would WEAKEN the browser:")
        for k, aval, fval, why in refused:
            print("   %s" % k)
            print("      all.js=%s   firefox.js=%s" % (aval, fval))
            print("      %s" % why)
    if ignored:
        print("")
        print("NOT HARDENING - firefox.js's value is the intended one, left alone:")
        for k, aval, fval, why in ignored:
            print("   %s" % k)
            print("      all.js=%s   firefox.js=%s" % (aval, fval))
            print("      %s" % why)

    body = ffj.read_text(encoding="utf-8", newline="")
    if MARK in body:
        print("")
        print("the repair block is already present - nothing to do")
        return 0
    if not beaten:
        print("")
        print("nothing to repair")
        return 0
    if not args.apply:
        print("")
        print("run again with --apply to append the repair block to")
        print("   %s" % ffj)
        return 1

    ffj.write_text(body.rstrip("\n") + "\n" + block(beaten),
                   encoding="utf-8", newline="\n")
    print("")
    print("appended %d pref(s) to the END of %s" % (len(beaten), ffj.name))
    print("Next: export_session_fixes.py, then rebuild - prefs live in omni.ja.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
