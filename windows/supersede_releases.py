"""Put an accurate SUPERSEDED / KNOWN ISSUES banner on older release pages.

WHY THIS EXISTS
  2026-09-14: the notes for v155.0.1-win64.3 said "WhatsApp and WebRTC calls now
  work". They did not, and it had not been tested. The two earlier Windows
  releases already carried SUPERSEDED banners - but those sent people to .3, the
  build with the false claim. v155.0.1-win64.4 is the first Windows build whose
  calls were verified with a real, logged call.

  The same day the Linux release pages were checked against the commits their
  tags point at. Both Linux .deb downloads (v154.0a1-1 and snapshot-2026-08-12)
  predate BOTH call fixes: no DTLS 1.2 cap (added 2026-09-13, ddc2319) and the
  old AudioContext tweak that forces 48000 Hz on every realtime context
  (media.gorilla.hardware_only_mode defaults to true; fixed 2026-08-26,
  2c67307). There is no newer Linux download to point at, so those pages get a
  KNOWN ISSUES banner instead of SUPERSEDED.

  Release notes are part of what ships. When a later finding corrects an
  earlier page, the page has to say so, and say what is actually wrong.

THE ENCODING TRAP
  Reading a release body through PowerShell decodes gh's UTF-8 output with the
  console codepage, so emoji come back as mojibake. Editing that text and
  writing it back would PUBLISH the mojibake. This tool reads gh's bytes in
  Python, decodes UTF-8 explicitly, writes the notes file as UTF-8, and re-reads
  every page afterwards to prove it is clean.

WHAT IT DOES
  - saves each current body to state/release_notes_backup/<tag>.md first
  - replaces an existing leading SUPERSEDED / KNOWN ISSUES blockquote, or
    prepends one - any OTHER leading notice (the add-ons one) is kept
  - sets the titles listed in TITLES
  - dry run by default; --apply to edit on GitHub; --only TAG to limit

USAGE
    python "working scripts/supersede_releases.py"
    python "working scripts/supersede_releases.py" --apply
    python "working scripts/supersede_releases.py" --apply --only v154.0a1-1
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(os.environ.get("GORILLA_ROOT")
            or Path(__file__).resolve().parent.parent)
REPO = "gorillanobakaa-dot/gorilla-firefox"
LATEST = "v155.0.1-win64.4"
LATEST_URL = "https://github.com/%s/releases/tag/%s" % (REPO, LATEST)
MOJIBAKE = ("â€", "â›", "ðŸ")
OWN_MARKERS = ("SUPERSEDED", "KNOWN ISSUES")

BANNER_OLD = """> # ⛔ SUPERSEDED — do not use this build
>
> **WhatsApp and other WebRTC calls do not work in this release.** They ring
> forever and never connect, with no error shown. It is not your internet. Two
> separate faults cause it: Meta's call relays drop DTLS 1.3 traffic (fixed in
> .3), and a limit of 8 background workers per website leaves WhatsApp's call
> engine waiting in a queue (fixed in .4).
>
> **This build also contacts Google Safe Browsing and Mozilla's captive-portal
> service**, and has Firefox Accounts enabled — eight privacy preferences were
> silently overridden by a later settings file and shipped as the opposite of
> what the notes below claim.
>
> **The address bar also draws no border**, which on a black toolbar makes it
> look missing.
>
> ### \U0001f449 Download [%s](%s) instead. All of these are fixed there, and calls were verified with a real, logged WhatsApp call on that exact build.
>
> *Banner corrected 2026-09-14: it previously pointed to v155.0.1-win64.3, whose calls did not work either.*
""" % (LATEST, LATEST_URL)

BANNER_3 = """> # ⛔ SUPERSEDED — do not use this build
>
> **The notes below say WhatsApp and WebRTC calls now work. They do not, and
> that had not been tested when it was written.** This build fixed one real
> cause (Meta's relays dropping DTLS 1.3), but calls still fail: you hear
> ringing, the other phone never rings and shows "Connecting…", and the call
> drops. The remaining cause was a limit of **8 background workers per
> website** (Firefox's own default is 512): WhatsApp's call engine was left
> waiting in a queue.
>
> One more correction: the "nine privacy settings" below included
> `javascript.options.mem.max`, which is a JavaScript memory cap, not a privacy
> setting — and this build halved it by mistake.
>
> ### \U0001f449 Download [%s](%s) instead. Calls there were verified with a real, logged WhatsApp call on that exact build.
>
> *Corrected 2026-09-14.*
""" % (LATEST, LATEST_URL)

BANNER_LINUX = """> # ⚠ KNOWN ISSUES IN THIS DOWNLOAD — WhatsApp and WebRTC calls
>
> **Calls do not work properly in this build.** Two faults were found after it
> was built. Both are fixed in the source; neither is fixed in this `.deb`.
>
> 1. **Calls ring forever and never connect.** Meta's call relays silently drop
>    DTLS 1.3 traffic, and this build does not cap it. Fixed in source on
>    2026-09-13 (commit `ddc2319`).
>    **Workaround, no rebuild needed:** open `about:config`, set
>    `media.peerconnection.dtls.version.max` to `771`, and restart the browser.
>    This was measured working on Linux.
> 2. **If a call does connect, nobody can hear anything.** This build forces
>    every live audio context to 48000 Hz (under `media.gorilla.hardware_only_mode`,
>    which is on by default), and WhatsApp's call audio needs 16000 Hz. Fixed in
>    source on 2026-08-26 (commit `2c67307`). No settings-only workaround has
>    been tested.
>
> A third setting, `dom.workers.maxPerDomain` = 8, stopped Windows calls
> completely until it was raised to 512 in
> [v155.0.1-win64.4](%s). This build has the same value of 8. Whether it affects
> Linux has **not** been measured yet.
>
> **No rebuilt Linux `.deb` has been published yet.** The fixes are in the
> source that `recreate.sh` builds, but that Linux build path has not been
> test-compiled since they were added.
>
> Both Linux releases publish a file with the same name,
> `gorilla-unleashed_154.0a1-1_amd64.deb`, so a package manager cannot tell
> them apart — check which release page you downloaded from.
>
> *Added 2026-09-14, after checking this release's tagged commit.*
""" % LATEST_URL

BANNERS = {
    "v155.0.1-win64.3": BANNER_3,
    "v155.0.1-win64.2": BANNER_OLD,
    "v155.0.1-win64": BANNER_OLD,
    "v154.0a1-1": BANNER_LINUX,
    "snapshot-2026-08-12": BANNER_LINUX,
}

TITLES = {
    "v155.0.1-win64.3": "SUPERSEDED - Gorilla Unleashed 155.0.1.3 (calls do NOT work - use .4)",
    "v155.0.1-win64.2": "SUPERSEDED - Gorilla Firefox 155.0.1 Windows .2 (calls do not work - use .4)",
    "v155.0.1-win64": "SUPERSEDED - Gorilla Firefox 155.0.1 Windows (calls do not work - use .4)",
    "v154.0a1-1": "Gorilla Unleashed 154 (154.0a1-1) - KNOWN ISSUE: WhatsApp calls broken, see notes",
    "snapshot-2026-08-12": "Snapshot 2026-08-12 - 154.0a1 build 2026-08-11 - KNOWN ISSUE: calls broken, see notes",
}


def gh_release(tag):
    r = subprocess.run(["gh", "release", "view", tag, "--repo", REPO, "--json", "body,name"],
                       capture_output=True, timeout=120)
    if r.returncode != 0:
        raise SystemExit("gh release view %s failed: %s"
                         % (tag, r.stderr.decode("utf-8", "replace")))
    d = json.loads(r.stdout.decode("utf-8"))
    return d["body"], d["name"]


def rebuild(body, banner):
    lines = body.replace("\r\n", "\n").split("\n")
    if lines and lines[0].startswith("> #") and any(m in lines[0] for m in OWN_MARKERS):
        i = 0
        while i < len(lines) and lines[i].startswith(">"):
            i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        rest = "\n".join(lines[i:])
    else:
        rest = "\n".join(lines)
    if not rest.lstrip().startswith("---"):
        rest = "---\n\n" + rest
    return banner + "\n" + rest


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", action="append", default=[], metavar="TAG")
    args = ap.parse_args()
    backup = ROOT / "state" / "release_notes_backup"
    backup.mkdir(parents=True, exist_ok=True)
    failures = 0
    for tag, banner in BANNERS.items():
        if args.only and tag not in args.only:
            continue
        body, name = gh_release(tag)
        (backup / ("%s.md" % tag)).write_text(body, encoding="utf-8")
        new = rebuild(body, banner)
        print("=" * 70)
        print("%s  (%d -> %d chars)   title: %s" % (tag, len(body), len(new), TITLES.get(tag, name)))
        for line in new.split("\n")[:5]:
            print("   " + line[:100])
        if not args.apply:
            continue
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md",
                                         delete=False) as fh:
            fh.write(new)
            path = fh.name
        cmd = ["gh", "release", "edit", tag, "--repo", REPO, "--notes-file", path]
        if tag in TITLES:
            cmd += ["--title", TITLES[tag]]
        r = subprocess.run(cmd, capture_output=True, timeout=180)
        os.unlink(path)
        if r.returncode != 0:
            print("   EDIT FAILED: %s" % r.stderr.decode("utf-8", "replace"))
            failures += 1
            continue
        after, after_name = gh_release(tag)
        clean = not any(m in after for m in MOJIBAKE)
        ok = (after.startswith(banner.split("\n")[0]) and clean
              and after.count(banner.split("\n")[0]) == 1
              and (tag not in TITLES or after_name == TITLES[tag]))
        print("   re-read: %s%s" % ("OK" if ok else "WRONG",
                                    "" if clean else " (mojibake found)"))
        failures += 0 if ok else 1
    if not args.apply:
        print("\ndry run - nothing edited. --apply to publish.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
