$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$FrontendPath = Join-Path $ProjectRoot "frontend"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker wurde nicht gefunden."
}

Write-Host "Erzeuge frontend/package-lock.json mit Node 22.16 und npm 10 ..."
docker run --rm `
    -v "${FrontendPath}:/frontend" `
    -w /frontend `
    node:22.16-alpine `
    npm install --package-lock-only --ignore-scripts --no-audit --no-fund

if ($LASTEXITCODE -ne 0) {
    throw "Das Lockfile konnte nicht erzeugt werden."
}

Write-Host "Fertig: $(Join-Path $FrontendPath 'package-lock.json')"
