$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$specPath = Join-Path $PSScriptRoot 'XSDManager.spec'
$distPath = Join-Path $projectRoot 'release'
$workPath = Join-Path $projectRoot 'build'

if (Test-Path $distPath) {
    Remove-Item $distPath -Recurse -Force
}

python -m PyInstaller --clean --noconfirm --distpath $distPath --workpath $workPath $specPath
