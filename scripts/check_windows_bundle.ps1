param([Parameter(Mandatory=$true)][string]$Bundle)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$source = (Resolve-Path -LiteralPath $Bundle).Path
$work = Join-Path $projectRoot ('tmp\Prototype été ' + [DateTime]::Now.ToString('yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $work | Out-Null
Copy-Item -LiteralPath $source -Destination $work -Recurse
$copied = Join-Path $work (Split-Path -Leaf $source)
$exe = Join-Path $copied 'ComptaPriveeAI.exe'
$before = @(Get-ChildItem -LiteralPath $copied -Recurse -File | Get-FileHash | Select-Object Path,Hash)
$tess = Get-Command tesseract -ErrorAction SilentlyContinue
$names = @('LOCALAPPDATA','COMPTAPRIVEE_PROTOTYPE_CHECK','PATH','PYTHONHOME','PYTHONPATH','TESSERACT_CMD','TCL_LIBRARY','TK_LIBRARY')
$previous = @{}
foreach ($name in $names) { $previous[$name] = [Environment]::GetEnvironmentVariable($name,'Process') }
try {
    $env:LOCALAPPDATA = Join-Path $work 'Profil fictif'
    $env:COMPTAPRIVEE_PROTOTYPE_CHECK = '1'
    $env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
    $env:PYTHONHOME = ''; $env:PYTHONPATH = ''; $env:TESSERACT_CMD = ''
    $env:TCL_LIBRARY = ''; $env:TK_LIBRARY = ''
    $firstId = $null
    foreach ($pass in 1..3) {
        if ($pass -eq 3 -and $tess) { $env:PATH += ';' + (Split-Path -Parent $tess.Source) }
        $clock = [Diagnostics.Stopwatch]::StartNew()
        $process = Start-Process -FilePath $exe -ArgumentList '--prototype-check' -WorkingDirectory $env:SystemRoot -WindowStyle Hidden -PassThru
        if (-not $process.WaitForExit(55000)) { throw "Délai dépassé, PID de diagnostic : $($process.Id)" }
        $clock.Stop()
        if ($process.ExitCode -ne 0) { throw "Diagnostic en échec : $($process.ExitCode), voir le profil fictif $work" }
        $resultPath = Join-Path $env:LOCALAPPDATA 'ComptaPriveeAI\logs\prototype-check.json'
        $result = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
        if (-not $result.ok -or -not $result.frozen) { throw 'Résultat non autonome.' }
        if ($pass -gt 1 -and (-not $result.persisted_from_previous_run -or $result.case_id -ne $firstId)) { throw 'Persistance incorrecte.' }
        $firstId = $result.case_id
        foreach ($module in $result.modules.PSObject.Properties) {
            if (-not $module.Value.StartsWith($result.resource_dir)) { throw "Module hors bundle : $($module.Name)" }
        }
        Write-Output "Passage $pass : OK, total=$([math]::Round($clock.Elapsed.TotalSeconds,2)) s, GUI=$($result.gui_seconds) s, OCR=$($result.ocr), persistance=$($result.persisted_from_previous_run)"
    }
    $after = @(Get-ChildItem -LiteralPath $copied -Recurse -File | Get-FileHash | Select-Object Path,Hash)
    if (Compare-Object $before $after -Property Path,Hash) { throw 'Le contenu du bundle a changé pendant les contrôles.' }
    Write-Output "Bundle inchangé. Preuves et profil fictif : $work"
} finally {
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$previous[$name],'Process') }
}
