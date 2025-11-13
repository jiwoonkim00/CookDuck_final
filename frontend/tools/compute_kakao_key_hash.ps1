<#
compute_kakao_key_hash.ps1

Computes the base64 Kakao key hash from a keystore (debug or release).
Usage:
  # debug keystore (default)
  .\compute_kakao_key_hash.ps1

  # custom keystore
  .\compute_kakao_key_hash.ps1 -KeystorePath 'C:\path\to\keystore.jks' -Alias yourAlias -StorePass yourStorePass

Outputs the computed key hash to stdout and copies it to the clipboard.
#>
param(
    [string]$KeystorePath = "$env:USERPROFILE\.android\debug.keystore",
    [string]$Alias = 'androiddebugkey',
    [string]$StorePass = 'android'
)

if (!(Test-Path $KeystorePath)) {
    Write-Error "Keystore not found at $KeystorePath"
    exit 1
}

try {
    $out = & keytool -list -v -keystore $KeystorePath -alias $Alias -storepass $StorePass 2>&1
} catch {
    Write-Error "keytool failed: $_"
    exit 1
}

$sha1Line = $out | Select-String -Pattern 'SHA1:' | ForEach-Object { $_.Line.Trim() }
if (-not $sha1Line) {
    Write-Error "Could not extract SHA1. keytool output:\n$out"
    exit 1
}

$sha1 = ($sha1Line -replace 'SHA1:\s*','').Trim()
$hex = $sha1 -replace '[: ]',''
$bytes = for ($i=0; $i -lt $hex.Length; $i += 2) { [Convert]::ToByte($hex.Substring($i,2),16) }
$hash = [System.Convert]::ToBase64String($bytes)
Write-Output "Kakao key hash: $hash"
Set-Clipboard -Value $hash
Write-Output "(Copied to clipboard)"
