<!-- Version: 1.0.0 · updated 26-10-23-23-00 -->
# Mac patches waiting for the next build

Commits made in the Mac tree after the published series (patches-mac.tar.xz, 15 patches). They are NOT in the
published series or the released app yet. The next Mac build exports them into the series with
`fieldkit macair export-patches`, and this folder is emptied then.

- `0001-Mac-no-Mozilla-in-the-app-s-identity...patch`: bundle ID org.gorilla.unleashed, vendor Gorilla, no Mozilla
  updater or DMG helper named in Info.plist (owner decision 2026-10-23).
