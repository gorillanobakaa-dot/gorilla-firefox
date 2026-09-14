#!/usr/bin/env bash
# =============================================================================
#  get-microsoft-fonts.sh  —  Gorilla Unleashed Firefox 154
#
#  Legally fetch the Microsoft fonts this build bundles, straight from
#  Microsoft's OWN free download: the Windows 11 Enterprise 90-day evaluation
#  ISO. Nothing is pirated and nothing proprietary is redistributed by this
#  repo — YOU pull the fonts from Microsoft, on your machine, with this script.
#
#  Method credit: Arch Linux `ttf-ms-win11-auto` (the upstream approach).
#  Full background is kept with the project's own notes.
#
#  LICENSING (read this):
#    * Microsoft's EULA permits USE of these fonts. It does NOT grant you the
#      right to REDISTRIBUTE the .ttf/.ttc files. That is why this repo ships
#      this SCRIPT instead of the font binaries.
#    * A browser BINARY you compile with these fonts baked in also contains
#      them. Handing that binary to others is redistribution too. If you plan
#      to distribute the compiled browser publicly, either (a) have recipients
#      run this script + rebuild, or (b) build with open fonts (e.g. Noto).
#
#  WHAT IT DOES (Human Track):
#    Downloads Microsoft's free trial Windows, opens it up like a zip, takes
#    out only the 8 font files this browser needs, checks them, and drops them
#    where the build expects them. No Windows install required.
#
#  WHAT IT DOES (Developer Track):
#    Fetches the CLIENTENTERPRISEEVAL x64 ISO, extracts sources/install.wim,
#    pulls /Windows/Fonts/<needed> out of the WIM with 7-Zip, verifies, and
#    copies into firefox-main/browser/fonts/.
# =============================================================================
set -euo pipefail

# --- the exact fonts this build bundles (browser/fonts/) ---------------------
NEEDED_FONTS=(
  consola.ttf      # Consolas  — monospace (DevTools, code)
  segoeui.ttf      # Segoe UI  — Latin/Greek/Cyrillic/Arabic/Hebrew/Thai
  segoeuib.ttf     # Segoe UI Bold
  seguisb.ttf      # Segoe UI Semibold
  SegUIVar.ttf     # Segoe UI Variable
  YuGothR.ttc      # Yu Gothic Regular — Japanese CJK
  YuGothB.ttc      # Yu Gothic Bold
)

# --- where the build wants them ----------------------------------------------
FF_SRC="${FF_SRC:-$HOME/firefox-src}"
DEST="$FF_SRC/browser/fonts"

# --- Microsoft's official free download page (the ISO link rotates; grab the
#     current CLIENTENTERPRISEEVAL x64 en-us ISO from here) --------------------
EVAL_PAGE="https://www.microsoft.com/en-us/evalcenter/evaluate-windows-11-enterprise"
# Optional: pin a known-good direct ISO URL here to skip the manual step.
ISO_URL="${ISO_URL:-}"

WORK="${WORK:-$PWD/temp_font_extract}"   # gitignored
ISO="$WORK/win11-enterprise-eval.iso"

# --- prerequisites -----------------------------------------------------------
need() { command -v "$1" >/dev/null 2>&1 || { echo "MISSING TOOL: $1  (install it and re-run)"; MISS=1; }; }
MISS=0
need 7z || need 7za          # p7zip — reads ISO and WIM
need curl
[ "$MISS" = 1 ] && { echo; echo "Debian/Ubuntu:  sudo apt install p7zip-full curl"; exit 1; }
SEVENZ="$(command -v 7z || command -v 7za)"

mkdir -p "$WORK" "$DEST"

# --- 1. obtain the ISO -------------------------------------------------------
if [ ! -f "$ISO" ]; then
  if [ -n "$ISO_URL" ]; then
    echo "[*] Downloading Win11 Enterprise eval ISO (~5-6 GB, be patient)..."
    curl -L --fail -o "$ISO" "$ISO_URL"
  else
    cat <<EOF

  [!] No ISO_URL pinned. One manual step (Microsoft rotates the direct link):

      1. Open:  $EVAL_PAGE
      2. Choose:  Windows 11 Enterprise  ->  ISO - Enterprise  ->  64-bit English
      3. Save it as:  $ISO
         (or re-run with:  ISO_URL="<direct-link>" $0 )

  Then run this script again.

EOF
    exit 2
  fi
fi

# --- 2. pull install.wim out of the ISO --------------------------------------
echo "[*] Extracting sources/install.wim from ISO..."
"$SEVENZ" e "$ISO" -o"$WORK" "sources/install.wim" -y >/dev/null
WIM="$WORK/install.wim"
[ -f "$WIM" ] || { echo "ERROR: install.wim not found in ISO"; exit 3; }

# --- 3. pull only the fonts we need out of the WIM ---------------------------
echo "[*] Extracting fonts from install.wim/Windows/Fonts ..."
FONTS_TMP="$WORK/Fonts"; mkdir -p "$FONTS_TMP"
# WIM images are indexed; extract the whole Fonts dir, flat, then cherry-pick.
"$SEVENZ" e "$WIM" -o"$FONTS_TMP" -r "Windows/Fonts/*" -y >/dev/null || true

# --- 4. verify + install the exact set ---------------------------------------
echo "[*] Installing into: $DEST"
missing=0
for f in "${NEEDED_FONTS[@]}"; do
  src=$(find "$FONTS_TMP" -iname "$f" -print -quit 2>/dev/null || true)
  if [ -n "$src" ] && [ -f "$src" ]; then
    cp -f "$src" "$DEST/$f"
    printf "    [OK]   %s  (%s)\n" "$f" "$(sha256sum "$DEST/$f" | cut -c1-16)"
  else
    printf "    [MISS] %s  — not found in this ISO edition\n" "$f"
    missing=1
  fi
done

echo
if [ "$missing" = 0 ]; then
  echo "[DONE] All ${#NEEDED_FONTS[@]} fonts installed to $DEST"
  echo "       You can delete the work dir:  rm -rf \"$WORK\""
else
  echo "[WARN] Some fonts were missing. Yu Gothic lives in the Japanese language"
  echo "       pack; if absent, grab it from the -japanese font set (see"
  echo "       the project's own font lists) or a JP eval ISO."
fi
