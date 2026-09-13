# Drive the address bar for real: focus, Ctrl+L, type, Enter, read the result.
#
# The machine-readable signal is the WINDOW TITLE. It changes only when a
# navigation actually completed, which is exactly the thing being tested and
# the thing a screenshot cannot assert.
#
# args: <scratch> <firefox.exe> <profile-keep-or-empty>
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class W {
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
}
'@
$sp = $args[0]; $exe = $args[1]
$prof = Join-Path $sp ("addrbar_" + (Get-Random))
New-Item -ItemType Directory -Force -Path $prof | Out-Null
@'
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("datareporting.policy.firstRunURL", "");
'@ | Out-File -FilePath (Join-Path $prof "user.js") -Encoding utf8

Get-Process firefox -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
Start-Process -FilePath $exe -ArgumentList @('-profile',"`"$prof`"",'-no-remote','-new-window','about:blank')
Start-Sleep -Seconds 20

function Win { Get-Process firefox -ErrorAction SilentlyContinue |
               Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1 }
$p = Win
if (-not $p) { Write-Output "RESULT|NOWINDOW|the browser never opened a window"; exit 1 }
[W]::ShowWindow($p.MainWindowHandle,3) | Out-Null
[W]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
Start-Sleep -Milliseconds 2000

function TypeAndGo($text, $label, $settle) {
  [System.Windows.Forms.SendKeys]::SendWait("^l")
  Start-Sleep -Milliseconds 900
  [System.Windows.Forms.SendKeys]::SendWait("^a")
  Start-Sleep -Milliseconds 300
  # SendKeys treats + ^ % ~ ( ) { } [ ] as operators
  $safe = $text -replace '([+^%~(){}\[\]])','{$1}'
  [System.Windows.Forms.SendKeys]::SendWait($safe)
  Start-Sleep -Milliseconds 1200
  # did the characters actually land? title is unchanged yet, so shoot instead
  [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
  Start-Sleep -Seconds $settle
  $w = Win
  $t = if ($w) { $w.MainWindowTitle } else { "" }
  Write-Output ("RESULT|" + $label + "|" + $t)
}

TypeAndGo "about:robots"   "about"  8
TypeAndGo "www.google.com" "url"    14
TypeAndGo "gorilla test"   "search" 14

# a screenshot of the final state, for a human
$b = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.Left,$b.Top,0,0,$bmp.Size)
$shot = Join-Path $sp "addressbar.png"
$bmp.Save($shot,[System.Drawing.Imaging.ImageFormat]::Png)
Write-Output ("SHOT|" + $shot)

Get-Process firefox -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1
Remove-Item -Recurse -Force $prof -ErrorAction SilentlyContinue
