param(
    [string]$Bundle = 'dist/post-v1-d/ComptaPriveeAI',
    [string]$ISCC = 'build/tools/inno-6.7.3/ISCC.exe',
    [string]$Destination = 'dist/installer-1.0.0'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    $bundlePath = (Resolve-Path -LiteralPath $Bundle).Path
    $compilerPath = (Resolve-Path -LiteralPath $ISCC).Path
    $outputPath = [IO.Path]::GetFullPath((Join-Path $projectRoot $Destination))
    $distRoot = Join-Path $projectRoot 'dist'
    if (-not $outputPath.StartsWith($distRoot + [IO.Path]::DirectorySeparatorChar)) { throw 'Destination requise sous dist/.' }
    if (-not $bundlePath.StartsWith($distRoot + [IO.Path]::DirectorySeparatorChar)) { throw 'Bundle requis sous dist/.' }
    if ($outputPath -eq $bundlePath -or $outputPath.StartsWith($bundlePath + [IO.Path]::DirectorySeparatorChar)) { throw 'La sortie doit rester hors du bundle.' }
    foreach ($required in @('ComptaPriveeAI.exe','_internal/python312.dll')) {
        if (-not (Test-Path -LiteralPath (Join-Path $bundlePath $required))) { throw "Bundle incomplet : $required" }
    }
    $versionLine = Select-String -LiteralPath 'pyproject.toml' -Pattern '^version = "([0-9]+\.[0-9]+\.[0-9]+)"$'
    if (-not $versionLine -or $versionLine.Count -gt 1) { throw 'Version stable non déterminée.' }
    $version = $versionLine.Matches[0].Groups[1].Value
    $artifact = Join-Path $outputPath "ComptaPriveeAI-Setup-$version.exe"
    if (Test-Path -LiteralPath $artifact) { throw 'Installateur déjà présent : choisir une autre destination.' }
    $files = @(Get-ChildItem -LiteralPath $bundlePath -Recurse -File)
    foreach ($file in $files) {
        $relative = $file.FullName.Substring($bundlePath.Length + 1)
        if ($relative -match '(^|[\\/])(data|exports|backups|tests|fixtures|\.git|\.venv|\.env)([\\/]|$)' -or $file.Name -like '.env*' -or
            $file.Extension -in @('.db','.sqlite','.sqlite3','.json','.pdf','.csv','.xlsx','.bak','.iss')) {
            throw "Contenu non autorisé dans le bundle : $relative"
        }
    }
    & $compilerPath "/DBundleDir=$bundlePath" "/DInstallerOutput=$outputPath" "/DProductVersion=$version" 'installer/ComptaPriveeAI.iss'
    if ($LASTEXITCODE -ne 0) { throw "Échec Inno Setup : $LASTEXITCODE" }
    $sourceCommit = (& git rev-parse HEAD).Trim()
    $metadata = [ordered]@{
        version = $version
        source_commit = $sourceCommit
        built_at_utc = [DateTime]::UtcNow.ToString('o')
        compiler = $compilerPath
        compiler_sha256 = (Get-FileHash -LiteralPath $compilerPath -Algorithm SHA256).Hash
        bundle_exe_sha256 = (Get-FileHash -LiteralPath (Join-Path $bundlePath 'ComptaPriveeAI.exe') -Algorithm SHA256).Hash
        artifact = $artifact
        size_bytes = (Get-Item -LiteralPath $artifact).Length
        sha256 = (Get-FileHash -LiteralPath $artifact -Algorithm SHA256).Hash
        git_status_at_build = @(& git status --short)
    }
    $metadata | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $outputPath 'build-info.json') -Encoding UTF8
    Write-Output "Installateur : $artifact"
    Write-Output "SHA-256 : $($metadata.sha256)"
} finally { Pop-Location }
