# install_dropins.ps1 — sync SCHOOLALGOL runtime into Eclipse dropins
# Usage:
#   .\install_dropins.ps1
#   .\install_dropins.ps1 -PluginJar
#   .\install_dropins.ps1 -EclipseDropins "D:\path\to\eclipse\dropins"

param(
    [string]$EclipseDropins = "C:\Users\User\eclipse\java-2022-12\eclipse\dropins",
    [switch]$PluginJar
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$DestInterp = Join-Path $EclipseDropins "schoolalgol-shaya\interpreters\SchoolAlgol"
$PluginVer = "0.6.4"

if (-not (Test-Path -LiteralPath $EclipseDropins)) {
    throw "Eclipse dropins not found: $EclipseDropins"
}

New-Item -ItemType Directory -Force -Path $DestInterp | Out-Null

$pyFiles = Get-ChildItem -LiteralPath $Root -Filter "*.py" -File
if (-not $pyFiles) {
    throw "No *.py files in $Root"
}

$copied = 0
foreach ($f in $pyFiles) {
    Copy-Item -LiteralPath $f.FullName -Destination (Join-Path $DestInterp $f.Name) -Force
    $copied++
}
Write-Host "Synced $copied Python file(s) -> $DestInterp"

if ($PluginJar) {
    $jarCandidates = @(
        (Join-Path $Root "org.myau.shaya.ide\build\org.myau.shaya.ide_$PluginVer.jar"),
        (Join-Path $Root "org.myau.shaya.ide_$PluginVer.jar")
    )
    $jar = $jarCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $jar) {
        Write-Warning "Plugin JAR $PluginVer not found under project; skipped. Build the plug-in first, then re-run with -PluginJar."
    } else {
        $destJar = Join-Path $EclipseDropins (Split-Path -Leaf $jar)
        Copy-Item -LiteralPath $jar -Destination $destJar -Force
        Write-Host "Copied plugin JAR -> $destJar"
        Write-Host "Restart Eclipse so OSGi picks up the bundle."
        foreach ($old in @(
            "org.myau.shaya.ide_0.6.1.jar",
            "org.myau.shaya.ide_0.6.2.jar",
            "org.myau.shaya.ide_0.6.3.jar"
        )) {
            $oldPath = Join-Path $EclipseDropins $old
            if (Test-Path -LiteralPath $oldPath) {
                try {
                    Remove-Item -LiteralPath $oldPath -Force
                    Write-Host "Removed old plugin JAR: $old"
                } catch {
                    Write-Warning "Could not remove $old (locked?): $($_.Exception.Message)"
                }
            }
        }
    }
}

Write-Host "Done. Preferences → ALG → Toolchain home should point to:"
Write-Host "  $(Join-Path $EclipseDropins 'schoolalgol-shaya')"
