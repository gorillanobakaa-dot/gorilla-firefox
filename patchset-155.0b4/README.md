# The 155 patch set

## 🧸 In plain words

This folder holds every change Gorilla Unleashed makes to Firefox, for the
version 155 line. Each `.patch` file is a small list of edits to one file of
Firefox's own source code. `NEW_FILES/` holds whole files that Firefox does
not have at all, like the gorilla artwork.

You do not need any of this to use the browser. Download the `.deb` from the
Releases page and install it. This folder is for someone who wants to build it
themselves, or who wants to read exactly what was changed and check it.

The older folder next to this one, `patches/`, is the same idea for the
version 154 line. Both are kept.

## 💻 Developer

Cut against the pristine `firefox-155.0b4.source.tar.xz`, SHA256
`1d5df65fc6089145354622db0e829df0947b833af11173321cd0eed261b83dbd`, which
matches Mozilla's published `SHA256SUMS`. See `BASELINE.txt`.

```
tar -xJf firefox-155.0b4.source.tar.xz
./apply.sh firefox-155.0
patches/11.FONT.SYSTEM/get-microsoft-fonts.sh firefox-155.0
python3 windows/add_builtin_extension.py --src firefox-155.0 --root . --amo ublock-origin
cd firefox-155.0 && ./mach build
```

Both fetch steps are required, not optional. The `mozconfig` is installed into
the tree by `apply.sh`, so there is nothing to copy by hand.

`apply.sh --check <tree>` is a dry run that changes nothing.

### Why this exists next to `patches/`

`patches/` is cut against Firefox 154.0a1, a nightly with no pinned changeset.
It does not apply cleanly to 155. The 155 browser that shipped had those
failures repaired by hand in a working tree, and the repository was therefore
unable to rebuild its own binary. This set is the measured difference between
the pinned upstream tarball and the tree that actually compiled the shipped
`.deb`, so it does not have that gap.

### Verification

Reconstructed from the tarball and compared against the build tree:

| step | result |
|---|---|
| patches applied at `--fuzz=0` | 418 |
| patches failed | 0 |
| `NEW_FILES` copied | 87 |
| `DELETED_FILES` removed | 6 |
| Microsoft fonts fetched | 7 |
| uBlock Origin payload fetched | 1.74.0 |
| `diff -rq` against the build tree | **exit 0, zero differences** |

The build tree in that comparison is the one that compiled
`gorilla-unleashed_155.0-3_amd64.deb`, BuildID `20260914210140`.

### Layout

| path | what |
|---|---|
| `NN.GROUP/*.patch` | patches, grouped by the same names as `patches/` |
| `NEW_FILES/` | files with no upstream counterpart, copied whole |
| `DELETED_FILES.manifest.txt` | upstream files the build removes |
| `apply.sh` | applies all of the above |
| `BASELINE.txt` | the pinned upstream source and the verification record |

### Fonts

Seven Microsoft fonts are a required part of the build and are present in the
shipped package. They are not in this repository, because the licence covers
use and not redistribution. `patches/11.FONT.SYSTEM/get-microsoft-fonts.sh`
fetches them from Microsoft's own free Windows evaluation image, which is the
same method Arch's `ttf-ms-win11-auto` uses.

### uBlock Origin

Bundled and visible in about:addons, the same as the 154 line. Measured on the
shipped build: `uBlock0@raymondhill.net` 1.74.0, location `app-builtin`,
active, not hidden.

The payload itself is not in this repository. `windows/add_builtin_extension.py`
fetches it from addons.mozilla.org at build time: 17 MB of someone else's code
does not belong in a patch set, and pinning a version beats committing a copy
that quietly ages. The patches that register it ARE here
(`browser/extensions/moz.build`, `browser/modules/moz.build`, the BrowserGlue
hook and `GorillaBuiltinExtensions.sys.mjs`), so without the fetch step the
build fails at configure time on a DIRS entry pointing at a directory that
does not exist.

### Two files shipped whole rather than as patches

`browser/locales/en-US/chrome/browser/uiDensity.properties` differs only by
line endings and a blank line, which makes a patch fragile.
`toolkit/xre/platform.ini.in` is empty, and a diff cannot represent a new
zero-byte file.
