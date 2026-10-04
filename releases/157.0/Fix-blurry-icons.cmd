@echo off
rem Gorilla Unleashed - fix blurry icons after you replace the Gorilla folder with a new version.
rem Windows keeps pictures of program icons in a cache. When a new Gorilla replaces the old one in the same
rem folder, Windows can keep showing the old, stretched picture, so the icon looks blurry.
rem This asks Windows to draw its icons again. It changes nothing else, sends nothing anywhere,
rem and needs no administrator rights.
echo.
echo  Asking Windows to redraw its icons...
ie4uinit.exe -show
echo.
echo  Done. Look at your desktop now.
echo  If the Gorilla icon is still blurry, sign out of Windows and sign back in
echo  (or restart the computer): Windows then draws every icon fresh.
echo.
pause
