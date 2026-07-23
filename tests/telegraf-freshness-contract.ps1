$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$configPath = Join-Path $RepoRoot "telegraf.conf"
$config = [System.IO.File]::ReadAllText($configPath)

foreach ($expected in @(
    "metric_batch_size = 1",
    "metric_buffer_limit = 2"
)) {
    if (-not $config.Contains($expected)) {
        throw "Telegraf freshness contract is missing '$expected'."
    }
}

Write-Host "[telegraf-freshness-contract] PASS"
