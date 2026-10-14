# The whole Linux 158 port as one diff
<!-- Version: 1.0.0 · updated 26-10-15-00-40 -->

`firefox-158.0-gorilla-linux.diff.gz` is every change the Linux port made to pristine Firefox 158.0 (tag
FIREFOX_158_0_RELEASE, commit 3c71aeacdb), as of 2026-10-15 00:40: 1,754 files, 332 of them binary (branding art),
no Microsoft font binaries. It is a safety copy: the structured per-group export is S9 of the migration plan,
after the build is verified.

To rebuild the ported tree from it, on a clean checkout of FIREFOX_158_0_RELEASE:

    gunzip -c firefox-158.0-gorilla-linux.diff.gz | git apply --binary
    git add -A && git write-tree     # must print 9051605ce537709b27bd0ef8646603ef97655529

The work tree's HEAD at the time: 22def19116dc8fae3c4453deb5a97c028187c153.
