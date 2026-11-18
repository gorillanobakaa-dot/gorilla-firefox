$ErrorActionPreference = 'Stop'
$root = Join-Path $env:RUNNER_TEMP ('gorilla-install-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $root | Out-Null
$install = Join-Path $root 'installed'
$ini = Join-Path $root 'install.ini'
@(
  '[Install]', "InstallDirectoryPath=$install", 'TaskbarShortcut=false', 'DesktopShortcut=false',
  'StartMenuShortcuts=false', 'MaintenanceService=false', 'PrivateBrowsingShortcut=false', 'RegisterDefaultAgent=false'
) | Set-Content -LiteralPath $ini -Encoding ascii
$process = Start-Process -FilePath $env:FIELDKIT_INSTALLER -ArgumentList "/INI=`"$ini`"" -Wait -PassThru
if ($process.ExitCode) { throw "Installer exited $($process.ExitCode)" }
$app = Join-Path $install 'firefox.exe'
$details = Get-Content -LiteralPath (Join-Path $install 'application.ini')
if ($details -cnotcontains "Version=$env:FIELDKIT_VERSION") { throw 'Installed Firefox has a different version' }
$screen = Join-Path $root 'installed.png'
$profile = Join-Path $root 'profile'
New-Item -ItemType Directory -Path $profile | Out-Null
$process = Start-Process -FilePath $app -ArgumentList "-headless -no-remote -profile `"$profile`" --screenshot `"$screen`" about:blank" -Wait -PassThru
if ($process.ExitCode -or -not (Test-Path -LiteralPath $screen -PathType Leaf)) { throw 'Installed Firefox did not render a page' }
