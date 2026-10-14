# Linux-side records, rescued 2026-10-14

These were written on the Debian machine during the 154 and 155 work and were never committed
anywhere. They are kept here beside the Windows records in `windows/`, as history, not as the
current build method (the current patch set is 157; `recreate.sh` and `mozconfig` at the top of
the repository are the Linux build).

- `155-port/`: the Firefox 155 port postmortem, both tracks (2026-08-27).
- `CALL-TRANSPORT-BLACKHOLE.*.md`: why WhatsApp calls rang forever (DTLS 1.3 handshake completes, data
  is dropped) and the DTLS 1.2 cap, both tracks (2026-08-26). The cap itself is in `patches/05.PREFS`.
- `CRISP_ICON_DOCTRINE.md`: the GNOME desktop icon and the crisp-icon rules (2026-09-09).
- `THEME_FIX_LOG_2026-08-27.md`: the theme fix log.
- `webrtc-selftest.html`: the WebRTC self-test page used for the call work.
