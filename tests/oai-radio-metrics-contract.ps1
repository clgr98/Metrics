$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$samplePath = Join-Path $RepoRoot "samples\OCUDU_OAI_RADIO_METRICS.yml"
$sample = [System.IO.File]::ReadAllText($samplePath)

function Assert-Contains {
    param([string]$Needle, [string]$Description)
    if (-not $sample.Contains($Needle)) {
        throw "$Description is missing '$Needle'."
    }
}

Assert-Contains "Count: 1" "OAI single-UE contract"
Assert-Contains "Type: ping" "Ping workload"
Assert-Contains "Type: iperf2" "iPerf2 workload"
Assert-Contains 'Measurement: "virtual_ran_ue_timeseries"' "RAN UE measurement"
Assert-Contains 'Measurement: "radio_channel_timeseries"' "Radio channel measurement"
Assert-Contains '"ue01_ran_cqi"' "CQI dashboard field"
Assert-Contains '"ue01_ran_dl_mcs"' "DL MCS dashboard field"
Assert-Contains '"ue01_ran_ul_mcs"' "UL MCS dashboard field"
Assert-Contains '"ue01_radio_pusch_snr_db"' "PUSCH SNR dashboard field"
Assert-Contains '"ue01_radio_pusch_rsrp_db"' "PUSCH RSRP dashboard field"
Assert-Contains '"ue01_radio_timing_advance_ns"' "Timing-advance dashboard field"
Assert-Contains '"DL MCS"' "DL MCS legend"
Assert-Contains '"UL MCS"' "UL MCS legend"
Assert-Contains '"PUSCH SNR"' "PUSCH SNR legend"
Assert-Contains '"PUSCH RSRP"' "PUSCH RSRP legend"
Assert-Contains '"PUCCH SNR"' "PUCCH SNR legend"

foreach ($legacy in @(
    "virtual_ueransim",
    "agent_type: ueransim",
    "interface: uesimtun0"
)) {
    if ($sample.Contains($legacy)) {
        throw "The OAI radio sample contains legacy RAN metadata: $legacy"
    }
}

Write-Host "[oai-radio-metrics-contract] PASS"
