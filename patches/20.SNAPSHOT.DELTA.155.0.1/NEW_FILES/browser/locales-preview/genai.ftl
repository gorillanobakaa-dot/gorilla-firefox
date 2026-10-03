# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# GORILLA: deliberately empty.
#
# The genai component was excised, and the excision removed this line from
# browser/locales/jar.mn:
#
#     preview/genai.ftl   (../components/genai/content/genai.ftl)
#
# together with the .ftl it pointed at. But browser/base/content/browser.xhtml
# is an UNMODIFIED UPSTREAM file and still declares the resource:
#
#     <link rel="localization" href="preview/genai.ftl"/>
#
# A localization resource that cannot be found stops the window's Fluent
# bundle from resolving, and then EVERY data-l10n-id in the browser chrome
# comes back empty. The visible result was an app menu with no labels at all -
# while JS-generated text like the "100%" zoom row still rendered, which is
# what proves the labels were ABSENT rather than merely invisible. It also
# produced a flood of console warnings such as:
#
#     <key id="key_newNavigatorTab" data-l10n-id="tab-new-shortcut">
#     is missing "key" and "keycode" attributes
#
# because tab-new-shortcut's .key attribute never resolved either.
#
# browser.xhtml references no genai* message id, so an empty file satisfies
# the resource without bringing any of the feature back. Keeping the file
# empty - rather than deleting the <link> from browser.xhtml - avoids carrying
# a local diff in an upstream file that changes every release.
