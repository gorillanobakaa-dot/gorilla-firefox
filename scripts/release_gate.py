#!/usr/bin/env python3
# Version: 1.0.0 · updated 26-09-14-22-30
"""
Refuse to ship a browser that has quietly lost a proven fix.

LAYMAN
  Every fix in this list cost real time to find, and each one is invisible
  once it is working: the browser looks completely normal without it, right
  up until a call fails. That is exactly how they get dropped during an
  upgrade to a new Firefox version, and it has already happened.

  This script checks the FINISHED browser, not the recipe. It is wired into
  the packaging step, so a .deb that has lost one of these cannot be built by
  accident.

DEVELOPER
  Checks the BUILT ARTIFACT (dist/bin) or a packaged .deb, and cross-checks
  it against the source tree. Source-only gates miss the failure mode found
  on 2026-09-14: the source was correct, the package was built from a stale
  objdir, and the running browser only worked because files had been copied
  into place by hand. Source and package must agree, and the binary must not
  predate the code it claims to contain.

  Exit 0 = every gate passed. Exit 1 = at least one failed. Exit 2 = misuse.

USAGE
  release_gate.py --dist  <objdir>/dist/bin  [--src <source tree>]
  release_gate.py --deb   path/to/package.deb
"""
import argparse, os, re, subprocess, sys, tempfile, shutil

# Every entry is a fix that was proven live and is invisible when absent.
REQUIRED_PREFS = [
    ("dom.workers.maxPerDomain", "512",
     "WhatsApp runs its crypto and WASM audio in Web Workers. At 8 the pool "
     "starves during call setup and the call never starts: getUserMedia was "
     "never called, measured 0 vs 18 after the fix. Cost three days because "
     "the symptom looked like a transport failure. Convicted live 2026-08-27 "
     "with two calls, the second on this pref alone."),
    ("media.peerconnection.dtls.version.max", "771",
     "Meta's relays complete a DTLS 1.3 handshake and then silently drop "
     "every application-data record. Convicted live 2026-08-26, capture "
     "wa-call3. Re-proven on 155.0-3, 11 client setups, none offered 1.3."),
]

REQUIRED_FONTS = ["segoeui.ttf", "segoeuib.ttf", "seguisb.ttf", "SegUIVar.ttf",
                  "consola.ttf", "YuGothB.ttc", "YuGothR.ttc"]

# Fixes that are not prefs. Same standing as REQUIRED_PREFS: each was proven
# live, each is invisible when absent, each has already been lost once.
REQUIRED_FIXES = {
 "audiocontext":
    "AudioContext must honour an explicitly requested sample rate. The old "
    "form forced 48000 Hz for every realtime context, so WhatsApp's 16 kHz "
    "WASM call audio was silently resampled and the other person heard "
    "nothing. Convicted live 2026-08-26 by a WebAudioAPI:5 capture. The rule "
    "is honor or throw, NEVER silently substitute a page-requested rate.",
 "ublock":
    "uBlock Origin must be bundled AND registered in the VISIBLE built-in "
    "location. This build blocks every add-on install route on purpose, so a "
    "user cannot add one back. A first attempt registered it via "
    "built_in_addons.json: it loaded and ran, and was invisible in "
    "about:addons with no toolbar button, so its settings, filter lists and "
    "on/off switch were unreachable. Working and invisible is not working. "
    "The 155 line then shipped with no blocker at all until 155.0-3, while "
    "the README promised one.",
}

UBLOCK_ID = "uBlock0@raymondhill.net"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FAILS = []
PASSES = []

def ok(gate, msg):   PASSES.append((gate, msg))
def bad(gate, msg, why=""): FAILS.append((gate, msg, why))

def read(p):
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()

def pref_value(txt, name):
    m = re.search(r'pref\(\s*"%s"\s*,\s*([^),]+)' % re.escape(name), txt)
    return m.group(1).strip() if m else None

# ---------------------------------------------------------------- gates ----
def gate_prefs(dist, label):
    """PREF-001: the proven prefs are in the SHIPPED pref file."""
    pf = os.path.join(dist, "browser/defaults/preferences/firefox.js")
    if not os.path.exists(pf):
        bad("PREF-001", "no shipped pref file in %s" % label)
        return
    txt = read(pf)
    for name, want, why in REQUIRED_PREFS:
        got = pref_value(txt, name)
        if got is None:
            bad("PREF-001", "%s is not set at all in %s" % (name, label), why)
        elif got != want:
            bad("PREF-001", "%s is %s, must be %s, in %s" % (name, got, want, label), why)
        else:
            ok("PREF-001", "%s = %s" % (name, want))

def gate_source_agrees(dist, src):
    """PREF-002: the package and the source agree. Catches a stale objdir."""
    sf = os.path.join(src, "browser/app/profile/firefox.js")
    df = os.path.join(dist, "browser/defaults/preferences/firefox.js")
    if not (os.path.exists(sf) and os.path.exists(df)):
        return
    stxt, dtxt = read(sf), read(df)
    for name, _want, why in REQUIRED_PREFS:
        s, d = pref_value(stxt, name), pref_value(dtxt, name)
        if s != d:
            bad("PREF-002",
                "%s is %s in the source but %s in the build" % (name, s, d),
                "The package was built from a stale objdir, or the build output "
                "was edited by hand. Rebuild; do not patch the output. " + why)
        else:
            ok("PREF-002", "%s agrees between source and build" % name)

def gate_audiocontext(src):
    """CODE-001: an explicitly requested AudioContext rate is honoured."""
    f = os.path.join(src, "dom/media/webaudio/AudioContext.cpp")
    if not os.path.exists(f):
        return
    txt = read(f)
    m = re.search(r"GetSampleRateForAudioContext\([^)]*\)\s*\{(.*?)\n\}", txt, re.S)
    if not m:
        bad("CODE-001", "GetSampleRateForAudioContext not found")
        return
    body = m.group(1)
    early = re.search(r"if\s*\(\s*aIsOffline\s*\|\|\s*aSampleRate\s*!=\s*0\.0\s*\)\s*\{?\s*return\s+aSampleRate", body)
    if not early:
        bad("CODE-001", "an explicitly requested sample rate is NOT honoured at all",
            REQUIRED_FIXES["audiocontext"])
        return
    if "48000" in body and body.index("48000") < body.index(early.group(0)):
        bad("CODE-001", "48000 is forced BEFORE the explicit-rate check",
            REQUIRED_FIXES["audiocontext"])
        return
    ok("CODE-001", "explicit sample rates are honoured before any override")

def gate_stale_binary(dist, src):
    """STALE-001: libxul must not predate the code it claims to contain."""
    xul = os.path.join(dist, "libxul.so")
    if not os.path.exists(xul):
        return
    xt = os.path.getmtime(xul)
    watched = ["dom/media/webaudio/AudioContext.cpp",
               "dom/media/platforms/PDMFactory.cpp"]
    for rel in watched:
        f = os.path.join(src, rel)
        if os.path.exists(f) and os.path.getmtime(f) > xt:
            bad("STALE-001", "%s is newer than libxul.so" % rel,
                "The binary was linked before this source change. Whatever the "
                "source says, the shipped browser does not contain it. Rebuild.")
            return
    ok("STALE-001", "libxul.so is newer than the source it is gated on")

def gate_ublock(dist, label):
    """EXT-001: uBlock is bundled, registered, and in the VISIBLE location.

    Presence is not enough. Registered in the wrong built-in location it runs
    but cannot be seen or switched off, which in a browser that blocks add-on
    installs is worse than absent.
    """
    man = os.path.join(dist, "browser/chrome/browser/gorilla-addons/ublock-origin/manifest.json")
    reg = os.path.join(dist, "browser/modules/GorillaBuiltinExtensions.sys.mjs")

    if not os.path.exists(man):
        bad("EXT-001", "uBlock Origin is not bundled in %s" % label,
            REQUIRED_FIXES["ublock"]); return
    ok("EXT-001", "uBlock Origin payload is bundled")

    if not os.path.exists(reg):
        bad("EXT-001", "the payload is there but nothing registers it in %s" % label,
            REQUIRED_FIXES["ublock"]); return
    rtxt = read(reg)
    if UBLOCK_ID not in rtxt:
        bad("EXT-001", "the registration module does not mention %s" % UBLOCK_ID,
            REQUIRED_FIXES["ublock"]); return
    if "maybeInstallBuiltinAddon" not in rtxt:
        bad("EXT-001", "uBlock is not registered in the VISIBLE built-in location",
            REQUIRED_FIXES["ublock"]); return
    ok("EXT-001", "registered via maybeInstallBuiltinAddon, so it appears in about:addons")

    # the version the payload actually is, against the version that was pinned
    try:
        import json
        mv = json.load(open(man, encoding="utf-8")).get("version")
    except Exception:
        mv = None
    if mv:
        ok("EXT-001", "bundled uBlock Origin version %s" % mv)
    return mv

def gate_ublock_pin(dist, repo_root, bundled_version):
    """EXT-002: the bundled payload matches the version this repo pinned."""
    if not (repo_root and bundled_version):
        return
    pin = os.path.join(repo_root, "state/builtin_extensions.json")
    if not os.path.exists(pin):
        return
    try:
        import json
        d = json.load(open(pin, encoding="utf-8"))
    except Exception:
        return
    for e in d.get("extensions", []):
        if e.get("id") == UBLOCK_ID:
            want = e.get("version")
            if want and want != bundled_version:
                bad("EXT-002",
                    "package has uBlock %s but this repo pins %s" % (bundled_version, want),
                    "The payload is fetched, not committed. A silent version "
                    "drift means the published source and the published "
                    "package describe different browsers.")
            else:
                ok("EXT-002", "bundled version matches the pin in state/")
            return

def gate_fonts(dist, label):
    """FONT-001: the fonts the look depends on are in the package."""
    d = os.path.join(dist, "fonts")
    missing = [f for f in REQUIRED_FONTS if not os.path.exists(os.path.join(d, f))]
    if missing:
        bad("FONT-001", "missing from %s: %s" % (label, ", ".join(missing)),
            "These are a wanted part of the build. They are fetched, not "
            "committed, so a fresh checkout that skips "
            "get-microsoft-fonts.sh silently produces a package without them.")
    else:
        ok("FONT-001", "all %d Microsoft fonts present" % len(REQUIRED_FONTS))

# ----------------------------------------------------------------- main ----
def run(dist, src, label, repo_root=None):
    gate_prefs(dist, label)
    bundled = gate_ublock(dist, label)
    gate_ublock_pin(dist, repo_root, bundled)
    gate_fonts(dist, label)
    if src:
        gate_source_agrees(dist, src)
        gate_audiocontext(src)
        gate_stale_binary(dist, src)

def main():
    ap = argparse.ArgumentParser(description="Refuse to ship a browser missing a proven fix.")
    ap.add_argument("--dist", help="an objdir dist/bin directory")
    ap.add_argument("--deb",  help="a packaged .deb")
    ap.add_argument("--src",  help="the source tree, enables the cross-checks")
    a = ap.parse_args()
    if not (a.dist or a.deb):
        ap.error("give --dist or --deb")

    tmp = None
    try:
        if a.deb:
            if not os.path.exists(a.deb):
                print("FATAL: no such .deb: %s" % a.deb); return 2
            tmp = tempfile.mkdtemp(prefix="release_gate.")
            subprocess.run(["dpkg-deb", "-x", a.deb, tmp], check=True)
            dist = os.path.join(tmp, "usr/lib/gorilla-unleashed")
            if not os.path.isdir(dist):
                print("FATAL: %s does not contain usr/lib/gorilla-unleashed" % a.deb); return 2
            run(dist, a.src, os.path.basename(a.deb), REPO_ROOT)
        else:
            if not os.path.isdir(a.dist):
                print("FATAL: no such dist/bin: %s" % a.dist); return 2
            run(a.dist, a.src, "the build", REPO_ROOT)
    finally:
        if tmp: shutil.rmtree(tmp, ignore_errors=True)

    for g, m in PASSES:
        print("  pass  %-10s %s" % (g, m))
    if not FAILS:
        print("\nAll %d gates passed." % len(PASSES))
        return 0
    print("")
    for g, m, why in FAILS:
        print("  FAIL  %-10s %s" % (g, m))
        if why:
            for line in re.findall(r".{1,68}(?:\s|$)", why):
                if line.strip(): print("        %s" % line.strip())
    print("\n%d gate(s) FAILED. This package must not be published." % len(FAILS))
    return 1

if __name__ == "__main__":
    sys.exit(main())
