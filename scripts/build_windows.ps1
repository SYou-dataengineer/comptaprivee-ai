param([string]$Python = '', [string]$Destination = 'dist')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $Python) { $Python = Join-Path $projectRoot '.venv-build\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $Python)) { throw 'Créer .venv-build et installer requirements-build.txt avant le build.' }
Push-Location $projectRoot
try {
    $outputPath = [IO.Path]::GetFullPath((Join-Path $projectRoot $Destination))
    $allowedRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'dist'))
    if ($outputPath -ne $allowedRoot -and -not $outputPath.StartsWith($allowedRoot + [IO.Path]::DirectorySeparatorChar)) { throw 'Destination hors dist interdite.' }
    if (Test-Path -LiteralPath (Join-Path $outputPath 'ComptaPriveeAI')) { throw 'Bundle déjà présent : choisir un autre sous-dossier dist pour le conserver.' }
    # Analyse fraîche sans supprimer les diagnostics des builds précédents.
    $workPath = Join-Path $projectRoot ('build/prototype-' + [Guid]::NewGuid().ToString('N'))
    & $Python -m PyInstaller --distpath $outputPath --workpath $workPath ComptaPriveeAI.spec
    if ($LASTEXITCODE -ne 0) { throw "Échec PyInstaller : $LASTEXITCODE" }
} finally { Pop-Location }
