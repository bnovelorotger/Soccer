# archive_docs.ps1
# Script para guardar una versión del walkthrough actual en el historial.

param (
    [string]$IterationName = "iteration"
)

$source = "C:\Users\bnove\.gemini\antigravity\brain\ad4b8e56-018f-4a39-b945-c008bbc3569d\walkthrough.md"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$destFolder = "docs/history"

if (!(Test-Path $destFolder)) {
    New-Item -ItemType Directory -Path $destFolder
}

$destPath = "$destFolder/walkthrough_${IterationName}_${timestamp}.md"

if (Test-Path $source) {
    Copy-Item -Path $source -Destination $destPath
    Write-Host "Copia de seguridad creada en: $destPath" -ForegroundColor Green
} else {
    Write-Host "Error: No se encontró el archivo original en $source" -ForegroundColor Red
}
