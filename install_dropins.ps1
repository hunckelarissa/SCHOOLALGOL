# install_dropins.ps1 — sync SCHOOLALGOL toolchain into Eclipse dropins
# Usage:
#   .\install_dropins.ps1
#   .\install_dropins.ps1 -PluginJar
#   .\install_dropins.ps1 -Examples
#   .\install_dropins.ps1 -EclipseDropins "D:\path\to\eclipse\dropins"
#
# Copies:
#   *.py              → schoolalgol-shaya\interpreters\SchoolAlgol\
#   tools\shaya-run.bat → schoolalgol-shaya\tools\
#   (optional) examples\ → schoolalgol-shaya\examples\
#   (optional) plugin JAR → dropins\
# Does NOT copy docs/ unless you sync them yourself (About/menu open GRAMMAR.md from repo or examples).

param(
    [string]$EclipseDropins = "",
    [switch]$PluginJar,
    [switch]$Examples
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PluginVer = "0.6.11"

function Find-EclipseDropins {
    param([string]$Preferred)
    if ($Preferred -and (Test-Path -LiteralPath $Preferred)) {
        return (Resolve-Path -LiteralPath $Preferred).Path
    }
    $candidates = @(
        "C:\Users\User\eclipse\java-2022-12\eclipse\dropins",
        (Join-Path $env:USERPROFILE "eclipse\java-2022-12\eclipse\dropins"),
        (Join-Path $env:USERPROFILE "eclipse\jee-2022-12\eclipse\dropins"),
        (Join-Path $env:USERPROFILE "eclipse\java-2023-12\eclipse\dropins"),
        (Join-Path $env:USERPROFILE "eclipse\jee-2023-12\eclipse\dropins")
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path -LiteralPath $c)) {
            return (Resolve-Path -LiteralPath $c).Path
        }
    }
    # Discover eclipse*\*\dropins under %USERPROFILE%\eclipse
    $eclipseRoot = Join-Path $env:USERPROFILE "eclipse"
    if (Test-Path -LiteralPath $eclipseRoot) {
        $found = Get-ChildItem -LiteralPath $eclipseRoot -Directory -ErrorAction SilentlyContinue |
            ForEach-Object {
                $d = Join-Path $_.FullName "eclipse\dropins"
                if (Test-Path -LiteralPath $d) { $d }
            } |
            Select-Object -First 1
        if ($found) { return $found }
    }
    return $null
}

$EclipseDropins = Find-EclipseDropins -Preferred $EclipseDropins
if (-not $EclipseDropins) {
    throw @"
Eclipse dropins not found.
Pass -EclipseDropins with the full path, e.g.:
  .\install_dropins.ps1 -EclipseDropins `"D:\path\to\eclipse\dropins`"
"@
}

Write-Host "Eclipse dropins: $EclipseDropins"

$Toolchain = Join-Path $EclipseDropins "schoolalgol-shaya"
$DestInterp = Join-Path $Toolchain "interpreters\SchoolAlgol"
$DestTools = Join-Path $Toolchain "tools"

New-Item -ItemType Directory -Force -Path $DestInterp | Out-Null
New-Item -ItemType Directory -Force -Path $DestTools | Out-Null

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

$batSrc = Join-Path $Root "tools\shaya-run.bat"
if (-not (Test-Path -LiteralPath $batSrc)) {
    throw "Missing $batSrc (required for ALG Run/Check)"
}
Copy-Item -LiteralPath $batSrc -Destination (Join-Path $DestTools "shaya-run.bat") -Force
Write-Host "Synced tools\shaya-run.bat -> $DestTools"

# Short honest README in toolchain (no false claims about full docs/)
$tcReadme = @(
    "# SCHOOLALGOL toolchain (Eclipse dropins)",
    "",
    "Layout:",
    "",
    "  schoolalgol-shaya/",
    "    tools/shaya-run.bat",
    "    interpreters/SchoolAlgol/   - runtime *.py from repo root",
    "    examples/                   - optional (install_dropins.ps1 -Examples)",
    "    docs/GRAMMAR.md             - English grammar (synced)",
    "    docs/GRAMMAR.ru.md          - Russian grammar (synced if present)",
    "",
    "Preferences -> ALG -> Toolchain home = this folder (or empty for auto-detect).",
    "Sync: install_dropins.ps1 [-PluginJar] [-Examples]",
    "See repo IDE_SETUP.md."
) -join "`n"
Set-Content -LiteralPath (Join-Path $Toolchain "README.md") -Value $tcReadme -Encoding UTF8

if ($Examples) {
    $exSrc = Join-Path $Root "examples"
    if (-not (Test-Path -LiteralPath $exSrc)) {
        Write-Warning "examples/ not found in repo; skipped."
    } else {
        $exDest = Join-Path $Toolchain "examples"
        if (Test-Path -LiteralPath $exDest) {
            Remove-Item -LiteralPath $exDest -Recurse -Force
        }
        Copy-Item -LiteralPath $exSrc -Destination $exDest -Recurse -Force
        Write-Host "Synced examples/ -> $exDest"
    }
}

# Grammar docs for About / menu (EN default + RU mirror)
$docsDest = Join-Path $Toolchain "docs"
New-Item -ItemType Directory -Force -Path $docsDest | Out-Null
foreach ($docName in @("GRAMMAR.md", "GRAMMAR.ru.md")) {
    $grammarSrc = Join-Path $Root $docName
    if (Test-Path -LiteralPath $grammarSrc) {
        Copy-Item -LiteralPath $grammarSrc -Destination (Join-Path $docsDest $docName) -Force
        Write-Host "Synced $docName -> $docsDest"
    }
}

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
            "org.myau.shaya.ide_0.6.3.jar",
            "org.myau.shaya.ide_0.6.4.jar",
            "org.myau.shaya.ide_0.6.5.jar",
            "org.myau.shaya.ide_0.6.6.jar",
            "org.myau.shaya.ide_0.6.7.jar",
            "org.myau.shaya.ide_0.6.8.jar",
            "org.myau.shaya.ide_0.6.9.jar",
            "org.myau.shaya.ide_0.6.10.jar"
        )) {
            $oldPath = Join-Path $EclipseDropins $old
            if (Test-Path -LiteralPath $oldPath) {
                try {
                    Remove-Item -LiteralPath $oldPath -Force
                    Write-Host "Removed old plugin JAR: $old"
                } catch {
                    Write-Warning "Could not remove $old (locked?): $($_.Exception.Message)"
                    Write-Warning "Close Eclipse, then delete $oldPath manually."
                }
            }
        }
    }
}

# C4: warn if several plugin JARs remain in dropins (OSGi may load the wrong one).
$pluginJars = @(Get-ChildItem -LiteralPath $EclipseDropins -Filter "org.myau.shaya.ide_*.jar" -ErrorAction SilentlyContinue)
if ($pluginJars.Count -gt 1) {
    $names = ($pluginJars | ForEach-Object { $_.Name }) -join ", "
    Write-Warning "Multiple ALG plugin JARs in dropins: $names"
    Write-Warning "Close Eclipse, keep only org.myau.shaya.ide_$PluginVer.jar, remove the rest."
} elseif ($pluginJars.Count -eq 1 -and $pluginJars[0].Name -ne "org.myau.shaya.ide_$PluginVer.jar") {
    Write-Warning "Dropins has $($pluginJars[0].Name); expected org.myau.shaya.ide_$PluginVer.jar (run with -PluginJar after build)."
}

Write-Host "Done. Preferences → ALG → Toolchain home should point to:"
Write-Host "  $Toolchain"
Write-Host "Tip: .\install_dropins.ps1 -Examples   to sync examples/track for Учебный трек…"
Write-Host "Tip: close Eclipse before removing old org.myau.shaya.ide_*.jar from dropins."
