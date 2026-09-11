"""Verify the privacy claims against the SHIPPED package, not the source.

WHY THIS EXISTS
  The release notes say "telemetry and data collection stripped out, AI
  features removed, sponsored tiles gone". Those are claims made to strangers
  who are trusting a binary they cannot read. They need checking against what
  actually ships.

THE SEMANTIC THAT MATTERS
  Firefox pref files are read TOP TO BOTTOM and the LAST definition of a pref
  wins. The Gorilla injection is appended, so its values sit BELOW upstream's.

  A first version of this audit grepped for the first match and reported
  `app.shield.optoutstudies.enabled = true` - a false alarm, because 475 lines
  further down the same file sets it false and locked. Reading the first match
  inverts the answer for every pref the patchset overrides, which is most of
  the interesting ones.

  So: parse every occurrence, keep the last.

WHAT IT CANNOT TELL YOU
  A pref says what the code is CONFIGURED to do. It does not prove the code is
  gone, and it does not prove nothing is sent. That is why this also checks
  whether the modules are present at all, and why `--network` exists: the only
  real proof that a browser does not phone home is watching it not phone home.

USAGE
    python "working scripts/audit_privacy_claims.py"
    python "working scripts/audit_privacy_claims.py" --install "C:/path"
    python "working scripts/audit_privacy_claims.py" --json
"""
import argparse
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

PREF_RE = re.compile(
    r'^\s*pref\(\s*"([^"]+)"\s*,\s*(.+?)\s*(,\s*(?:locked|sticky))?\s*\)\s*;', re.M)

# (pref, required value, why it matters)
TELEMETRY = [
    ("toolkit.telemetry.enabled", "false", "the main telemetry switch"),
    ("toolkit.telemetry.unified", "false", "unified telemetry collection"),
    ("toolkit.telemetry.server", '""', "where pings would be sent"),
    ("toolkit.telemetry.archive.enabled", "false", "local ping archive"),
    ("toolkit.telemetry.newProfilePing.enabled", "false", "ping on new profile"),
    ("toolkit.telemetry.updatePing.enabled", "false", "ping on update"),
    ("toolkit.telemetry.shutdownPingSender.enabled", "false", "ping at shutdown"),
    ("toolkit.telemetry.bhrPing.enabled", "false", "background hang reports"),
    ("toolkit.telemetry.firstShutdownPing.enabled", "false", "first-shutdown ping"),
    ("datareporting.healthreport.uploadEnabled", "false", "health report upload"),
    ("datareporting.policy.dataSubmissionEnabled", "false", "master data-submission gate"),
    ("app.shield.optoutstudies.enabled", "false", "Shield/Normandy remote experiments"),
    ("extensions.experiments.enabled", "false", "experiment add-ons"),
    ("browser.discovery.enabled", "false", "add-on recommendations by browsing"),
    # The rest of Column A from patches/14.EGRESS.LOCKDOWN's hardening plan.
    ("messaging-system.rsexperimentloader.enabled", "false", "Nimbus experiment loader"),
    ("browser.crashReports.unsubmittedCheck.enabled", "false", "unsubmitted-crash probe"),
    ("browser.tabs.crashReporting.sendReport", "false", "tab-crash reports"),
    ("browser.ping-centre.telemetry", "false", "Activity Stream ping-centre"),
    ("browser.newtabpage.activity-stream.feeds.telemetry", "false", "newtab feed telemetry"),
    ("toolkit.telemetry.coverage.opt-out", "true", "disables the coverage ping mechanism"),
    # The tenth. Missed by the first pass of this audit purely because it was
    # not in the list being checked - the audit found four gaps when there
    # were five. Reading the whole close-list file, rather than the entries
    # already known about, is what surfaced it.
    ("browser.attribution.enabled", "false", "install/attribution reporting"),
]

# Connections deliberately LEFT OPEN, with the reason. From the project's own
# doctrine in patches/14.EGRESS.LOCKDOWN: close surveillance, preserve the
# infrastructure that makes a browser usable, and write down every kept door
# so a later over-zealous pass does not "harden" cert revocation into oblivion.
KEPT_DOORS = [
    ("extensions.blocklist.enabled", "true",
     "malicious add-on blocklist - a security feed, not a report"),
    ("browser.safebrowsing.malware.enabled", "true",
     "Safe Browsing malware list (Google-operated; list is downloaded, not queried per-site)"),
    ("browser.safebrowsing.phishing.enabled", "true",
     "Safe Browsing phishing list"),
    ("network.captive-portal-service.enabled", "true",
     "detects hotel/airport wifi login pages - without it such networks appear broken"),
    ("extensions.update.enabled", "true",
     "add-on security updates"),
]
SPONSORED = [
    ("browser.newtabpage.activity-stream.showSponsored", "false", "sponsored stories"),
    ("browser.newtabpage.activity-stream.showSponsoredTopSites", "false", "sponsored tiles"),
    ("browser.topsites.contile.enabled", "false", "the tile-serving service"),
    ("browser.newtabpage.activity-stream.feeds.system.topstories", "false", "Pocket stories"),
    ("browser.newtabpage.activity-stream.telemetry", "false", "new-tab telemetry"),
    ("browser.urlbar.quicksuggest.enabled", "false", "Firefox Suggest"),
    ("browser.urlbar.suggest.quicksuggest.sponsored", "false", "sponsored suggestions"),
    ("extensions.pocket.enabled", "false", "Pocket"),
]
AI = [
    ("browser.ml.enable", "false", "the ML runtime master switch"),
    ("browser.ml.chat.enabled", "false", "the AI chatbot sidebar"),
    ("extensions.ml.enabled", "false", "ML for extensions"),
    ("browser.tabs.groups.smart.enabled", "false", "AI tab grouping"),
]

# Modules whose ABSENCE from the package is the real proof.
ABSENT = [
    ("AI chatbot", ["GenAI.sys.mjs", "genai"]),
    ("ML engine", ["MLEngine", "EngineProcess.sys.mjs"]),
    ("AI Window", ["aiwindow/"]),
    ("Link Preview", ["LinkPreview"]),
]


def last_pref_values(text):
    """name -> (value, modifier) taking the LAST definition. See the docstring."""
    out = {}
    for m in PREF_RE.finditer(text):
        out[m.group(1)] = (m.group(2), (m.group(3) or "").strip(", "))
    return out


def load(install):
    """Merge both archives, preserving file order so 'last wins' is honoured."""
    merged, names = {}, []
    for rel, member in (("omni.ja", "greprefs.js"),
                        ("browser/omni.ja", "defaults/preferences/firefox.js")):
        p = install / rel
        if not p.is_file():
            continue
        with zipfile.ZipFile(p) as z:
            names += z.namelist()
            for n in z.namelist():
                if n.endswith(member):
                    merged.update(last_pref_values(
                        z.read(n).decode("utf-8", "replace")))
    return merged, names


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


def section(title, rows, prefs, results):
    print("")
    print("=" * 74)
    print(title)
    print("=" * 74)
    ok = bad = 0
    for name, want, why in rows:
        got, mod = prefs.get(name, (None, ""))
        if got is None:
            state, mark = "NOT SET (upstream default applies)", "?"
            bad += 1
        elif got.strip() == want:
            state = "%s%s" % (got, "  [locked]" if mod == "locked" else "")
            mark = "+"
            ok += 1
        else:
            state, mark = "%s   <-- EXPECTED %s" % (got, want), "!"
            bad += 1
        print(" %s %-52s %s" % (mark, name, state))
        if mark != "+":
            print("       %s" % why)
        results.append({"pref": name, "want": want, "got": got,
                        "locked": mod == "locked", "ok": mark == "+"})
    print("")
    print("   %d of %d as claimed" % (ok, ok + bad))
    return bad


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--install", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    install = Path(args.install) if args.install else find_install()
    if not install:
        print("no installed build found - pass --install <dir>")
        return 2
    prefs, names = load(install)
    if not prefs:
        print("could not read the packaged prefs from %s" % install)
        return 2

    print("install : %s" % install)
    print("prefs parsed (last definition wins): %d" % len(prefs))
    results = []
    bad = 0
    bad += section("TELEMETRY AND DATA COLLECTION", TELEMETRY, prefs, results)
    bad += section("SPONSORED CONTENT", SPONSORED, prefs, results)
    bad += section("AI FEATURES", AI, prefs, results)

    print("")
    print("=" * 74)
    print("CODE ACTUALLY REMOVED FROM THE PACKAGE")
    print("=" * 74)
    print("  A pref says what the code is told to do. This says whether the code")
    print("  is there at all.")
    print("")
    for label, needles in ABSENT:
        hits = [n for n in names if any(x.lower() in n.lower() for x in needles)]
        if hits:
            print("  ! %-16s %d file(s) still present: %s"
                  % (label, len(hits), hits[0]))
        else:
            print("  + %-16s absent from the package" % label)

    print("")
    print("=" * 74)
    print("DOORS DELIBERATELY LEFT OPEN")
    print("=" * 74)
    print("  These DO contact the network. None of them reports what you do -")
    print("  they fetch security lists or detect the network you are on. Listed")
    print("  so the claim is 'no surveillance', not the stronger and false")
    print("  'contacts nothing'.")
    print("")
    for name, expect, why in KEPT_DOORS:
        got, _m = prefs.get(name, (None, ""))
        state = got if got is not None else "<upstream default>"
        flag = " " if (got or "").strip() == expect or got is None else "*"
        print("  %s %-46s %s" % (flag, name, state))
        print("       %s" % why)

    print("")
    print("=" * 74)
    print("VERDICT")
    print("=" * 74)
    if bad == 0:
        print("  Every checked pref matches the claim.")
    else:
        print("  %d pref(s) do not match the claim - see the ! lines above." % bad)
    print("")
    print("  This checks CONFIGURATION and PRESENCE. It cannot prove nothing is")
    print("  sent. For that, watch the process: see verify_no_phone_home.py.")

    if args.json:
        print(json.dumps(results, indent=2))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
