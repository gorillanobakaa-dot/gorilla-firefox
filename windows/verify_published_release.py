"""Prove the installer on GitHub is the build that was tested - and is installed.

WHY THIS EXISTS
  2026-09-14, from the user: "you claim ... webrtc works. It does not. ... If you
  hallucinated that, chances are that the last stuff you pushed on the online
  github is hallucinated as well."

  That was answerable only by measurement, done by hand that day:
    1. GitHub's asset digest for the installer
    2. the local deploy/ installer's sha256
    3. the installer UNPACKED, and its omni.ja / browser/omni.ja /
       application.ini compared byte-for-byte with the installed browser
  Later the same day the user asked for the published file to be downloaded
  and installed - the strongest version of the same check.

  "Uploaded" and "the file people get is the file that was tested" are
  different claims. This checks the second.

HOW THE INSTALLER IS UNPACKED
  Firefox's Windows setup.exe is a 7-Zip self-extractor with the payload under
  core/. Windows 10+ ships bsdtar, which reads it: tar -xf setup.exe core/omni.ja.
  No 7-Zip needed.

USAGE
    python "working scripts/verify_published_release.py"                 # latest release
    python "working scripts/verify_published_release.py" --tag v155.0.1-win64.4
    python "working scripts/verify_published_release.py" --download       # fetch from GitHub too
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(os.environ.get("GORILLA_ROOT")
            or Path(__file__).resolve().parent.parent)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_address_bar as vab    # noqa: E402

REPO = "gorillanobakaa-dot/gorilla-firefox"
COMPARE = ["omni.ja", "browser/omni.ja", "application.ini"]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def gh_json(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, timeout=120)
    if r.returncode != 0:
        raise SystemExit("gh api %s failed: %s" % (path, r.stderr.decode("utf-8", "replace")))
    return json.loads(r.stdout.decode("utf-8"))


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", default=None, help="default: the latest release")
    ap.add_argument("--download", action="store_true",
                    help="download the published installer and check THAT file")
    args = ap.parse_args()

    rel = gh_json("repos/%s/releases/%s" % (REPO, ("tags/" + args.tag) if args.tag else "latest"))
    asset = next((a for a in rel["assets"] if a["name"].endswith("-setup.exe")), None)
    if not asset:
        print("release %s has no installer asset" % rel["tag_name"])
        return 1
    published = (asset.get("digest") or "").replace("sha256:", "")
    print("release   %s  (%s)" % (rel["tag_name"], rel["published_at"]))
    print("asset     %s  %d bytes  state=%s" % (asset["name"], asset["size"], asset["state"]))
    print("github    sha256 %s" % (published or "(no digest exposed)"))

    fails = 0
    local = ROOT / "deploy" / asset["name"]
    if local.is_file():
        ls = sha256(local)
        print("deploy/   sha256 %s  %s" % (ls, "MATCH" if ls == published else "DIFFERENT"))
        fails += ls != published
    else:
        print("deploy/   %s not present locally" % asset["name"])

    work = Path(tempfile.mkdtemp(prefix="relcheck-"))
    try:
        subject = local if local.is_file() else None
        if args.download:
            r = subprocess.run(["gh", "release", "download", rel["tag_name"], "--repo", REPO,
                                "--dir", str(work), "--pattern", asset["name"]],
                               capture_output=True, timeout=1800)
            got = work / asset["name"]
            if r.returncode != 0 or not got.is_file():
                print("download  FAILED")
                return 1
            ds = sha256(got)
            print("download  sha256 %s  %s" % (ds, "MATCH" if ds == published else "DIFFERENT"))
            fails += ds != published
            subject = got
        if not subject:
            print("nothing to unpack - pass --download")
            return 1

        out = work / "unpacked"
        out.mkdir()
        subprocess.run(["tar", "-xf", str(subject)] + ["core/" + c for c in COMPARE],
                       cwd=str(out), capture_output=True)
        install = vab.find_install()
        print("")
        print("installer contents vs installed browser (%s):" % install)
        for c in COMPARE:
            a, b = out / "core" / c, (install / c) if install else None
            if not a.is_file():
                print("  %-18s NOT IN INSTALLER (unpack failed?)" % c)
                fails += 1
                continue
            if not b or not b.is_file():
                print("  %-18s not installed" % c)
                fails += 1
                continue
            same = sha256(a) == sha256(b)
            print("  %-18s %s" % (c, "IDENTICAL" if same else "DIFFERENT - the installed "
                                  "browser is not this release"))
            fails += not same
    finally:
        shutil.rmtree(work, ignore_errors=True)

    print("")
    print("RESULT: %s" % ("the published installer is the installed, tested build"
                          if not fails else "%d mismatch(es)" % fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
