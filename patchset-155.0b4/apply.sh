#!/usr/bin/env bash
# =============================================================================
# apply.sh - lay the Gorilla 155 patch set onto a pristine Firefox 155.0b4 tree
#
# LAYMAN: takes a clean copy of Firefox's source code and applies every change
#    this project makes to it. Run it once, pointing at the folder you
#    unpacked the Firefox source into.
#
# DEVELOPER: applies NN.GROUP/*.patch with patch -p1, copies NEW_FILES over the
#    tree, removes the paths in DELETED_FILES.manifest.txt, and reports counts.
#    Anchored to the target tree: refuses to run if it is not a Firefox source
#    tree, rather than creating one.
#
# USAGE:  apply.sh /path/to/firefox-155.0          apply
#         apply.sh --check /path/to/firefox-155.0  dry run, changes nothing
# =============================================================================
set -u
SET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CHECK=0
if [ "${1:-}" = "--check" ]; then CHECK=1; shift; fi
SRC="${1:-}"

[ -n "$SRC" ] || { echo "usage: apply.sh [--check] /path/to/firefox-155.0" >&2; exit 2; }
[ -d "$SRC" ] || { echo "FATAL: no such directory: $SRC" >&2; exit 2; }
# Refuse to invent a tree. A missing marker means the wrong path, not a first run.
[ -f "$SRC/browser/app/profile/firefox.js" ] || {
  echo "FATAL: $SRC does not look like a Firefox source tree" >&2
  echo "       (browser/app/profile/firefox.js is missing)" >&2
  exit 2; }

applied=0; failed=0; FAILED=()
while IFS= read -r p; do
  args=(-p1 --forward --batch --fuzz=0 -s -d "$SRC")
  [ "$CHECK" = 1 ] && args+=(--dry-run)
  if patch "${args[@]}" < "$p" >/dev/null 2>&1; then
    applied=$((applied+1))
  else
    failed=$((failed+1)); FAILED+=("${p#$SET_DIR/}")
  fi
done < <(find "$SET_DIR" -regextype posix-extended -regex '.*/[0-9]{2}\.[^/]+/.*\.patch' | sort)

copied=0
if [ "$CHECK" = 0 ] && [ -d "$SET_DIR/NEW_FILES" ]; then
  while IFS= read -r -d '' f; do
    rel="${f#$SET_DIR/NEW_FILES/}"
    mkdir -p "$SRC/$(dirname "$rel")"
    cp -a "$f" "$SRC/$rel" && copied=$((copied+1))
  done < <(find "$SET_DIR/NEW_FILES" -type f -print0)
fi

removed=0
if [ "$CHECK" = 0 ] && [ -f "$SET_DIR/DELETED_FILES.manifest.txt" ]; then
  while IFS= read -r rel; do
    case "$rel" in ''|'#'*) continue;; esac
    [ -e "$SRC/$rel" ] && { rm -f "$SRC/$rel" && removed=$((removed+1)); }
  done < "$SET_DIR/DELETED_FILES.manifest.txt"
fi

echo "patches applied : $applied"
echo "patches failed  : $failed"
echo "new files copied: $copied"
echo "files removed   : $removed"

if [ "$failed" -gt 0 ]; then
  echo
  echo "FAILED:"
  printf '  %s\n' "${FAILED[@]}"
  echo
  echo "A partly applied set compiles fine and produces a browser quietly"
  echo "missing whichever changes did not land. Fix these before building."
  exit 1
fi

echo
echo "The Microsoft fonts are not in this repository and are still needed."
echo "Run patches/11.FONT.SYSTEM/get-microsoft-fonts.sh against $SRC."
