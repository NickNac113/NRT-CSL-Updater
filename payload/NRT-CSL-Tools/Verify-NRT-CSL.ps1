[CmdletBinding()]
param([string]$PackageRoot)
$ErrorActionPreference = 'Stop'

function Read-Sha256([string]$Path) {
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    $stream = [System.IO.File]::OpenRead($Path)
    try {
        return ([BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-', '').ToLowerInvariant()
    } finally {
        $stream.Dispose()
        $algorithm.Dispose()
    }
}

function Resolve-ChildFile([string]$Parent, [string]$Relative) {
    if ([System.IO.Path]::IsPathRooted($Relative) -or $Relative -match '(^|[\\/])\.\.([\\/]|$)') {
        throw "Invalid catalog path: $Relative"
    }
    $parentPath = [System.IO.Path]::GetFullPath($Parent).TrimEnd([char[]]@('\','/'))
    $result = [System.IO.Path]::GetFullPath((Join-Path $parentPath $Relative))
    if (-not $result.StartsWith($parentPath + [System.IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path leaves the selected folder: $Relative"
    }
    return $result
}

try {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    if ([string]::IsNullOrWhiteSpace($PackageRoot)) { $PackageRoot = Split-Path -Parent $scriptDir }
    $PackageRoot = [System.IO.Path]::GetFullPath($PackageRoot)
    $catalog = Get-Content -LiteralPath (Join-Path $scriptDir 'runtime-integrity.json') -Raw | ConvertFrom-Json
    $candidates = @('NRT CSL', 'CSL') | ForEach-Object { Join-Path $PackageRoot $_ } | Where-Object { Test-Path -LiteralPath $_ -PathType Container }
    if (@($candidates).Count -ne 1) { throw 'Select a package root containing exactly one NRT CSL or CSL folder.' }
    $cslRoot = @($candidates)[0]
    $types = @($catalog.types.PSObject.Properties)
    $failures = [System.Collections.Generic.List[string]]::new()
    $checked = 0
    foreach ($type in $types) {
        $folder = Resolve-ChildFile $cslRoot $type.Name
        $manifest = Resolve-ChildFile $folder 'xsb_aircraft.txt'
        if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
            $failures.Add("Missing: $($type.Name)/xsb_aircraft.txt")
        } else {
            $bytes = [System.IO.File]::ReadAllBytes($manifest)
            $hash = Read-Sha256 $manifest
            if ($bytes.Length -eq 0 -or $bytes -contains 0 -or $type.Value.allowed_manifest_sha256 -notcontains $hash) {
                $failures.Add("Damaged or changed: $($type.Name)/xsb_aircraft.txt")
            }
        }
        $checked++
        foreach ($asset in $type.Value.assets.PSObject.Properties) {
            $path = Resolve-ChildFile $folder $asset.Name
            if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
                $failures.Add("Missing: $($type.Name)/$($asset.Name)")
            } elseif ((Read-Sha256 $path) -ne $asset.Value) {
                $failures.Add("Damaged or changed: $($type.Name)/$($asset.Name)")
            }
            $checked++
        }
    }
    if ($failures.Count) {
        Write-Host "CHECK FAILED: $($failures.Count) file(s) need attention."
        foreach ($failure in $failures) { Write-Host $failure }
        Write-Host 'Copy the affected files again from your verified full CSL package. This tools feed does not distribute aircraft assets.'
        exit 1
    }
    Write-Host "PASS: $($types.Count) type folders and $checked runtime files match the supported catalog."
    Write-Host 'File verification only; simulator and multiplayer testing remain separate.'
    exit 0
} catch {
    Write-Host ('CHECK FAILED: ' + $_.Exception.Message)
    exit 1
}
