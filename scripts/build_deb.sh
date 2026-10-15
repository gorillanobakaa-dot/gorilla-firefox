#!/usr/bin/env bash
# =============================================================================
# build_deb.sh — package a built Gorilla Unleashed dist/bin into a .deb
#
# 🧸 LAYMAN: takes the browser we just compiled and wraps it into a single
#    installable file (a .deb) — the thing a Debian/Ubuntu user double-clicks
#    (or `sudo apt install ./file.deb`) to get Gorilla Unleashed on their menu.
#
# 💻 DEVELOPER: stages dist/bin into the deb_template layout under
#    usr/lib/gorilla-unleashed/, refreshes DEBIAN/control (version +
#    Installed-Size), fixes the about-logo branding, and runs dpkg-deb.
#    Reproducible: same inputs -> same package tree. No sudo needed
#    (--root-owner-group makes root:root ownership without being root).
#
# USAGE:  build_deb.sh [VERSION] [DIST_BIN] [OUT_DIR]
#   VERSION   default: read from application.ini (e.g. 154.0a1) + "-1"
#   DIST_BIN  default: $HOME/firefox-src/obj-x86_64-pc-linux-gnu/dist/bin
#   OUT_DIR   default: FIrefox.154.Work/release
# =============================================================================
set -euo pipefail

DIST_BIN="${2:-$HOME/firefox-src/obj-x86_64-pc-linux-gnu/dist/bin}"
OUT_DIR="${3:-$PWD/release}"
TEMPLATE="${4:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/deb_template}"
ICON_MASTER="$TEMPLATE/usr/share/icons/hicolor/1024x1024/apps/gorilla-unleashed.png"

[ -d "$DIST_BIN" ]  || { echo "FATAL: dist/bin not found: $DIST_BIN" >&2; exit 1; }
[ -x "$DIST_BIN/firefox" ] || { echo "FATAL: no firefox binary in $DIST_BIN" >&2; exit 1; }
[ -d "$TEMPLATE" ]  || { echo "FATAL: deb_template missing: $TEMPLATE" >&2; exit 1; }

# Version: default from the built binary, so the package can never claim a
# version the artifact doesn't actually carry.
if [ -n "${1:-}" ]; then VERSION="$1"; else
  BINVER=$(sed -n 's/^Version=//p' "$DIST_BIN/application.ini" | head -1)
  VERSION="${BINVER:-154.0a1}-1"
fi
BUILDID=$(sed -n 's/^BuildID=//p' "$DIST_BIN/application.ini" | head -1)
PKG="gorilla-unleashed_${VERSION}_amd64"
STAGE="$OUT_DIR/$PKG"

# =============================================================================
# RELEASE GATE - refuse to package a browser that has lost a proven fix
#
# LAYMAN: before wrapping the browser into an installable file, check that the
#    fixes that took days to find are still in it. Each one is invisible when
#    missing: the browser looks perfectly normal until a call fails.
#
# DEVELOPER: scripts/release_gate.py checks the BUILT ARTIFACT and cross-checks
#    it against the source. It lives in this repository and needs nothing
#    outside it, so a clone and a future version port inherit it.
#
#    WHY THIS EXISTS: on 2026-09-14 the published source could not rebuild the
#    published browser. The .deb on disk was packaged from a stale objdir, and
#    the only working browser existed as files copied into place by hand. The
#    pref that makes WhatsApp calls work was 8 in the patch set and 512 in the
#    running browser, and nothing detected it. A source-only check would have
#    passed.
#
#    Skip deliberately with GORILLA_SKIP_RELEASE_GATE=1, never silently.
# =============================================================================
GATE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/release_gate.py"
if [ "${GORILLA_SKIP_RELEASE_GATE:-0}" = "1" ]; then
  echo "   release gate: SKIPPED by GORILLA_SKIP_RELEASE_GATE=1"
elif [ ! -f "$GATE" ]; then
  echo "FATAL: release gate missing: $GATE" >&2
  echo "       Refusing to package. Restore it or set GORILLA_SKIP_RELEASE_GATE=1." >&2
  exit 1
elif ! command -v python3 >/dev/null 2>&1; then
  echo "FATAL: python3 is required to run the release gate." >&2; exit 1
else
  echo "== release gate =="
  GATE_SRC="${SRC_TREE:-$(cd "$DIST_BIN/../../.." 2>/dev/null && pwd)}"
  if [ -n "$GATE_SRC" ] && [ -f "$GATE_SRC/browser/app/profile/firefox.js" ]; then
    python3 "$GATE" --dist "$DIST_BIN" --src "$GATE_SRC" || {
      echo "Refusing to build a package that has lost a proven fix." >&2; exit 1; }
  else
    python3 "$GATE" --dist "$DIST_BIN" || {
      echo "Refusing to build a package that has lost a proven fix." >&2; exit 1; }
  fi
fi

echo "== Gorilla Unleashed .deb builder =="
echo "   version : $VERSION   (buildid $BUILDID)"
echo "   dist    : $DIST_BIN"
echo "   stage   : $STAGE"

rm -rf "$STAGE"; mkdir -p "$STAGE"
# 1. skeleton from template (DEBIAN scripts, .desktop, icons) — but NOT its
#    placeholder usr/lib/gorilla-unleashed contents.
rsync -a --exclude 'usr/lib/gorilla-unleashed/' "$TEMPLATE"/ "$STAGE"/
mkdir -p "$STAGE/usr/lib/gorilla-unleashed"

# 2. the browser itself.
#    The unpacked dev build's dist/bin symlinks into the source tree; `-L` dereferences
#    those into REAL files so the package is self-contained (plain `rsync -a` would ship
#    symlinks that dangle on the user's machine). Drop dev-only cruft + the broken build
#    symlinks (nsinstall/rapl). The bundled fonts — INCLUDING the Microsoft set — SHIP:
#    this is the owner's documented, since-v152 bundled-font feature (ttf-ms-win-auto
#    pattern; fonts sourced from Microsoft's own Win11 eval edition, legal question long
#    settled by the owner, zero GitHub complaints). See memory `ms-fonts-owner-feature`.
#    DO NOT strip them and DO NOT invent font-licensing policy here.
rsync -aL --delete \
  --exclude 'tmp/' --exclude '*.log' --exclude '.cache/' --exclude 'crashreporter*' \
  --exclude 'nsinstall' --exclude 'rapl' --exclude '.lldbinit' \
  "$DIST_BIN"/ "$STAGE/usr/lib/gorilla-unleashed"/

# 2b. scrub the builder's home path out of GENERATED TEXT files (about:buildconfig,
#     RFPTarget generated refs, etc.). grep -I = text files only (never touch binaries).
#     Cosmetic hygiene: a public binary shouldn't advertise the builder's home-dir layout.
grep -rlIF '/home/gorilla' "$STAGE/usr/lib/gorilla-unleashed" 2>/dev/null | while read -r f; do
  sed -i 's#/home/gorilla#/builddir#g' "$f"
done

# 2c. STRIP symbols from shipped binaries — release hygiene. Mozilla ships stripped
#     (their libxul is ~176MB stripped; ours was 246MB unstripped = +50MB of .symtab that
#     end users never use). strip -s removes the symbol table only; CODE is untouched, and
#     the source tree rebuilds symbols anytime. Biggest single size win in the package.
find "$STAGE/usr/lib/gorilla-unleashed" -type f \( -name '*.so' -o -name '*.so.*' \) -exec strip -s {} + 2>/dev/null || true
for bin in firefox glxtest vaapitest plugin-container updater pingsender; do
  f="$STAGE/usr/lib/gorilla-unleashed/$bin"; [ -f "$f" ] && strip -s "$f" 2>/dev/null || true
done

# 3. branding: about-logo is shipped AS BUILT (D-157-35, one master). Until 2026-10-15 this step regenerated it here:
#    a 500px about-logo.png over the build's 1400px master and an extra 1000px about-logo@2x.png, written for the
#    154/155 one-PNG doctrine. D-157-35 (2026-10-07) made ONE 1400px master, linked by every page and decoded once,
#    and retired the @2x copy; this step undid that in every .deb (the blurry 500px gorilla of the first 158 install,
#    and the register's omni_absent FAIL on about-logo@2x.png). The picture now comes only from the tree, checked by
#    fieldkit preflight `binary-patches` and the package check `about-logo is the tree's master`.
# the branding folder of the tree that was built (hicolor icons below, the display name further down)
BR="${5:-$(cd "$DIST_BIN/../../.." 2>/dev/null && pwd)/browser/branding/gorilla}"
# hicolor app icon sizes from the branding set (for the .desktop Icon= entry)
for sz in 16 22 24 32 48 64 128 256; do
  src="$BR/default${sz}.png"
  [ -f "$src" ] || continue
  d="$STAGE/usr/share/icons/hicolor/${sz}x${sz}/apps"; mkdir -p "$d"
  cp "$src" "$d/gorilla-unleashed.png" 2>/dev/null || true
done
# APP-GRID ICON FIX — the template's 1024x1024 slot is the RAW vault master
# (2598x2626, NON-SQUARE) so GNOME renders it wrong/small in the app grid. Regenerate
# proper SQUARE large icons with the CANONICAL command from wayland_dual_icon_bug_fixer.sh
# (see the icon pipeline notes): fuzz-trim the
# transparent padding, Lanczos-fit, then center-pad to an exact NxN square. Never copy a
# raw non-square master into a size dir.
if command -v magick >/dev/null; then
  for sz in 512 1024; do
    d="$STAGE/usr/share/icons/hicolor/${sz}x${sz}/apps"; mkdir -p "$d"
    magick "$ICON_MASTER" -fuzz 5% -trim -filter Lanczos -resize "${sz}x${sz}" \
      -background none -gravity center -extent "${sz}x${sz}" -quality 95 \
      "$d/gorilla-unleashed.png"
  done
  echo "   app-grid icon: regenerated square 512+1024 (Lanczos) from master"
else
  echo "WARN: magick missing — 1024 app-grid icon left as raw non-square master (renders small)" >&2
fi

# NAME = BRANDING + VERSION (D-158-05, owner 2026-10-15: "Gorilla Unleashed followed by the version", on hover, in
# the task manager and wherever the browser appears in a search). The template said "Gorilla Unleashed 154" through
# 155 and 158 because nobody stamped it. Stamped here from the branding's MOZ_APP_DISPLAYNAME and the built
# application.ini's major version, into every name a desktop shows or searches: Name, X-GNOME-FullName, Comment
# (the hover tooltip on many docks), Keywords. Checked by the Fieldkit pipeline (package stage, verify_deb).
DISPLAYNAME=$(sed -n 's/^MOZ_APP_DISPLAYNAME="\{0,1\}\([^"]*\)"\{0,1\}$/\1/p' "$BR/configure.sh" 2>/dev/null | head -1)
MAJOR=$(sed -n 's/^Version=\([0-9]*\).*/\1/p' "$DIST_BIN/application.ini" | head -1)
if [ -n "$DISPLAYNAME" ] && [ -n "$MAJOR" ]; then
  APPNAME="$DISPLAYNAME $MAJOR"
  python3 - "$STAGE/usr/share/applications/gorilla-unleashed.desktop" "$APPNAME" <<'PY'
import sys, re
path, name = sys.argv[1:3]
s = open(path).read()
head, sep, rest = s.partition("\n[Desktop Action")
def put(text, key, value):
    if re.search(rf"(?m)^{key}=", text):
        return re.sub(rf"(?m)^{key}=.*$", f"{key}={value}", text, count=1)
    return text.rstrip("\n") + f"\n{key}={value}\n"
head = put(head, "Name", name)
head = put(head, "X-GNOME-FullName", name)
head = put(head, "Comment", f"{name} web browser")
words = name.split()
kw = re.search(r"(?m)^Keywords=(.*)$", head)
have = [k for k in (kw.group(1).split(";") if kw else []) if k]
head = put(head, "Keywords", ";".join(dict.fromkeys(words + have)) + ";")
open(path, "w").write(head + sep + rest)
PY
  echo "   name: $APPNAME (branding $BR/configure.sh + application.ini)"
else
  echo "FATAL: cannot name the package: MOZ_APP_DISPLAYNAME='$DISPLAYNAME' major version='$MAJOR'" >&2; exit 1
fi

# PROGRAM NAME AND WINDOW IDENTITY (D-158-05, owner 2026-10-15: yes to renaming the program file).
# - RemotingName in application.ini is read at start-up and becomes the Wayland app_id / X11 WM_CLASS of any window
#   started without --name. It was "firefox-default", so a link opened from another app, or any plain launch, showed
#   in the dock as "firefox-default" with a generic icon. Now gorilla-unleashed, matching StartupWMClass.
# - The program is shipped as gorilla-unleashed beside firefox (kept for existing scripts): the task manager shows
#   the file name, cut by Linux to 15 characters ("gorilla-unleash"). The menu entry starts the new name.
APPDIR="$STAGE/usr/lib/gorilla-unleashed"
sed -i 's/^RemotingName=.*/RemotingName=gorilla-unleashed/' "$APPDIR/application.ini"
cp -p "$APPDIR/firefox" "$APPDIR/gorilla-unleashed"
sed -i 's#/usr/lib/gorilla-unleashed/firefox #/usr/lib/gorilla-unleashed/gorilla-unleashed #g' \
  "$STAGE/usr/share/applications/gorilla-unleashed.desktop"
echo "   program: gorilla-unleashed (RemotingName gorilla-unleashed)"

# 4. DEBIAN/control — bump version, compute Installed-Size (KB), keep the rest
INSTALLED_KB=$(du -sk "$STAGE" | cut -f1)
CTRL="$STAGE/DEBIAN/control"
python3 - "$CTRL" "$VERSION" "$INSTALLED_KB" "$BUILDID" <<'PY'
import sys,re
ctrl,ver,size,bid=sys.argv[1:5]
s=open(ctrl).read()
s=re.sub(r'(?m)^Version:.*$', f'Version: {ver}', s)
if 'Installed-Size:' in s:
    s=re.sub(r'(?m)^Installed-Size:.*$', f'Installed-Size: {size}', s)
else:
    s=re.sub(r'(?m)^(Architecture:.*)$', rf'\1\nInstalled-Size: {size}', s)
if 'X-Gorilla-BuildID' not in s:
    s=s.rstrip()+f'\nX-Gorilla-BuildID: {bid}\n'
open(ctrl,'w').write(s)
print(s)
PY

# 5. permissions: control scripts executable, tree readable
chmod 0755 "$STAGE/DEBIAN"/postinst 2>/dev/null || true
find "$STAGE/DEBIAN" -maxdepth 1 -type f \( -name 'preinst' -o -name 'prerm' -o -name 'postrm' \) -exec chmod 0755 {} \; 2>/dev/null || true

# 6. build (root-owner-group => correct ownership without sudo)
mkdir -p "$OUT_DIR"
DEB="$OUT_DIR/${PKG}.deb"
fakeroot dpkg-deb --build --root-owner-group "$STAGE" "$DEB" >/dev/null
echo "== BUILT: $DEB"
ls -la "$DEB" | awk '{print "   size:", $5, "bytes"}'
echo "== dpkg-deb --info =="
dpkg-deb --info "$DEB" | sed 's/^/   /'
echo "== lint: contents sanity =="
dpkg-deb --contents "$DEB" | grep -E ' \./usr/lib/gorilla-unleashed/firefox$| \./usr/share/applications/| \./usr/share/icons/hicolor/1024' | sed 's/^/   /'
# The staged tree passed. Verify the FINISHED package as well: the thing that
# actually gets uploaded is the .deb, not the directory it was made from.
if [ "${GORILLA_SKIP_RELEASE_GATE:-0}" != "1" ] && [ -f "$GATE" ]; then
  echo "== release gate, on the finished package =="
  python3 "$GATE" --deb "$DEB" || {
    echo "The packaged .deb failed the release gate. Not fit to publish." >&2
    exit 1; }
fi
echo "DONE"
