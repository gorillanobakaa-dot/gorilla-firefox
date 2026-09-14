"""Find theme rules that select an element which does not exist.

THE BUG THIS FINDS
  2026-09-13. The address bar was reported, twice, to have no cyan
  border. master-redirect.css styled it three times:

      #urlbar-background { border: 1px solid #00FFFF !important; }

  Firefox 155 builds that element as

      <html:div class="urlbar-background"/>        UrlbarInput.mjs:101

  A CLASS. No id anywhere. Every rule matched nothing, so the field drew no
  edge at all and the only border ever seen was Firefox's own focus ring.

  The cruel part: the same file already recorded the rename, near the bottom -
  "FF155 renamed it from an ID to a CLASS, so the theme's #urlbar-background
  rules were dead code". A later rescue block was written against the ID
  anyway. Knowing is not the same as checking.

WHY IT NEEDS A TOOL
  Dead CSS fails silently by construction. No exception, no console warning,
  no build error - the page renders, just without your rule. The only detector
  is a human noticing an absent colour, which is how this one was found, after
  it shipped.

THE TRAP INSIDE THE TOOL
  The first version searched the tree for ="urlbar-background" and found
  class="urlbar-background", so it declared the selector RESOLVED - reporting
  the very defect it was built to catch as fine. The pattern must be id="...".
  Verified by reintroducing the bug: 4 dead selectors with it, 3 without.

USAGE
    python "working scripts/fix_theme_dead_selectors.py"
    python "working scripts/fix_theme_dead_selectors.py" --suggest
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("GORILLA_ROOT")
            or Path(__file__).resolve().parent.parent)

DEFAULT_SHEETS = [
    "browser/themes/shared/master-redirect.css",
    "browser/themes/shared/findbar.css",
]


def rg(pattern, src, *paths):
    try:
        r = subprocess.run(["rg", "-l", "--no-messages", pattern] + list(paths),
                           cwd=str(src), capture_output=True, text=True,
                           timeout=180)
        return [l for l in (r.stdout or "").splitlines() if l.strip()]
    except Exception:
        return None


def id_selectors(css_text):
    """Every #foo used as a selector, excluding hex colours."""
    body = re.sub(r"/\*.*?\*/", "", css_text, flags=re.S)   # prose is not code
    out = set()
    for m in re.finditer(r"#([A-Za-z][\w-]*)", body):
        tok = m.group(1)
        if re.fullmatch(r"[0-9A-Fa-f]{3,8}", tok):          # #FFC0CB is a colour
            continue
        out.add(tok)
    return sorted(out)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--sheet", action="append", default=None,
                    help="stylesheet to check, relative to src/ (repeatable)")
    ap.add_argument("--suggest", action="store_true",
                    help="for each dead id, look for a class of the same name")
    args = ap.parse_args()

    root = Path(args.root)
    src = root / "src"
    if not src.is_dir():
        raise SystemExit("no source tree at %s" % src)
    sheets = args.sheet or DEFAULT_SHEETS

    total_dead = 0
    for rel in sheets:
        p = src / rel
        if not p.is_file():
            print("skip (absent): %s" % rel)
            continue
        ids = id_selectors(p.read_text(encoding="utf-8", errors="replace"))
        print("")
        print("%s" % rel)
        print("   %d id selector(s)" % len(ids))
        dead = []
        for i in ids:
            # MUST be id=, not just ="...". A class of the same name is
            # exactly the failure mode being hunted.
            hits = rg('id="%s"' % i, src, "browser", "toolkit")
            if hits is None:
                print("   ripgrep unavailable - cannot check")
                return 2
            if not hits:
                dead.append(i)
        if not dead:
            print("   all resolve")
            continue
        total_dead += len(dead)
        for i in dead:
            print("   DEAD  #%s" % i)
            if args.suggest:
                cls = rg('class="[^"]*\\b%s\\b' % re.escape(i), src,
                         "browser", "toolkit")
                if cls:
                    print("         a CLASS of that name exists - try .%s" % i)
                    for f in cls[:3]:
                        print("            %s" % f)
                else:
                    print("         no class of that name either; the element")
                    print("         may be built in JS, or the rule is obsolete")

    print("")
    print("=" * 68)
    if total_dead:
        print("%d dead selector(s)." % total_dead)
        print("")
        print("Do NOT bulk-rewrite them. Open the .mjs/.xhtml that builds each")
        print("element and use the selector it actually has. And prefer")
        print("OUTLINE over border - an outline does not participate in layout,")
        print("which is this project's CSS invariant.")
        return 1
    print("every theme id selector resolves to a real element")
    return 0


if __name__ == "__main__":
    sys.exit(main())
