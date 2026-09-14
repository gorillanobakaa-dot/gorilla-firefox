"""Put an accurate SUPERSEDED banner on every older Windows release page.

WHY THIS EXISTS
  2026-09-14: the notes for v155.0.1-win64.3 said "WhatsApp and WebRTC calls now
  work". They did not, and it had not been tested. The two earlier releases
  already carried SUPERSEDED banners - but those banners sent people to .3, the
  build with the false claim. v155.0.1-win64.4 is the first Windows build whose
  calls were verified with a real, logged call.

  Release notes are part of what ships. When a later build corrects an earlier
  one, every older page has to say so, and say what was actually wrong.

THE ENCODING TRAP
  Reading a release body through PowerShell decodes gh's UTF-8 output with the
  console codepage, so the banner's "no entry" emoji comes back as mojibake
  ("â›”"). Editing that text and writing it back would PUBLISH the mojibake. This
  tool reads gh's bytes in Python, decodes UTF-8 explicitly, writes the notes
  file as UTF-8, and re-reads every page afterwards to prove it is clean.

WHAT IT DOES
  - saves each current body to state/release_notes_backup/<tag>.md first
  - replaces an existing leading SUPERSEDED blockquote, or prepends one
  - leaves the rest of each page untouched
  - dry run by default; --apply to edit on GitHub

USAGE
    python "working scripts/supersede_releases.py"
    python "working scripts/supersede_releases.py" --apply
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

BANNERS = {
    "v155.0.1-win64.3": BANNER_3,
    "v155.0.1-win64.2": BANNER_OLD,
    "v155.0.1-win64": BANNER_OLD,
}


def gh_body(tag):
    r = subprocess.run(["gh", "release", "view", tag, "--repo", REPO, "--json", "body"],
                       capture_output=True, timeout=120)
    if r.returncode != 0:
        raise SystemExit("gh release view %s failed: %s"
                         % (tag, r.stderr.decode("utf-8", "replace")))
    return json.loads(r.stdout.decode("utf-8"))["body"]


def rebuild(body, banner):
    lines = body.replace("\r\n", "\n").split("\n")
    if lines and lines[0].startswith("> #") and "SUPERSEDED" in lines[0]:
        i = 0
        while i < len(lines) and lines[i].startswith(">"):
            i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        rest = "\n".join(lines[i:])
    else:
        rest = "---\n\n" + "\n".join(lines)
    if not rest.lstrip().startswith("---"):
        rest = "---\n\n" + rest
    return banner + "\n" + rest


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    backup = ROOT / "state" / "release_notes_backup"
    backup.mkdir(parents=True, exist_ok=True)
    failures = 0
    for tag, banner in BANNERS.items():
        body = gh_body(tag)
        (backup / ("%s.md" % tag)).write_text(body, encoding="utf-8")
        new = rebuild(body, banner)
        print("=" * 70)
        print("%s  (%d -> %d chars)" % (tag, len(body), len(new)))
        for line in new.split("\n")[:6]:
            print("   " + line[:100])
        if not args.apply:
            continue
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md",
                                         delete=False) as fh:
            fh.write(new)
            path = fh.name
        r = subprocess.run(["gh", "release", "edit", tag, "--repo", REPO,
                            "--notes-file", path], capture_output=True, timeout=180)
        os.unlink(path)
        if r.returncode != 0:
            print("   EDIT FAILED: %s" % r.stderr.decode("utf-8", "replace"))
            failures += 1
            continue
        after = gh_body(tag)
        clean = not any(m in after for m in MOJIBAKE)
        ok = after.startswith(banner.split("\n")[0]) and LATEST in after[:2000] and clean
        print("   re-read: %s%s" % ("OK" if ok else "WRONG",
                                    "" if clean else " (mojibake found)"))
        failures += 0 if ok else 1
    if not args.apply:
        print("\ndry run - nothing edited. --apply to publish.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
