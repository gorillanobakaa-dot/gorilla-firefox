#!/usr/bin/env bash
set -euo pipefail

case "$1" in
  debian-x86_64)
    apt-get install -y "$FIELDKIT_INSTALLER"
    mapfile -t binaries < <(dpkg -L gorilla-unleashed | grep '/gorilla-unleashed/gorilla-unleashed$')
    ((${#binaries[@]} == 1))
    binary=${binaries[0]}
    ;;
  macos-x86_64)
    shopt -s nullglob
    existing=(/Applications/Gorilla*.app)
    ((${#existing[@]} == 0))
    sudo -n installer -pkg "$FIELDKIT_INSTALLER" -target /
    apps=(/Applications/Gorilla*.app)
    ((${#apps[@]} == 1))
    name=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "${apps[0]}/Contents/Info.plist")
    binary="${apps[0]}/Contents/MacOS/$name"
    ;;
  *) exit 2 ;;
esac
test -x "$binary"
reported=$("$binary" --version)
[[ " ${reported} " == *" $FIELDKIT_VERSION "* ]]
