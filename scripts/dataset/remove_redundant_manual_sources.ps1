$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$manualRoot = Join-Path $projectRoot 'datasets\instalasi_manual'
$targets = @(
    'WIDER_train',
    'WIDER_val',
    'WIDER_test',
    'wider_face_split',
    'wider_face_split.zip',
    'qr-codes-main',
    'archive (1)',
    'midv500-master',
    'stamp-detection-main'
)

foreach ($name in $targets) {
    $target = Join-Path $manualRoot $name
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
        Write-Output "Removed: $target"
    }
}

Write-Output 'Retained: datasets/instalasi_manual/archive (2)/data (resume PDFs).'
