#!/bin/bash
# Version: 1.2.0 · updated 26-10-21-01-30
# Trial: the WHOLE Gorilla 157 patch set on the Momiji 157 tree, for the Air (owner 2026-10-20: every Linux/Windows
# decision applies to the Mac). Runs on a separate worktree, never on the tree being built. Records every patch.
# Usage: bash fullset-trial.sh WORKTREE BASE_COMMIT
set -u
WT=${1:?worktree}; BASE=${2:?base commit}
G="${GORILLA_PATCHES:-$(cd "$(dirname "$0")/../patches" && pwd)}"   # the Gorilla patch set next to this folder
PROFILE="$(cd "$(dirname "$0")" && pwd)"
OUT="$PROFILE/fullset-trial-$(date +%y-%m-%d-%H-%M).log"
# The 157 path (what the Windows 157 release applied), in policy order. No 158-only groups.
SET="01.MEDIA 02.GPU 03.NETWORKING 04.PERFORMANCE 05.PREFS 06.QUOTA 07.TOOLKIT 08.Look 09.REMOTE 10.OVERRIDES 11.FONT.SYSTEM 12.MOZAMBIQUE.DRILL 13.TELEMETRY.KILL 14.EGRESS.LOCKDOWN 16.SNAPSHOT.DELTA.2026-08-12 20.SNAPSHOT.DELTA.155.0.1 21.PORT.FIXES.157 22.EGRESS.LOCKDOWN.157"
# Physically impossible or harmful on the Air (PATCHES.md says why). Their 158 forms replace two 01.MEDIA ones.
SKIP="01.MEDIA/dom_media_AudioStream.cpp.patch 01.MEDIA/dom_media_AudioStream.h.patch 01.MEDIA/dom_media_CubebUtils.cpp.patch 01.MEDIA/dom_media_platforms_ffmpeg_FFmpegVideoDecoder.cpp.patch 01.MEDIA/gfx_thebes_gfxPlatformGtk.cpp.patch 01.MEDIA/dom_media_moz.build.patch 01.MEDIA/dom_media_ipc_RemoteVideoDecoder.cpp.patch 01.MEDIA/dom_media_webrtc_jsapi_DefaultCodecPreferences.cpp.patch"
# 0179/0181: the 158 forms of two 01.MEDIA patches. 21.PORT.FIXES.158/007 and 008: the BUILD halves of 01.MEDIA
# (PDMFactory.h Purpose/mForWebCodecs, DecoderTraits FindInReadable); 01.MEDIA was never built on 157 before.
EXTRA="23.REBASE.158.linux/0179-dom_media_ipc_RemoteVideoDecoder_cpp.patch 23.REBASE.158.linux/0181-dom_media_webrtc_jsapi_DefaultCodecPreferences_cpp.patch 21.PORT.FIXES.158/007-build-fix-pdmfactory-h-decoderagent-cpp-webcodecs-purpose-mi.patch 21.PORT.FIXES.158/008-build-fix-findinreadable-pattern-text-comparator-caseinsensi.patch 22.EGRESS.LOCKDOWN.158/026-d-158-15-webcodecs-software-vp8-whatsapp-web-calls-is-a-buil.patch 22.EGRESS.LOCKDOWN.158/017-d-157-32-satellite-menu-open-settings-opens-privacy-netsetti.patch"
# 2026-10-21: 017 was missed (owner found Open Settings landing on General). Momiji 157 has the settings redesign,
# so the switch lives on Privacy & security exactly as in 158. Check every 22.EGRESS.LOCKDOWN.158 patch with
# git apply --check / -R per file before a build; 029's two Cu.isInAutomation lines were missed the same way.

if ! git -C "$WT" checkout -q -f "$BASE" || ! git -C "$WT" clean -qfd; then echo "STOP: cannot reset $WT"; exit 2; fi
cd "$WT" || exit 2
ok=0; bad=0; skipped=0
apply_one() {
  local rel=$1 r
  # GNU patch cannot apply git binary diffs (the Gorilla logos): those patches go through git apply, whole or not at all
  if grep -q '^GIT binary patch' "$G/$rel"; then
    if r=$(git apply --whitespace=nowarn "$G/$rel" 2>&1); then echo "APPLIED  $rel (git apply: binary)" >> "$OUT"; ok=$((ok + 1))
    else echo "FAILED   $rel (git apply) :: $(echo "$r" | tr '\n' ' ' | cut -c1-220)" >> "$OUT"; bad=$((bad + 1)); fi
    return
  fi
  if r=$(patch -p1 --forward --fuzz=3 --no-backup-if-mismatch -s < "$G/$rel" 2>&1); then
    echo "APPLIED  $rel" >> "$OUT"; ok=$((ok + 1))
  else
    echo "FAILED   $rel :: $(echo "$r" | tr '\n' ' ' | cut -c1-220)" >> "$OUT"; bad=$((bad + 1))
  fi
}
for g in $SET; do
  [ -d "$G/$g" ] || { echo "MISSING-GROUP $g" >> "$OUT"; continue; }
  for p in $(cd "$G" && ls "$g"/*.patch 2>/dev/null | sort); do
    case " $SKIP " in *" $p "*) echo "SKIPPED  $p (Mac: see PATCHES.md)" >> "$OUT"; skipped=$((skipped + 1)); continue ;; esac
    apply_one "$p"
  done
  if [ "$g" = 01.MEDIA ]; then for p in $EXTRA; do apply_one "$p"; done; fi
  if [ -d "$G/$g/NEW_FILES" ]; then
    n=0
    while IFS= read -r f; do
      rel="${f#"$G/$g/NEW_FILES/"}"
      [ "$g/$rel" = "10.OVERRIDES/user.js" ] && continue
      mkdir -p "$(dirname "$rel")" && cp -p "$f" "$rel" && n=$((n + 1))
    done < <(find "$G/$g/NEW_FILES" -type f)
    echo "NEWFILES $g: $n copied" >> "$OUT"
  fi
done
rej=$(find . -name '*.rej' | wc -l)
native=$(git grep -n -E '^[^#]*march=native' -- '*.build' '*.mozbuild' '*.mk' '*.configure' | wc -l)
{ echo; echo "SUMMARY applied $ok, failed $bad, skipped $skipped, .rej files $rej, non-comment -march=native in build files: $native"; } >> "$OUT"
echo "$OUT"; tail -1 "$OUT"
