#!/usr/bin/env bash
# =============================================================================
# recreate_success.sh — THE BIG GREEN BUTTON (2026-08-04 rewrite, patch-based)
# =============================================================================
# 🧸 LAYMAN: one command that recreates Gorilla Unleashed from nothing. It
#    downloads a clean copy of Firefox's source code, lays all our changes onto
#    it, compiles it, and (if you want) wraps it into an installable .deb. Grab
#    a coffee — the download and the compile each take a while.
#
# 💻 DEVELOPER: cold-start reproducer. Clones mozilla-unified, applies the
#    Gorilla patch set via patches/apply.sh (fuzz-tolerant, see BASELINE.txt),
#    copies the tuned mozconfig, builds through the hardened capture wrapper, and
#    optionally packages the .deb. Replaces the OLD graft-based script, whose
#    universal_freedom_installer/precheck.sh dependencies no longer exist and
#    whose file-copy method this project deliberately abandoned.
#
# USAGE:  recreate_success.sh [SRC_DIR]
#   SRC_DIR default: ~/gorilla-recreate/firefox-src  (a FRESH dir; never your
#                    existing working tree — this clones from scratch)
#
# -----------------------------------------------------------------------------
# 🦍 YO, PAY ATTENTION — WHY BUILDING BEATS DOWNLOADING:
#
#   Because you build from MY mozconfig, you get the added bonus -march=native,
#   and if I'm in a good mood I'll even throw in a few other goodies like -O3,
#   BIOTCHES. 😎
#
#   Translation for the sane: `-march=native` tells the compiler "optimise for
#   the EXACT chip you're compiling on" — YOUR laptop, not mine. It uses every
#   instruction your CPU actually has instead of the museum-safe baseline that
#   shipped binaries must assume. Same for -O3 and LTO. That is the whole point:
#
#     * the prebuilt .deb on the Releases page was compiled for MY machine
#       (Ivy Bridge / Intel HD 4000). It RUNS elsewhere, but it is tuned to me.
#     * this script compiles for YOU. Your cache sizes, your instruction set.
#       That is a better browser than anything I can hand you prebuilt.
#
#   The cost is time (the compile is long on an old machine) and disk (~10-15 GB
#   of build tree). If you have neither, grab the prebuilt .deb instead — it
#   works fine. If you have a spare evening, build it. It's your silicon; use it.
#
#   ⚠ One honest catch: a binary built with -march=native may NOT run on a
#   DIFFERENT/older CPU. Build it on the machine you'll run it on. Don't compile
#   on your shiny new laptop and copy the .deb to grandma's 2009 netbook — it
#   will die with "Illegal instruction". Build there, or use the generic .deb.
# -----------------------------------------------------------------------------
# =============================================================================
set -euo pipefail

# ---- resolve repo root from THIS script's location (portable; no hardcoded paths) ----
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCHSET="$REPO/patches"
MOZCONFIG_SRC="$REPO/mozconfig"                    # the tuned clang-21 mozconfig (bundled)
SRC="${1:-$HOME/gorilla-recreate/firefox-src}"

# ---- unattended mode --------------------------------------------------------
# The stated goal of this project is that an agent can be pointed at this script
# and told "compile the browser and report back". A blocking y/N prompt whose
# default is N breaks that completely and SILENTLY: with no tty, `read` gets
# EOF, the answer stays empty, the compile is skipped, the script prints "Done."
# and exits 0. An agent reads that as success and reports a build that never
# happened. Measured 2026-09-13; it is the single hardest blocker on this path.
#
#   GORILLA_YES=1   or   --yes   answers yes to every prompt.
#
# Also assumed when stdin is not a terminal - exactly the agent case.
GORILLA_YES="${GORILLA_YES:-}"
for a in "$@"; do case "$a" in --yes|-y) GORILLA_YES=1 ;; esac; done
[ -t 0 ] || GORILLA_YES="${GORILLA_YES:-1}"

# ask <prompt> -> 0 for yes, 1 for no. Never blocks when unattended.
ask(){
  if [ -n "$GORILLA_YES" ]; then
    echo -e "${B_C}$1${NC} [auto-yes: unattended]"
    return 0
  fi
  local r=""; read -p "$(echo -e "${B_C}$1 [y/N]: ${NC}")" r || r=n
  [[ "$r" =~ ^[Yy]$ ]]
}
UPSTREAM="https://github.com/mozilla-firefox/firefox.git"  # mozilla-unified mirror
BASELINE_DATE="2026-07-10"

B_G='\033[1;32m'; B_C='\033[1;36m'; B_Y='\033[1;33m'; B_R='\033[1;31m'; NC='\033[0m'
say(){ echo -e "${B_C}$*${NC}"; }
ok(){ echo -e "${B_G}✓ $*${NC}"; }
warn(){ echo -e "${B_Y}⚠ $*${NC}"; }
die(){ echo -e "${B_R}✗ $*${NC}" >&2; exit 1; }

echo -e "${B_G}"
echo "   ╔══════════════════════════════════════════════╗"
echo "   ║   G O R I L L A   U N L E A S H E D   1 5 4    ║"
echo "   ║        recreate our success — one button       ║"
echo "   ╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# ---- 0. sanity: tools + patch set present ----
[ -d "$PATCHSET" ] || die "patch set not found: $PATCHSET"
[ -x "$PATCHSET/apply.sh" ] || die "apply.sh missing/not executable in $PATCHSET"

# =============================================================================
# 0a. PREFLIGHT — "yo, before you click, let me look at your machine"
#
# Compiling a browser is not `apt install`. It is tens of gigabytes, hours of
# CPU, and a pile of build tools. This block checks your box FIRST and tells you
# the truth, so you find out now instead of 4 hours in with a full disk.
# =============================================================================
BUILD_PARENT="$(dirname "$SRC")"; mkdir -p "$BUILD_PARENT" 2>/dev/null || true
DISK_FREE_GB=$(df -BG --output=avail "$BUILD_PARENT" 2>/dev/null | tail -1 | tr -dc '0-9'); DISK_FREE_GB=${DISK_FREE_GB:-0}
HOME_FREE_GB=$(df -BG --output=avail "$HOME" 2>/dev/null | tail -1 | tr -dc '0-9'); HOME_FREE_GB=${HOME_FREE_GB:-0}
RAM_GB=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}'); RAM_GB=${RAM_GB:-0}
SWAP_GB=$(free -g 2>/dev/null | awk '/^Swap:/{print $2}'); SWAP_GB=${SWAP_GB:-0}
CORES=$(nproc 2>/dev/null || echo 1)

# what the build ACTUALLY costs (measured on the reference machine, not guessed):
#   fresh shallow clone ~3-5 GB · objdir ~5-10 GB · ~/.mozbuild toolchains ~2-3 GB
#   => 25 GB free is comfortable, 20 GB is the "you will sweat" minimum.
NEED_GB=25; MIN_GB=20

echo -e "${B_C}┌─ PREFLIGHT — having a look at your computer ────────────────────┐${NC}"
printf "   Disk free (build dir) : %s GB\n" "$DISK_FREE_GB"
printf "   Disk free (\$HOME)     : %s GB   (toolchains land in ~/.mozbuild)\n" "$HOME_FREE_GB"
printf "   RAM / swap            : %s GB / %s GB\n" "$RAM_GB" "$SWAP_GB"
printf "   CPU threads           : %s\n" "$CORES"
echo -e "${B_C}└─────────────────────────────────────────────────────────────────┘${NC}"

# ---- the tools. split: MUST-HAVE vs TOOLCHAIN(mozconfig-specific) ----
MISS_APT=(); MISS_RUST=(); MISS_LLVM=()
for t in git python3 patch rsync curl unzip; do command -v "$t" >/dev/null || MISS_APT+=("$t"); done
command -v rustc    >/dev/null || MISS_RUST+=(rustc)
command -v cargo    >/dev/null || MISS_RUST+=(cargo)
command -v cbindgen >/dev/null || MISS_RUST+=(cbindgen)
command -v node     >/dev/null || MISS_APT+=(nodejs)
# the tuned mozconfig pins the LLVM-21 toolchain by name:
for t in clang-21 clang++-21 lld-21 llvm-ar-21 llvm-nm-21 llvm-ranlib-21 llvm-objcopy-21 llvm-objdump-21; do
  command -v "$t" >/dev/null || MISS_LLVM+=("$t")
done
command -v sccache >/dev/null || MISS_RUST+=(sccache)

# ---- verdicts, in plain English ----
FATAL=0
if [ "$DISK_FREE_GB" -lt "$MIN_GB" ]; then
  echo -e "\n${B_R}💔 DISK: you have ${DISK_FREE_GB} GB free. Compiling Firefox needs ~${NEED_GB} GB.${NC}"
  echo -e "${B_R}   My heart breaks for you, but your computer hasn't got the room to even${NC}"
  echo -e "${B_R}   sniff a Firefox compile. Free up about $((NEED_GB-DISK_FREE_GB)) GB — delete the 'educational${NC}"
  echo -e "${B_R}   material', the distro ISOs you'll never boot, and \`sudo apt clean\`. Then come back.${NC}"
  echo -e "${B_C}   OR: skip all this and grab the prebuilt .deb from the Releases page. Zero GB, zero hours.${NC}"
  FATAL=1
elif [ "$DISK_FREE_GB" -lt "$NEED_GB" ]; then
  warn "DISK: ${DISK_FREE_GB} GB free — that's tight (want ~${NEED_GB} GB). It may work; it may die at 90%."
else
  ok "DISK: ${DISK_FREE_GB} GB free — plenty."
fi

TOTAL_MEM=$((RAM_GB + SWAP_GB))
if [ "$TOTAL_MEM" -lt 4 ]; then
  echo -e "${B_R}🧠 RAM: ${RAM_GB} GB (+${SWAP_GB} GB swap). Linking libxul is the greedy bit and WILL${NC}"
  echo -e "${B_R}   run out of memory here. Add at least 8 GB of swap first, or use the prebuilt .deb.${NC}"
  FATAL=1
elif [ "$TOTAL_MEM" -lt 8 ]; then
  warn "RAM: ${RAM_GB} GB (+${SWAP_GB} GB swap). Thin ice — the final link is memory-hungry."
  warn "     If it dies with 'out of memory'/'signal 9' at the link step: add swap, that's the fix."
else
  ok "RAM: ${RAM_GB} GB (+${SWAP_GB} GB swap) — fine."
fi

# time estimate from core count — honest, not flattering
if   [ "$CORES" -ge 8 ]; then EST="1.5-3 hours"
elif [ "$CORES" -ge 4 ]; then EST="3-6 hours"
else                          EST="6-12 hours (yes, really)"; fi
say "TIME: roughly ${EST} for a cold build on ${CORES} threads. Plug the laptop in."

if [ ${#MISS_APT[@]} -gt 0 ] || [ ${#MISS_RUST[@]} -gt 0 ] || [ ${#MISS_LLVM[@]} -gt 0 ]; then
  echo
  echo -e "${B_Y}📦 YO — you're missing build dependencies. You can't compile a browser without them.${NC}"
  [ ${#MISS_APT[@]}  -gt 0 ] && echo -e "   system packages : ${MISS_APT[*]}"
  [ ${#MISS_RUST[@]} -gt 0 ] && echo -e "   rust toolchain  : ${MISS_RUST[*]}"
  [ ${#MISS_LLVM[@]} -gt 0 ] && echo -e "   LLVM 21         : ${MISS_LLVM[*]}"
  echo
  echo -e "${B_C}   Install them with (copy-paste, ~1-3 GB download, 10-30 min):${NC}"
  [ ${#MISS_APT[@]} -gt 0 ] && \
    echo "     sudo apt install -y build-essential git python3 python3-pip curl unzip rsync patch nodejs libgtk-3-dev libdbus-glib-1-dev libasound2-dev libpulse-dev pkg-config"
  [ ${#MISS_RUST[@]} -gt 0 ] && {
    echo "     curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh   # rust"
    echo "     cargo install cbindgen sccache"; }
  [ ${#MISS_LLVM[@]} -gt 0 ] && {
    echo "     # LLVM 21 is NOT in Debian/Ubuntu default repos — use upstream:"
    echo "     wget https://apt.llvm.org/llvm.sh && chmod +x llvm.sh && sudo ./llvm.sh 21"; }
  echo
  echo -e "${B_C}   Easier option: let Mozilla install most of it for you —${NC}"
  echo    "     cd \"$SRC\" && ./mach --no-interactive bootstrap --application-choice=browser"
  echo -e "${B_C}   (run that AFTER the clone step; it pulls its own clang+rust into ~/.mozbuild)${NC}"
  if [ ${#MISS_LLVM[@]} -gt 0 ]; then
    echo
    warn "NOTE: the tuned mozconfig names clang-21 explicitly. No LLVM 21? Either install it above,"
    warn "      or edit '$MOZCONFIG_SRC' and point CC/CXX/linker at the clang you DO have."
  fi
  FATAL=1
fi

if [ "$FATAL" -ne 0 ]; then
  echo
  echo -e "${B_R}✋ Stopping here — fix the above, then run me again.${NC}"
  echo -e "${B_C}   Not interested in any of this? Totally fair. Download the ready-made .deb:${NC}"
  echo    "   https://github.com/gorillanobakaa-dot/gorilla-firefox/releases"
  exit 1
fi
ok "Preflight passed — your machine can do this. Nice."
echo
say "Baseline: Firefox 154.0a1 nightly, snapshot ~${BASELINE_DATE}."
warn "154.0a1 is a NIGHTLY with no exact pinned changeset (see patches/BASELINE.txt)."
warn "A fresh clone is CLOSE to our baseline; patches apply with fuzz tolerance, and any"
warn "hunk that still won't apply will be reported (not silently skipped)."
echo

# ---- 1. fetch a clean source tree ----
if [ -d "$SRC/.git" ]; then
  say "Step 1/5  Reusing existing checkout at $SRC (git clean + reset)…"
  git -C "$SRC" clean -fdx >/dev/null 2>&1 || true
  git -C "$SRC" reset --hard >/dev/null 2>&1 || true
else
  say "Step 1/5  Cloning vanilla Firefox source (large — this is the long download)…"
  mkdir -p "$(dirname "$SRC")"
  git clone --depth 1 "$UPSTREAM" "$SRC" || die "clone failed"
fi
[ -f "$SRC/browser/config/version.txt" ] || die "clone does not look like a Firefox tree"
ok "vanilla source ready: $(cat "$SRC/browser/config/version.txt")"

# ---- 2. tuned mozconfig ----
say "Step 2/5  Installing the tuned mozconfig (clang-21 / sccache / Wayland)…"
if [ -f "$MOZCONFIG_SRC" ]; then cp "$MOZCONFIG_SRC" "$SRC/mozconfig"; ok "mozconfig installed";
else warn "tuned mozconfig not found at $MOZCONFIG_SRC — using tree default"; fi

# ---- 3. apply the Gorilla patch set (fuzz-tolerant) ----
say "Step 3/5  Applying the Gorilla Unleashed patch set…"
"$PATCHSET/apply.sh" --check "$SRC" || warn "some patches don't apply exactly on this clone (expected on a drifted nightly)."
applied=0; fuzzy=0; failed=0; declare -a FAILEDP=()
while IFS= read -r p; do
  if out=$(patch -p1 --forward --batch --fuzz=3 -d "$SRC" < "$p" 2>&1); then
    echo "$out" | grep -q 'with fuzz' && fuzzy=$((fuzzy+1)) || applied=$((applied+1))
  else failed=$((failed+1)); FAILEDP+=("$(basename "$p")"); fi
done < <(find "$PATCHSET" -regextype posix-extended -regex '.*/[0-9]{2}\.[^/]+/.*\.patch' | sort)
# NEW_FILES + profile user.js handled by a full apply.sh pass.
# This installs the new files AND the profile user.js, which is where the
# privacy hardening lives. It used to run as `>/dev/null 2>&1 || true`, which
# discarded stdout, stderr AND the exit code - so a total failure to install
# the new files was indistinguishable from success.
if ! "$PATCHSET/apply.sh" "$SRC" > "$SRC/.gorilla-apply.log" 2>&1; then
  warn "the NEW_FILES / user.js pass reported a failure."
  warn "last 20 lines of $SRC/.gorilla-apply.log:"
  tail -20 "$SRC/.gorilla-apply.log" | sed "s/^/     /"
  failed=$((failed+1)); FAILEDP+=("apply.sh NEW_FILES pass")
fi
ok "patches: ${applied} clean, ${fuzzy} applied-with-fuzz, ${failed} failed"
if [ "$failed" -gt 0 ]; then
  warn "these hunks need manual attention (upstream drifted past them):"
  printf '     - %s\n' "${FAILEDP[@]}"
  # A partly-applied patch set compiles perfectly well and produces a browser
  # missing an arbitrary subset of the Gorilla changes. That is this project's
  # signature failure - a green build with the fixes absent - and this used to
  # be only a warning, with the build proceeding regardless.
  if [ -z "${GORILLA_IGNORE_FAILED_PATCHES:-}" ]; then
    die "$failed patch(es) failed. Refusing to build a partly-patched tree.
     A browser built from this compiles cleanly and quietly lacks whichever
     changes did not apply. Fix the patches, or set
     GORILLA_IGNORE_FAILED_PATCHES=1 for a deliberate partial build."
  fi
  warn "GORILLA_IGNORE_FAILED_PATCHES set - continuing with a PARTIAL patch set."
fi

# ---- 3b. bundle the built-in extensions ------------------------------------
# The patch set adds "ublock-origin" to browser/extensions/moz.build DIRS and
# installs browser/modules/GorillaBuiltinExtensions.sys.mjs, but it does NOT
# carry the extension itself - 17 MB of third-party code does not belong in a
# patch set, and pinning it by hash is better than committing a copy that
# quietly ages.
#
# So the payload is fetched here. Without this step DIRS points at a directory
# that does not exist and the build fails at configure time. Found 2026-09-13
# by auditing this path; nothing documented the step.
#
# The bundler is idempotent: it skips the DIRS entry and the BrowserGlue hook
# when the patches have already installed them, and only adds the payload.
say "Step 3b/5  Fetching the bundled extensions (uBlock Origin)..."
BUNDLER=""
for c in "$REPO/windows/add_builtin_extension.py"          "$REPO/../working scripts/add_builtin_extension.py"; do
  [ -f "$c" ] && { BUNDLER="$c"; break; }
done
if [ -z "$BUNDLER" ]; then
  warn "add_builtin_extension.py not found - skipping."
  warn "If the patch set lists ublock-origin in DIRS, the build WILL fail."
elif ! command -v python3 >/dev/null 2>&1; then
  die "python3 is required to fetch the bundled extension set."
else
  if python3 "$BUNDLER" --src "$SRC" --root "$REPO" --amo ublock-origin; then
    ok "bundled extensions in place"
  else
    die "could not fetch the bundled extension. The patch set lists it in
     browser/extensions/moz.build DIRS, so the build will fail at configure
     time without it. Check the network, then re-run."
  fi
fi

# ---- 4. build (hardened wrapper — never bare ./mach build) ----
say "Step 4/5  Building (hardened wrapper: unbuffered + telemetry-off)…"
if ask "Start the compile now? ~20-40 min with sccache."; then
  bash "$REPO/scripts/run_build_and_capture.sh" "$SRC" || die "build failed — read the captured log"
  ok "build finished"
  # ---- 5. optional .deb ----
  if ask "Package a .deb now?"; then
    bash "$REPO/scripts/build_deb.sh" "" "$SRC/obj-x86_64-pc-linux-gnu/dist/bin" "$(dirname "$SRC")/release" "$REPO/deb_template" "$SRC/browser/branding/gorilla" && ok "packaged"
  fi
else
  echo -e "\n${B_C}Build later with:${NC}  bash $REPO/scripts/run_build_and_capture.sh \"$SRC\""
fi

echo -e "\n${B_G}Done. Source tree: $SRC${NC}"
