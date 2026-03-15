$ErrorActionPreference = 'Stop'

Set-Location -Path (Resolve-Path (Join-Path $PSScriptRoot '..'))

function Fail([string]$Message, [string]$Code) {
    Write-Output "[FAIL] $Message"
    if ($Code) { Write-Output "        code: $Code" }
    exit 1
}

Write-Output "== LXS_UI run preflight check =="

$phaseStatus = 'docs\UI_PHASE_STATUS.md'
if (-not (Test-Path $phaseStatus)) {
    Fail "Missing required file: $phaseStatus" "MISSING_FILE"
}

$statusText = Get-Content -Path $phaseStatus -Raw
$latestMatch = [regex]::Match($statusText, '\*{0,2}Latest Completed Run:\*{0,2}\s*Run\s*(\d{2})')
if (-not $latestMatch.Success) {
    Fail "Unable to parse Latest Completed Run from $phaseStatus" "MISSING_STATUS_PARSE"
}
$runNumber = $latestMatch.Groups[1].Value
$runNumber = ('{0:D2}' -f [int]$runNumber)
$checkpoint = Join-Path 'docs/checkpoints' ("RUN_{0}.md" -f $runNumber)
if (-not (Test-Path $checkpoint)) {
    Fail "Missing checkpoint for latest run: $checkpoint" "MISSING_CHECKPOINT"
}

$checkpointText = Get-Content -Path $checkpoint -Raw
$hashMatch = [regex]::Match($checkpointText, '\*\*Commit Hash:\*\*\s*([0-9a-fA-F]+)')
if (-not $hashMatch.Success) {
    Fail "Missing commit hash in $checkpoint" "MISSING_HASH"
}
$checkpointHash = $hashMatch.Groups[1].Value
$head = (git rev-parse --short HEAD).Trim()
if ($checkpointHash -ne $head) {
    $mergeCheck = $null
    $null = & git merge-base --is-ancestor $checkpointHash $head
    $mergeCode = $LASTEXITCODE
    if ($mergeCode -ne 0) {
        Fail ("Checkpoint hash mismatch for $checkpoint. Found {0}, repo HEAD is {1}" -f $checkpointHash, $head) "HASH_MISMATCH"
    }
    Write-Output "==> Checkpoint hash is not HEAD but is a valid repo ancestor commit."
}

$remote = git remote -v 2>$null
if ([string]::IsNullOrWhiteSpace($remote)) {
    Fail "No git remote configured for C:\\DEV\\LXS_UI. Push precondition is missing." "NO_REMOTE"
}
if ($remote -notmatch '\(push\)') {
    Fail "Configured remotes have no push URL. Push precondition is missing." "NO_PUSH_REMOTE"
}

$artifact = Join-Path 'artifacts' ("run_{0}_launch.txt" -f $runNumber)
if (-not (Test-Path $artifact)) {
    Fail "Missing launch proof artifact for latest run: $artifact" "MISSING_ARTIFACT"
}
$artifactText = Get-Content -Path $artifact -Raw
if ($artifactText -notmatch 'Result: PASS') {
    Fail "Launch artifact does not show PASS: $artifact" "ARTIFACT_FAILED"
}

$gitStatus = git status --short
if ([string]::IsNullOrWhiteSpace($gitStatus)) {
    Write-Output "[OK] Working tree clean in C:\\DEV\\LXS_UI"
} else {
    Write-Output "[WARN] Uncommitted changes exist in C:\\DEV\\LXS_UI."
    Write-Output ($gitStatus | ForEach-Object { "    $_" })
}

Write-Output "[OK] Checkpoint hash matches HEAD ($head)."
Write-Output "[OK] Push remote present: "
Write-Output $remote
Write-Output "[OK] Launch proof artifact present: $artifact"
Write-Output "[OK] Latest completed run: Run $runNumber"
Write-Output "Preflight passed."
exit 0
