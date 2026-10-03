# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# NSIS branding defines for the Gorilla Unleashed build.
#
# GORILLA: this file arrived from the Linux branding directory as the stock
# UNOFFICIAL template, which declares the product as "Mozilla Developer
# Preview" from mozilla.org. Nothing in the build overrides it, so the first
# packaged installer introduced itself as Mozilla's - wrong on the facts and
# a trademark problem besides. The names below are the ones the installer
# UI, the Add/Remove Programs entry and the registry keys actually use.
#
# BrandFullNameInternal is used for registry and filesystem values. Changing
# it after a release orphans the previous install's registry keys, so it is
# set once, here, and left alone.

# BrandFullNameInternal is used for some registry and file system values
# instead of BrandFullName and typically should not be modified.
!define BrandFullNameInternal "Gorilla Unleashed"
!define BrandFullName         "Gorilla Unleashed"
!define CompanyName           "Gorilla"
!define URLInfoAbout          "https://github.com/gorillanobakaa-dot"
!define HelpLink              "https://github.com/gorillanobakaa-dot"

# GORILLA: the stub installer is NOT built or shipped by this project, but
# installer.nsi references these unconditionally so they must stay defined.
# They shipped pointing at download.mozilla.org - meaning any stub built
# from this branding would have downloaded and installed upstream Firefox
# under this name. Pointed at the project instead: still inert, no longer
# wrong.
!define URLStubDownloadX86 "https://github.com/gorillanobakaa-dot"
!define URLStubDownloadAMD64 "https://github.com/gorillanobakaa-dot"
!define URLStubDownloadAArch64 "https://github.com/gorillanobakaa-dot"
!define URLManualDownload "https://github.com/gorillanobakaa-dot"
!define URLSystemRequirements "https://github.com/gorillanobakaa-dot"
!define Channel "release"

# GORILLA: the stub installer is not built or shipped here. These remain
# only because installer.nsi references them unconditionally; the full
# installer never downloads anything, so they are inert.
# The installer's certificate name and issuer expected by the stub installer
!define CertNameDownload   "Mozilla Corporation"
!define CertIssuerDownload "DigiCert Trusted G4 Code Signing RSA4096 SHA384 2021 CA1"

# Dialog units are used so the UI displays correctly with the system's DPI
# settings.
!define PROFILE_CLEANUP_LABEL_TOP "35u"
!define PROFILE_CLEANUP_LABEL_LEFT "0"
!define PROFILE_CLEANUP_LABEL_WIDTH "100%"
!define PROFILE_CLEANUP_LABEL_HEIGHT "80u"
!define PROFILE_CLEANUP_LABEL_ALIGN "center"
!define PROFILE_CLEANUP_CHECKBOX_LEFT "center"
!define PROFILE_CLEANUP_CHECKBOX_WIDTH "100%"
!define PROFILE_CLEANUP_BUTTON_LEFT "center"
!define INSTALL_BLURB_TOP "137u"
!define INSTALL_BLURB_WIDTH "60u"
!define INSTALL_FOOTER_TOP "-48u"
!define INSTALL_FOOTER_WIDTH "250u"
!define INSTALL_INSTALLING_TOP "70u"
!define INSTALL_INSTALLING_LEFT "0"
!define INSTALL_INSTALLING_WIDTH "100%"
!define INSTALL_PROGRESS_BAR_TOP "112u"
!define INSTALL_PROGRESS_BAR_LEFT "20%"
!define INSTALL_PROGRESS_BAR_WIDTH "60%"
!define INSTALL_PROGRESS_BAR_HEIGHT "12u"

!define PROFILE_CLEANUP_CHECKBOX_TOP_MARGIN "20u"
!define PROFILE_CLEANUP_BUTTON_TOP_MARGIN "20u"
!define PROFILE_CLEANUP_BUTTON_X_PADDING "40u"
!define PROFILE_CLEANUP_BUTTON_Y_PADDING "4u"

# Font settings that can be customized for each channel
!define INSTALL_HEADER_FONT_SIZE 28
!define INSTALL_HEADER_FONT_WEIGHT 400
!define INSTALL_INSTALLING_FONT_SIZE 28
!define INSTALL_INSTALLING_FONT_WEIGHT 400

# UI Colors that can be customized for each channel
!define COMMON_TEXT_COLOR 0xFFFFFF
!define COMMON_BACKGROUND_COLOR 0x000000
!define INSTALL_INSTALLING_TEXT_COLOR 0xFFFFFF
