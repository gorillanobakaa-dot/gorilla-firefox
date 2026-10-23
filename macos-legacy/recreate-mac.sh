#!/usr/bin/env bash
# Version: 1.2.0 · updated 26-10-23-19-21
# =====================================================================================================================
# recreate-mac.sh: Gorilla Unleashed for old Intel Macs (built for the MacBook Air 2011, macOS 10.13 High Sierra)
# =====================================================================================================================
# IN PLAIN WORDS: one command on a Linux PC that downloads everything, builds the Gorilla browser for an old Mac, and
#   checks that every program in it runs on macOS 10.13. You copy the finished .zip to the Mac and open it. No AI,
#   no Mac needed for the build (an old Mac cannot build a modern browser: the compiler needs a newer system).
#
# FOR BUILDERS: the base is Momiji v157.0-mj (github.com/aobaharuki2005/firefox), a Firefox kept alive for old macOS.
#   ROUTE A (default): Momiji + OUR Mac patch series (patches-mac.tar.xz, sha256 pinned below). Same source as our
#     release.
#   ROUTE B (--route b, the hard way we started): Momiji + the whole Gorilla 157 patch set (../patches) with the 8 Mac
#     exclusions, then our Mac-only commits on top. Every patch is reported; expect to resolve conflicts by hand.
#   Then: the Microsoft fonts fetched the honest way (Microsoft's own evaluation download, never shipped by us),
#   Apple's macOS SDK pinned by Mozilla, Mozilla's toolchain bootstrap, build, package, check.
#
# USAGE:   bash recreate-mac.sh [all|preflight|source|fonts|sdk|configure|build|package|check] [--route a|b]
#          WORK=~/gorilla-air-recreate (default). Every stage can run alone; a stage that is already done says so.
#          PATCHES_TARBALL=/path/patches-mac.tar.xz   use a local copy instead of downloading it
#          FONTS_FROM=/path/to/folder                 a folder that already holds the 7 Microsoft font files
# NEEDS:   64-bit Linux, about 45 GB free disk, 12 GB RAM or more (16 better), git, curl, python3, unzip, xz, 7z
#          (fonts). Measured on the author's 2012 laptop (i7-3632QM, 16 GB): build 2 h 13 min the first time; a rebuild of the
#          SAME configuration reuses its own compiler cache (one cache per configuration, never shared).
# ENDS:    one line  VERDICT  READY: <zip>  (or the stage that stopped and why)
# =====================================================================================================================
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="${WORK:-$HOME/gorilla-air-recreate}"
SRC="$WORK/momiji-157"
ROUTE=a
STAGE=all
for arg in "$@"; do
  case "$arg" in
    --route) ;;
    a|b) ROUTE="$arg" ;;
    all|preflight|source|fonts|sdk|configure|build|package|check) STAGE="$arg" ;;
    -h|--help) sed -n '2,30p' "$0"; exit 0 ;;
    *) echo "unknown argument: $arg (see --help)"; exit 2 ;;
  esac
done

MOMIJI_URL=https://github.com/aobaharuki2005/firefox.git
MOMIJI_TAG=v157.0-mj
MOMIJI_COMMIT=189d295392c582c310687c6012f66b2d56d95570
PATCHES_URL="${PATCHES_URL:-https://github.com/gorillanobakaa-dot/gorilla-firefox/releases/download/macbook-air/patches-mac.tar.xz}"
PATCHES_SHA256="$(cat "$HERE/patches-mac.sha256" 2>/dev/null | awk '{print $1}')"
SDK_URL=https://swcdn.apple.com/content/downloads/09/08/047-91568-A_Y1CFZWQCD4/4xekpyz43i26dbp4enxfro8eb1q7wiujh5/CLTools_macOSNMOS_SDK.pkg
SDK_SHA512=5db8b5a06a489a7d3ec587ebb7e01be55163128029923fc24edcad47faecd67830193c0d91e2643ee0e92f2ccca37adf20e4c42cf8de5784666f8663638b5cc5
SDK="$HOME/.mozbuild/MacOSX26.5.sdk"
export MOZBUILD_STATE_PATH="$HOME/.mozbuild-legacy-mac"     # kept apart from any Linux Firefox build's toolchain
export MOZCONFIG="$HERE/mozconfig.air"
export RUSTC_BOOTSTRAP=mozglue_static,qcms,encoding_rs,any_all_workaround,coremidi_sys,cubeb_coreaudio

# One compiler cache per configuration (owner 2026-10-23, after a shared cache crashed every clean build): the folder is
# named by a hash of the build settings, the source commit and the patch series. Same configuration: the cache is
# reused (fast). Anything changed: a new, empty cache (never another configuration's objects). Own server port, so the
# author's other builds' sccache server is never reused with the wrong folder.
cache_setup() {
  local sc="$HOME/.mozbuild/sccache/sccache" key
  [ -x "$sc" ] || { unset GORILLA_AIR_SCCACHE_DIR; return 0; }
  key=$( { sha256sum "$MOZCONFIG" | cut -c1-64; git -C "$SRC" rev-parse HEAD 2>/dev/null; echo "$PATCHES_SHA256"; } \
         | sha256sum | cut -c1-16)
  export GORILLA_AIR_SCCACHE_DIR="$HOME/.cache/sccache-gorilla-air/$key"
  export SCCACHE_DIR="$GORILLA_AIR_SCCACHE_DIR" SCCACHE_SERVER_PORT=4231 SCCACHE_CACHE_SIZE=20G
  mkdir -p "$SCCACHE_DIR"
  SCCACHE_SERVER_PORT=4231 "$sc" --stop-server >/dev/null 2>&1 || true     # a running server keeps its old folder
  echo "  compiler cache: $SCCACHE_DIR (this configuration only)"
}
FONTS=(consola.ttf segoeui.ttf segoeuib.ttf seguisb.ttf SegUIVar.ttf YuGothR.ttc YuGothB.ttc)

say()  { echo "$*"; }
stop() { echo "VERDICT  STOPPED at $1: $2"; echo "NEXT     $3"; exit 3; }
done_() { echo "  ok: $*"; }

preflight() {
  say "== preflight: does this machine have what the build needs?"
  local miss=()
  for t in git curl python3 unzip xz; do command -v "$t" >/dev/null || miss+=("$t"); done
  command -v 7z >/dev/null || command -v 7za >/dev/null || miss+=("p7zip-full (7z, for the fonts)")
  [ "$(uname -s)" = Linux ] && [ "$(uname -m)" = x86_64 ] || stop preflight "this is $(uname -s) $(uname -m)" \
      "run it on 64-bit Linux (x86_64); the Mac itself cannot build a modern browser"
  local free_gb ram_gb
  mkdir -p "$WORK"
  free_gb=$(df -Pk "$WORK" | awk 'NR==2{printf "%d", $4/1048576}')
  ram_gb=$(awk '/MemTotal/{printf "%d", $2/1048576}' /proc/meminfo)
  [ "${#miss[@]}" -eq 0 ] || stop preflight "missing: ${miss[*]}" \
      "Debian/Ubuntu: sudo apt install git curl python3 unzip xz-utils p7zip-full"
  [ "$free_gb" -ge 45 ] || stop preflight "only ${free_gb} GB free in $WORK (45 needed)" "free space, or WORK=/a/bigger/disk"
  [ "$ram_gb" -ge 11 ] || stop preflight "only ${ram_gb} GB RAM (12 needed; the link step peaked at 10.7 GB)" \
      "use a machine with more memory"
  done_ "$(uname -m) Linux, ${free_gb} GB free, ${ram_gb} GB RAM, tools present"
}

source_tree() {
  say "== source: Momiji $MOMIJI_TAG + route $ROUTE"
  # The marker names the series it was made from. A tree made from an older series is put back to Momiji and the
  # new series applied (2026-10-23: a changed series was skipped as "already prepared" and the build would have
  # shipped the old patches).
  if [ -f "$SRC/.gorilla-route" ]; then
    if grep -q "series $PATCHES_SHA256" "$SRC/.gorilla-route"; then done_ "already prepared ($(cat "$SRC/.gorilla-route"))"; return; fi
    [ -z "$(git -C "$SRC" status --porcelain --untracked-files=no)" ] || stop source "$SRC has uncommitted changes and an older series" \
        "look at git -C $SRC status; move the tree to the trash if nothing there is yours, then run again"
    say "  the tree was made from another series ($(cat "$SRC/.gorilla-route")): back to Momiji, then the new series"
    git -C "$SRC" reset -q --hard "$MOMIJI_COMMIT" || stop source "could not go back to Momiji $MOMIJI_COMMIT" "move $SRC to the trash and run again"
    rm -f "$SRC/.gorilla-route"
  fi
  if [ ! -d "$SRC/.git" ]; then
    say "  downloading Momiji (shallow, about 5.9 GB on disk)"
    git clone --depth 1 --branch "$MOMIJI_TAG" "$MOMIJI_URL" "$SRC"
  fi
  [ "$(git -C "$SRC" rev-parse HEAD)" = "$MOMIJI_COMMIT" ] || stop source "Momiji $MOMIJI_TAG is not commit $MOMIJI_COMMIT" \
      "the tag moved upstream; tell the Gorilla project (this script pins the commit it was proven on)"
  git -C "$SRC" config user.email >/dev/null || git -C "$SRC" config user.email "recreate@localhost"
  git -C "$SRC" config user.name >/dev/null || git -C "$SRC" config user.name "recreate-mac.sh"
  local tb="${PATCHES_TARBALL:-$WORK/patches-mac.tar.xz}"
  if [ ! -f "$tb" ]; then say "  downloading our Mac patch series"; curl -L --fail -o "$tb" "$PATCHES_URL"; fi
  [ -n "$PATCHES_SHA256" ] || stop source "no patches-mac.sha256 next to this script" "download the whole macos-legacy folder"
  echo "$PATCHES_SHA256  $tb" | sha256sum -c --quiet - || stop source "$tb does not match patches-mac.sha256" \
      "delete it and run again (a broken download), or check you have the matching script version"
  rm -rf "$WORK/patches" && mkdir -p "$WORK/patches" && tar -xJf "$tb" -C "$WORK/patches"
  local all=("$WORK"/patches/*.patch)
  if [ "$ROUTE" = a ]; then
    git -C "$SRC" am --quiet "${all[@]}" || stop source "a patch did not apply (git am stopped)" \
        "git -C $SRC am --abort, then report the patch name; the series is proven on $MOMIJI_COMMIT"
  else
    # route B: patch 0001 (a build side effect), then the Gorilla 157 set itself instead of our 0002, then the rest
    git -C "$SRC" am --quiet "${all[0]}"
    bash "$HERE/fullset-trial.sh" "$SRC" "$(git -C "$SRC" rev-parse HEAD)" || say "  (route B: read the report above)"
    git -C "$SRC" add -A && git -C "$SRC" commit -q -m "route B: Gorilla 157 set applied by fullset-trial.sh"
    git -C "$SRC" am --quiet -3 "${all[@]:2}" || stop source "route B: a Mac commit did not apply on your set" \
        "resolve it (git -C $SRC status), git am --continue, then run this stage again"
  fi
  echo "route $ROUTE $(date -u +%FT%TZ) series $PATCHES_SHA256" > "$SRC/.gorilla-route"
  done_ "source ready, route $ROUTE, $(git -C "$SRC" log --oneline | wc -l) commits"
}

fonts() {
  say "== fonts: the 7 Microsoft fonts into browser/fonts (fetched from Microsoft, never shipped by us)"
  local d="$SRC/browser/fonts" have=0
  for f in "${FONTS[@]}"; do [ -f "$d/$f" ] && have=$((have+1)); done
  if [ "$have" -eq "${#FONTS[@]}" ]; then done_ "all 7 present"; return; fi
  if [ -n "${FONTS_FROM:-}" ]; then
    for f in "${FONTS[@]}"; do cp "$FONTS_FROM/$f" "$d/" || stop fonts "$f not in $FONTS_FROM" "point FONTS_FROM at a folder with all 7"; done
  else
    FF_SRC="$SRC" WORK="$WORK/font-extract" bash "$HERE/../patches/11.FONT.SYSTEM/get-microsoft-fonts.sh" \
      || stop fonts "the font fetch did not finish" "follow its one manual step (Microsoft's ISO link), then run: $0 fonts"
  fi
  for f in "${FONTS[@]}"; do [ -f "$d/$f" ] || stop fonts "$f missing after the fetch" "run: $0 fonts"; done
  done_ "all 7 fonts in $d"
}

sdk() {
  say "== sdk: Apple's macOS SDK (the version Mozilla pins, checked by sha512)"
  if [ -f "$SDK/SDKSettings.json" ]; then done_ "already at $SDK"; return; fi
  grep -q "$SDK_SHA512" "$SRC/taskcluster/kinds/toolchain/macos-sdk.yml" || stop sdk "the tree does not pin this SDK" \
      "the source changed: report it"
  mkdir -p "$SDK"
  (cd "$SRC" && ./mach python taskcluster/scripts/misc/unpack-sdk.py "$SDK_URL" "$SDK_SHA512" \
      Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk "$SDK")
  [ -f "$SDK/SDKSettings.json" ] || stop sdk "the SDK did not unpack" "run: $0 sdk"
  done_ "SDK at $SDK"
}

configure() {
  cache_setup
  say "== configure (downloads Mozilla's toolchain the first time, into $MOZBUILD_STATE_PATH)"
  (cd "$SRC" && ./mach --no-interactive configure > "$WORK/configure.log" 2>&1) \
      || { tail -25 "$WORK/configure.log"; stop configure "see $WORK/configure.log" "fix what it names, run: $0 configure"; }
  local native sandy
  # "no match" is grep's exit 1: under set -e -o pipefail it killed the script with no VERDICT (stranger run,
  # 2026-10-22), exactly when the answer was right (no -march=native). Count without letting grep fail the line.
  native=$( { grep -rE --include=*.mk --include=config.status '^[^#]*-march=native' "$SRC/obj-legacy-mac" 2>/dev/null || true; } | wc -l)
  sandy=$( { grep -c -- '-march=sandybridge' "$SRC/obj-legacy-mac/config.status" || true; } )
  [ "$native" = 0 ] && [ "$sandy" -gt 0 ] || stop configure "CPU flags wrong (native $native, sandybridge $sandy)" \
      "never -march=native: it would build for YOUR CPU and crash the Mac"
  done_ "configured for Sandy Bridge, macOS 10.12+"
}

build() {
  cache_setup
  say "== build (about 2 hours on a 2012 laptop; log: $WORK/build.log)"
  (cd "$SRC" && ./mach --no-interactive build -j"$(nproc)" > "$WORK/build.log" 2>&1) \
      || { tail -30 "$WORK/build.log"; stop build "see $WORK/build.log" "fix what it names, run: $0 build (it resumes)"; }
  done_ "built"
}

package() {
  say "== package"
  (cd "$SRC" && ./mach --no-interactive package > "$WORK/package.log" 2>&1) \
      || { tail -20 "$WORK/package.log"; stop package "see $WORK/package.log" "run: $0 package"; }
  done_ "packaged"
}

check() {
  say "== check: every program file 64-bit Intel and allowed on macOS 10.13; the fonts inside"
  local omni app
  omni=$(find "$SRC/obj-legacy-mac/dist" -mindepth 5 -maxdepth 5 -path "*.app/Contents/Resources/omni.ja" | head -1)
  [ -n "$omni" ] || stop check "no packaged app found" "run: $0 package"
  app=${omni%/Contents/Resources/omni.ja}
  for f in "${FONTS[@]}"; do [ -f "$app/Contents/Resources/fonts/$f" ] || stop check "$f is not inside the app" "run: $0 fonts, then build"; done
  OBJDUMP="$MOZBUILD_STATE_PATH/clang/bin/llvm-objdump" sh "$HERE/check-app.sh" "$app" > "$WORK/check.log" 2>&1 \
      || { cat "$WORK/check.log"; stop check "a program file would not run on 10.13" "see $WORK/check.log"; }
  local zip
  zip="$WORK/gorilla-air-$(date +%y-%m-%d-%H-%M).zip"
  mv /tmp/legacy-mac-test.zip "$zip"
  sha256sum "$zip" > "$zip.sha256"
  tail -3 "$WORK/check.log"
  echo "VERDICT  READY: $zip ($(du -h "$zip" | cut -f1)); copy it to the Mac, unzip, move Gorilla Unleashed.app to Applications"
  echo "NEXT     first start on a newer macOS: System Settings > Privacy & Security > Open Anyway (the app is not signed by Apple)"
}

case "$STAGE" in
  preflight) preflight ;;  source) source_tree ;;  fonts) fonts ;;  sdk) sdk ;;
  configure) configure ;;  build) build ;;  package) package ;;  check) check ;;
  all) preflight; source_tree; fonts; sdk; configure; build; package; check ;;
esac
