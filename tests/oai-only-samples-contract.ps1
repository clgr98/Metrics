$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$sampleRoot = Join-Path $RepoRoot "samples"

$allTest = [System.IO.File]::ReadAllText(
    (Join-Path $sampleRoot "ALLTEST_DOCKER_IPERF2.yml")
)
foreach ($required in @(
    "Count: 1",
    "experiment_mode: virtual_oai",
    "agent_type: oai",
    "ran_type: ocudu_oai_zmq",
    "interface: oaitun_ue1",
    "RadioChannel:",
    "-P 1"
)) {
    if (-not $allTest.Contains($required)) {
        throw "ALLTEST_DOCKER_IPERF2.yml is missing: $required"
    }
}
foreach ($retiredField in @("ue02_", "ue03_", "-P 5")) {
    if ($allTest.Contains($retiredField)) {
        throw "ALLTEST_DOCKER_IPERF2.yml still contains: $retiredField"
    }
}

Write-Host "[oai-only-samples-contract] PASS"
