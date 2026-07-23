$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$samplePath = Join-Path $RepoRoot "samples\OCUDU_OAI_CHANNEL_COMPARISON.yml"
$sample = [System.IO.File]::ReadAllText($samplePath)

function Assert-Contains {
    param([string]$Needle, [string]$Description)
    if (-not $sample.Contains($Needle)) {
        throw "$Description is missing '$Needle'."
    }
}

Assert-Contains "Profile: baseline-noise40" "Baseline channel profile"
Assert-Contains "Profile: attenuation-6db-noise40" "Attenuated channel profile"
Assert-Contains "DownlinkAttenuationDb: 6" "Downlink attenuation"
Assert-Contains "UplinkAttenuationDb: 6" "Uplink attenuation"
Assert-Contains "NoisePowerDbfs: -40" "Common noise floor"
Assert-Contains "Type: ping" "Comparable ping workload"
Assert-Contains "Type: iperf2" "Comparable iPerf2 workload"
Assert-Contains 'Measurement: "radio_channel_ground_truth_timeseries"' "Ground-truth measurement"
Assert-Contains '"ue01_channel_downlink_attenuation_db"' "Ground-truth dashboard field"
Assert-Contains '"ue01_channel_noise_power_dbfs"' "Noise ground-truth dashboard field"
Assert-Contains '"ue01_radio_pusch_rsrp_db"' "RSRP dashboard field"
Assert-Contains '"ue01_ran_dl_harq_error_percent"' "BLER proxy dashboard field"
Assert-Contains '"ue01_iperf2_tcp_stream_total_throughput_bps"' "Throughput dashboard field"

$pingCount = ([regex]::Matches($sample, "Type: ping")).Count
$iperfCount = ([regex]::Matches($sample, "Type: iperf2")).Count
if ($pingCount -ne 2 -or $iperfCount -ne 2) {
    throw "The comparison must run the same ping and iPerf2 workload once per condition."
}

$noiseCount = ([regex]::Matches($sample, "NoisePowerDbfs: -40")).Count
if ($noiseCount -ne 4) {
    throw "Every comparable workload must use the same -40 dBFS noise power."
}

$singleStreamCount = ([regex]::Matches($sample, '-P 1"')).Count
if ($singleStreamCount -ne 2) {
    throw "Both iPerf2 conditions must use the same single-stream workload."
}

foreach ($legacy in @(
    "virtual_ueransim",
    "agent_type: ueransim",
    "interface: uesimtun0"
)) {
    if ($sample.Contains($legacy)) {
        throw "The OAI channel comparison contains legacy RAN metadata: $legacy"
    }
}

Write-Host "[oai-channel-comparison-contract] PASS"
