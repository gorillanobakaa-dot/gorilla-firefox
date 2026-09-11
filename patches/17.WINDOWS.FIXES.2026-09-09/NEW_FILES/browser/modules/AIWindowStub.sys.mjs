/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

/**
 * GORILLA: inert stand-in for the excised AI Window component.
 *
 * WHY THIS FILE EXISTS
 *   The AI Window was removed (browser/components/aiwindow has no moz.build
 *   and is commented out of browser/components/moz.build, so nothing in it is
 *   built). The excision also deleted the ChromeUtils.defineESModuleGetters
 *   entries that exposed `AIWindow` - but it did NOT remove every CALL, and
 *   two of the callers are unmodified upstream files:
 *
 *     browser/base/content/browser-places.js       3 calls
 *     browser/components/sessionstore/SessionStore.sys.mjs  2 calls
 *
 *   The result was a ReferenceError during window setup:
 *
 *     browser-places.js, line 1562: ReferenceError: AIWindow is not defined
 *
 *   That line is inside _isNewTabURI(), which is why opening a new tab
 *   produced a blank page: the function threw before it could answer.
 *
 * WHY A STUB RATHER THAN EDITING THE CALLERS
 *   Both callers are upstream files. Patching them adds permanent local diff
 *   to files that change every release, and - more importantly - a missed
 *   call site stays invisible until someone happens to walk that code path.
 *   That is exactly how this shipped. A stub makes every call site safe at
 *   once, including ones nobody has exercised yet.
 *
 * WHAT IT PROMISES
 *   Only that the AI Window is never active. Every predicate answers false,
 *   so callers take the "no AI window" branch - which is the branch that
 *   matches reality in this build. `initialStartupURL` is only read after
 *   isAIWindowActiveAndEnabled() returns true, so it is never reached; it is
 *   defined anyway rather than left to throw.
 *
 *   If a future upstream version calls a member that is not here, the failure
 *   is a clear "not a function" naming this file, rather than a bare
 *   ReferenceError pointing at unmodified upstream code.
 */

export const AIWindow = {
  /** Is this window an AI Window? Never, in this build. */
  isAIWindowActive() {
    return false;
  },

  /** Is this window an AI Window AND is the feature enabled? Never. */
  isAIWindowActiveAndEnabled() {
    return false;
  },

  /**
   * Is this URI the AI Window's own new-tab document? Never - the real new
   * tab page is about:newtab, which this build uses unconditionally.
   */
  isAIWindowNewTabPage() {
    return false;
  },

  /** Unreachable: guarded by isAIWindowActiveAndEnabled() above. */
  get initialStartupURL() {
    return null;
  },
};
