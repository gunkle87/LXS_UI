param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(1, 99)]
    [int] $Run,

    [Parameter(Mandatory = $true)]
    [ValidateSet("in-progress", "blocked", "done")]
    [string] $Status,

    [string] $Files = "",
    [string] $Action = "",
    [string] $Next = ""
)

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$artifactsDir = Join-Path $root "artifacts"
if (-not (Test-Path $artifactsDir)) {
    New-Item -ItemType Directory -Path $artifactsDir | Out-Null
}

$runFile = Join-Path $artifactsDir ("run_{0:D2}_heartbeat.txt" -f $Run)
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$line = ("{0} | files={1} | action={2} | status={3} | next={4}" -f $timestamp, $Files, $Action, $Status, $Next)
Add-Content -Path $runFile -Value $line
Write-Output $line
