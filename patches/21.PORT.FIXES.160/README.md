# 21.PORT.FIXES.160

Repairs needed to carry Gorilla's patches onto Firefox 160. Apply in order, after the snapshot groups.

- `003-browser-ftl-a-block-of-158-strings-ids-upstream-renamed-or-r.patch`: Browser.ftl: a block of 158 strings (ids upstream renamed or removed) had landed in the wrong place and duplicated the 160 ids urlbar-result-menu-*2; removed, and the market/dismiss-all/trending messages restored to the 160 ids (Fluent each id once)
- `004-upstream-160-moved-about-studies-from-toolkit-components-nor.patch`: Upstream 160 moved about:studies from toolkit/components/normandy to browser/components/nimbus; the port carried the .sys.mjs and .html hunks but dropped the 158 about-studies.css hunk (cyan text, fixed-bottom watermark 450px, MARK-001): carried to the new path
