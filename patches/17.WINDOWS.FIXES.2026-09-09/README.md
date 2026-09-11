# Windows build fixes, 2026-09-09

Everything here was found by BUILDING AND RUNNING the browser on
Windows, not by reading the tree. None of it failed at build time.

Each item has a matching preflight check in `harness/lib/preflight.py`
and a full diagnosis in `harness/lib/diagnoses.py`. Read
`BUILD-PLAYBOOK.md` for the assembled version.

## The pattern behind most of these

The AI/genai excision deleted definitions and left references behind.
JavaScript has no link step, so every one of them was silent until the
exact line ran:

| mechanism | symptom |
|---|---|
| bare global -> ReferenceError | every new tab opened blank |
| `lazy.Foo` -> undefined | address bar accepted text, Enter did nothing |
| trailing comma -> SyntaxError | toolbar click handlers dead |
| missing .ftl resource | EVERY label in the chrome window empty |

## Patches

- `browser/app/profile/firefox.js`  
  same gating for the 4 Linux-only prefs that land in this file; both pref files ship on every platform, so an unguarded Linux value is a Windows regression
- `browser/base/content/browser.js`  
  restores the AIWindow ESModule getter, pointed at the stub
- `browser/base/content/navigator-toolbox.js`  
  removes the trailing commas the excision left in two closest() selector lists (SyntaxError killed the toolbar click handlers) and the orphaned AIWindowUI cases
- `browser/components/sessionstore/SessionStore.sys.mjs`  
  restores the AIWindow lazy getter, pointed at the stub
- `browser/components/urlbar/UrlbarProviderQuickSuggest.sys.mjs`  
  restores the UrlbarShared lazy getter; without it get type() threw at provider registration and the address bar would not navigate
- `browser/components/urlbar/UrlbarProviderSearchSuggestions.sys.mjs`  
  same UrlbarShared getter, same defect, not yet triggered
- `browser/installer/package-manifest.in`  
  ONNX entry excised - configure defines ONNX_RUNTIME but the DLL is never built
- `browser/locales/jar.mn`  
  re-adds the preview/genai.ftl mapping the excision removed
- `browser/modules/moz.build`  
  registers AIWindowStub.sys.mjs (EXTRA_JS_MODULES is sorted case-insensitively - AIWindowStub goes AFTER AboutNewTab)
- `browser/themes/shared/browser-shared.css`  
  restores the tabs-navbar.tokens.css import the theme patch replaced rather than added
- `modules/libpref/init/all.js`  
  wraps 9 Linux-only prefs in #ifndef XP_WIN. Four of them (the gpu-process group) INVERT upstream's deliberate Windows defaults - StaticPrefList.yaml sets them true on XP_WIN - which disabled Media Foundation hardware decode and parent-process-ed the compositor

## New files

- `browser/branding/gorilla/branding.nsi`  
  installer identity; shipped as 'Mozilla Developer Preview' from mozilla.org, and the stub download URLs pointed at Mozilla's CDN
- `browser/locales-preview/genai.ftl`  
  empty stub; browser.xhtml still requests preview/genai.ftl and one unresolvable resource blanks EVERY label in the chrome window
- `browser/modules/AIWindowStub.sys.mjs`  
  inert stand-in for the excised AI Window; upstream browser-places.js and SessionStore still call AIWindow, and the ReferenceError blanked every new tab
- `browser/themes/shared/master-redirect.css`  
  FF155 fixes: gray-05 is a FOREGROUND token (blacking it hid every icon), .urlbar-background is a CLASS not an ID, panel styling restored

## Regenerated artwork

Copied whole rather than diffed. All derived from the canonical master
at `gorilla-patchset/deb_template/usr/share/icons/hicolor/1024x1024/`
`apps/gorilla-unleashed.png` (2598x2626 - the directory name lies).

Regenerate with, in this order:

```
regen_branding_pngs.py
generate_branding_icons.py --force
generate_windows_branding_assets.py --force
brand_installer_stub.py
rebuild_about_logo.py --master <canonical> --size 1200
rm <objdir>/browser/app/*.res      # make does not track .ico deps
```

See `doctrine/ICON-DOCTRINE-WINDOWS.md`.

35 artwork file(s) included.
