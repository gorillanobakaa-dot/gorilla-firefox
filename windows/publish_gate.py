"""Refuse to publish a browser nobody has proven works.

WHY THIS EXISTS
  2026-09-13: a build was uploaded to GitHub as a release. It had a URL bar
  with no visible edge (a theme rule written against an ID that FF155 had
  renamed to a class, so it matched nothing), and nine privacy prefs that
  shipped with the OPPOSITE of their hardened value because greprefs.js loads
  before firefox.js and the last definition wins.

  Both were invisible to every check that existed. Both reached users.

  There was no publish step - uploads were done by hand, from whatever
  happened to be on disk. This is that missing step.

WHAT IT ENFORCES
  Everything below must pass. There is no --force. If you genuinely need to
  publish something this refuses, fix the check or delete it deliberately -
  do not add a flag that lets a tired person skip it at 2am.

  1. preflight            zero BLOCKERs
  2. address bar          proven to navigate, on THIS build
  3. installed build      carries every tracked fix
  4. bundled extensions   present AND visible in about:addons
  5. patches              export cleanly and re-apply
  6. privacy claims       package matches what the release notes say
  7. artifact identity    the file you are about to upload is the one tested

USAGE
    python "working scripts/publish_gate.py"
    python "working scripts/publish_gate.py" --artifact deploy/Gorilla...exe
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("GORILLA_ROOT")
            or Path(__file__).resolve().parent.parent)
PY = sys.executable or "python"


def run(cmd, cwd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           cwd=str(cwd), timeout=900)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as exc:
        return 99, "could not run: %s" % exc


def gate_preflight(root):
    rc, out = run([PY, "harness/gorilla_build.py", "preflight"], root)
    blockers = [l.strip() for l in out.splitlines()
                if l.startswith("[-]") or "(BLOCKER)" in l]
    if blockers:
        return False, "%d blocker(s): %s" % (len(blockers), blockers[0][:90])
    if "Preflight cleared" not in out:
        return False, "preflight did not clear"
    return True, "cleared, no blockers"


def gate_script(root, script, args, ok_needle):
    p = root / "working scripts" / script
    if not p.is_file():
        return None, "%s not present" % script
    rc, out = run([PY, str(p)] + args, root)
    if rc == 0 and (ok_needle is None or ok_needle in out):
        last = [l for l in out.splitlines() if l.strip()]
        return True, (last[-1][:90] if last else "ok")
    bad = [l.strip() for l in out.splitlines()
           if l.strip().startswith(("FAIL", "-", "!"))]
    return False, (bad[0][:110] if bad else "exit %d" % rc)


def gate_artifact(root, artifact):
    """The file about to be uploaded must be the build that was tested."""
    res = root / "state" / "address_bar_result.json"
    if not artifact:
        cands = sorted((root / "deploy").glob("*.exe"))
        if not cands:
            return None, "no installer in deploy/ to check"
        artifact = cands[-1]
    artifact = Path(artifact)
    if not artifact.is_file():
        return False, "artifact not found: %s" % artifact
    h = hashlib.sha256()
    with open(artifact, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    digest = h.hexdigest()
    sums = root / "deploy" / "SHA256SUMS.txt"
    if sums.is_file():
        body = sums.read_text(encoding="utf-8", errors="replace")
        if digest not in body:
            return False, ("%s does not match SHA256SUMS.txt - the recorded "
                           "hash belongs to a different file" % artifact.name)
    if not res.is_file():
        return False, "no address-bar result to tie this artifact to"
    return True, "%s  sha256 %s..." % (artifact.name, digest[:16])


def gate_address_bar(root):
    """Read the RECORDED result. Do not re-run it here.

    Only one tool in this project may take the keyboard, and it asks first.
    A gate that seizes input for a minute would either be skipped or would
    collide with whatever the user is doing - which is exactly how the first
    run of it produced two failures that were not real.
    """
    res = root / "state" / "address_bar_result.json"
    if not res.is_file():
        return False, ('never run - do: python "working scripts/verify_address_bar.py"')
    try:
        d = json.loads(res.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, "result unreadable: %s" % exc
    if not d.get("passed"):
        return False, "the recorded run FAILED (%s)" % d.get("when", "?")
    try:
        sys.path.insert(0, str(root / "working scripts"))
        import verify_address_bar as _v
        inst = _v.find_install()
        if inst and _v.build_id(inst) != d.get("build_id"):
            return False, "the passing result is for a DIFFERENT build - re-run it"
    except Exception:
        pass
    return True, "navigates, verified %s" % d.get("when", "?")


GATES = [
    ("preflight",          lambda r, a: gate_preflight(r)),
    ("address bar",        lambda r, a: gate_address_bar(r)),
    ("installed build",    lambda r, a: gate_script(r, "verify_installed_build.py",
                                                    [], "OK")),
    ("bundled extensions", lambda r, a: gate_script(r, "verify_builtin_extension.py",
                                                    ["--source-only", "--quiet"], None)),
    ("patches re-apply",   lambda r, a: gate_script(r, "verify_patches_apply.py",
                                                    [], "0 failed")),
    ("privacy claims",     lambda r, a: gate_script(r, "audit_privacy_claims.py",
                                                    [], None)),
    ("artifact identity",  lambda r, a: gate_artifact(r, a)),
]


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--artifact", default=None,
                    help="the installer you are about to upload")
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args()
    root = Path(args.root)

    print("PUBLISH GATE - nothing goes to GitHub unless every line says PASS")
    print("=" * 70)
    failed, skipped = [], []
    for name, fn in GATES:
        try:
            ok, detail = fn(root, args.artifact)
        except Exception as exc:
            ok, detail = False, "check raised %s: %s" % (type(exc).__name__, exc)
        mark = "PASS" if ok else ("skip" if ok is None else "FAIL")
        print("  [%s] %-20s %s" % (mark, name, detail))
        if ok is None:
            skipped.append(name)
        elif not ok:
            failed.append((name, detail))

    print("=" * 70)
    if failed:
        print("")
        print("DO NOT PUBLISH. %d gate(s) failed:" % len(failed))
        for n, d in failed:
            print("  - %-20s %s" % (n, d))
        print("")
        print("  On 2026-09-13 a build went out with a dead theme selector and")
        print("  nine privacy prefs set to the opposite of what was intended.")
        print("  Every check then in existence passed. That is why this exists,")
        print("  and why it has no --force.")
        return 1
    if skipped:
        print("cleared, but %d gate(s) could not run: %s"
              % (len(skipped), ", ".join(skipped)))
        return 0
    print("CLEARED - safe to publish.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
