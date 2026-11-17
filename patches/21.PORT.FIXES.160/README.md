# 21.PORT.FIXES.160

Repairs needed to carry Gorilla's patches onto Firefox 160. Apply in order, after the snapshot groups.

- `003-browser-ftl-a-block-of-158-strings-ids-upstream-renamed-or-r.patch`: Browser.ftl: a block of 158 strings (ids upstream renamed or removed) had landed in the wrong place and duplicated the 160 ids urlbar-result-menu-*2; removed, and the market/dismiss-all/trending messages restored to the 160 ids (Fluent each id once)
- `004-upstream-160-moved-about-studies-from-toolkit-components-nor.patch`: Upstream 160 moved about:studies from toolkit/components/normandy to browser/components/nimbus; the port carried the .sys.mjs and .html hunks but dropped the 158 about-studies.css hunk (cyan text, fixed-bottom watermark 450px, MARK-001): carried to the new path
- `005-d-157-00-160-link-preview-and-highlight-to-search-settings-removed-support-link-tolerates-empty-base.patch`: about:preferences threw at build-verify (2026-11-16): pageNavigation still listed the removed link-preview rows, and highlight-to-search (chatbot action via the excised GenAI.sys.mjs, Fluent ids absent) is removed with them; moz-support-link formatUTMParams no longer throws on a relative link when app.support.baseURL is empty (about:addons add-on-badges, newtab sponsor-privacy)
- `007-160-port-fix-currenttabpagecategory-guarded-the-aiwindow-age.patch`: 160 port fix: currentTabPageCategory guarded; the aiwindow AgentPageDetector module is excised, ASRouter targeting threw and the new tab page stayed blank
- `009-160-port-fix-currenttabpagecategory-guarded-the-aiwindow-age.patch`: on top of 007: the AgentPageDetector lazy getter is dropped and currentTabPageCategory returns null outright (the aiwindow module is excised; no tab has a page category)
