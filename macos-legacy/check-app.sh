#!/bin/sh
# Check a cross-built Mac .app on Linux BEFORE it goes to the MacBook Air.
# Fails (exit 1) if any Mach-O file in the bundle needs a macOS newer than 10.13
# or is not x86_64. Prints the bundle's sha256 for the report.
# Usage: sh check-app.sh <path to .app>
set -eu
APP=${1:?usage: sh check-app.sh <path to .app>}
OBJDUMP=${OBJDUMP:-$HOME/.mozbuild/clang/bin/llvm-objdump}
[ -x "$OBJDUMP" ] || { echo "missing $OBJDUMP" >&2; exit 2; }

bad=0; n=0
find "$APP" -type f > /tmp/check-app.list
while IFS= read -r f; do
  head -c4 "$f" | od -An -tx1 | grep -Eq 'cf fa ed fe|ca fe ba be' || continue
  n=$((n+1))
  hdr=$("$OBJDUMP" --macho --private-headers "$f" 2>/dev/null)
  arch=$("$OBJDUMP" --macho --private-header "$f" 2>/dev/null | awk '/^MH_MAGIC/{print $2}' | sort -u | paste -sd' ' -)
  minos=$(echo "$hdr" | awk '/LC_BUILD_VERSION/{b=1} b&&/minos/{print $2; exit} /LC_VERSION_MIN_MACOSX/{v=1} v&&/version/{print $2; exit}')
  ok=yes
  [ "$arch" = "X86_64" ] || ok=no
  case "$minos" in 10.7*|10.8*|10.9*|10.10*|10.11*|10.12*|10.13*) ;; *) ok=no;; esac
  [ $ok = yes ] || { echo "BAD  $f arch=$arch minos=$minos"; bad=1; }
done < /tmp/check-app.list
echo "Mach-O files checked: $n"
[ "$n" -gt 0 ] || { echo "no Mach-O files found" >&2; exit 1; }
echo "sha256 of the zip to carry:"; ( rm -f /tmp/legacy-mac-test.zip; cd "$(dirname "$APP")" && zip -qry /tmp/legacy-mac-test.zip "$(basename "$APP")" && sha256sum /tmp/legacy-mac-test.zip )
[ $bad = 0 ] && echo "PASS: every Mach-O is x86_64 with minimum macOS <= 10.13" || { echo "FAIL"; exit 1; }
