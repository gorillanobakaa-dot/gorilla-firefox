# Firefox 158.0 port on Linux: where it stands
<!-- Version: 1.0.0 · updated 26-10-14-20-50 -->

Snapshot of 2026-10-14 20:50, saved here so the work survives the session that did it.

| | |
|---|---|
| Task | `firefox-158-linux` (Fieldkit build harness), work tree `~/Documents/FIREFOX.WORK/work/firefox-158.0` on the Linux machine |
| Steps | done 80, proposed 5, deferred 5, obsolete 13, pending 19 (of 122) |
| Groups finished and exported | 01 to 14: `patchset-158.0-groups-01-14/` holds them as patches against pristine 158.0 |
| Still to port | 16.SNAPSHOT.DELTA (in progress), 20.SNAPSHOT.DELTA.155.0.1, 21.PORT.FIXES.157, 22.EGRESS.LOCKDOWN.157 |
| Waiting for the owner | 5 adapted proposals (`proposals/`: each a .diff and a .json with the reason), accepted in one go with `fieldkit build-harness accept firefox-158-linux --all`; 5 deferred steps (upstream removed what they change) |

The exported group patches do NOT yet contain the 5 proposals; they are applied when the owner accepts them and
the groups are exported again.

What to read: `HANDOVER-linux-26-10-14.md` (the whole state and the rules learned), `TEACHING-LOG-linux-26-10-14.md`
(every command run, in order), then `../../MIGRATION-PLAN.md`. The migration plan governs this port from now on.
