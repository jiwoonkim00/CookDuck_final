<#
open_kakao_with_hashes.ps1

Computes the debug Kakao key hash and opens the Kakao Developers site.
It also prints both the computed debug key hash and an optional user-supplied key.
#>
param(
    [string]$UserHash
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$compute = Join-Path $scriptDir 'compute_kakao_key_hash.ps1'
if (!(Test-Path $compute)) { Write-Error "Missing compute script: $compute"; exit 1 }

& $compute

if ($UserHash) {
    Write-Output "User-provided key hash: $UserHash"
    Set-Clipboard -Value ($(Get-Clipboard) + "`n" + $UserHash)
    Write-Output "(Both hashes copied to clipboard)"
}

Start-Process 'https://developers.kakao.com'
Write-Output "Opened Kakao Developers console. Paste the copied hashes into My Application -> Platform -> Android -> Key Hashes."
