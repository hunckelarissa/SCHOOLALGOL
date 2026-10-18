# build_plugin.ps1 — compile org.myau.shaya.ide and pack JAR for Eclipse dropins
# Usage:  .\org.myau.shaya.ide\build_plugin.ps1
# Requires: javac/jar on PATH, Eclipse plugins under %USERPROFILE%\.p2\pool\plugins
#           (or set $env:ECLIPSE_PLUGINS)

$ErrorActionPreference = "Stop"
$PluginRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $PluginRoot
$Ver = "0.6.7"
$Build = Join-Path $PluginRoot "build"
$Classes = Join-Path $Build "classes"
$Stage = Join-Path $Build "stage"
$SrcRoot = Join-Path $PluginRoot "src"

function Find-EclipsePlugins {
    if ($env:ECLIPSE_PLUGINS -and (Test-Path -LiteralPath $env:ECLIPSE_PLUGINS)) {
        return (Resolve-Path -LiteralPath $env:ECLIPSE_PLUGINS).Path
    }
    $candidates = @(
        (Join-Path $env:USERPROFILE ".p2\pool\plugins"),
        "C:\Users\User\.p2\pool\plugins"
    )
    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath $c) { return (Resolve-Path -LiteralPath $c).Path }
    }
    throw "Eclipse plugins pool not found. Set ECLIPSE_PLUGINS to …\plugins"
}

$Pool = Find-EclipsePlugins
Write-Host "Eclipse plugins: $Pool"

# Required bundle JARs (latest matching prefix)
$need = @(
    "org.eclipse.ui_",
    "org.eclipse.ui.workbench_",
    "org.eclipse.ui.editors_",
    "org.eclipse.ui.ide_",
    "org.eclipse.ui.console_",
    "org.eclipse.ui.views_",
    "org.eclipse.debug.core_",
    "org.eclipse.debug.ui_",
    "org.eclipse.core.runtime_",
    "org.eclipse.core.resources_",
    "org.eclipse.core.jobs_",
    "org.eclipse.core.commands_",
    "org.eclipse.core.contenttype_",
    "org.eclipse.core.filesystem_",
    "org.eclipse.core.expressions_",
    "org.eclipse.jface_",
    "org.eclipse.jface.text_",
    "org.eclipse.ui.workbench.texteditor_",
    "org.eclipse.text_",
    "org.eclipse.osgi_",
    "org.eclipse.equinox.common_",
    "org.eclipse.equinox.registry_",
    "org.eclipse.equinox.preferences_",
    "org.eclipse.equinox.app_",
    "org.eclipse.swt_",
    "org.eclipse.swt.win32.win32.x86_64_",
    "org.eclipse.e4.ui.workbench_",
    "org.eclipse.e4.ui.model.workbench_",
    "org.eclipse.e4.core.contexts_",
    "org.eclipse.e4.core.services_",
    "org.eclipse.e4.ui.services_",
    "org.eclipse.e4.ui.di_",
    "org.eclipse.e4.core.di_",
    "org.eclipse.e4.ui.widgets_",
    "org.eclipse.e4.ui.css.core_",
    "org.eclipse.e4.ui.css.swt_",
    "org.eclipse.e4.ui.css.swt.theme_",
    "org.eclipse.e4.ui.workbench3_",
    "org.eclipse.e4.ui.workbench.swt_",
    "org.eclipse.e4.ui.workbench.renderers.swt_",
    "org.eclipse.e4.ui.bindings_",
    "org.eclipse.e4.core.commands_",
    "org.eclipse.e4.ui.dialogs_",
    "org.eclipse.emf.ecore_",
    "org.eclipse.emf.common_",
    "org.eclipse.emf.ecore.xmi_",
    "org.eclipse.urischeme_",
    "org.osgi.service.component_",
    "org.osgi.util.promise_",
    "org.osgi.util.function_",
    "org.apache.felix.scr_",
    "com.ibm.icu_",
    "org.eclipse.core.databinding_",
    "org.eclipse.core.databinding.observable_",
    "org.eclipse.core.databinding.property_",
    "org.eclipse.jface.databinding_",
    "javax.inject_",
    "javax.annotation_",
    "org.eclipse.osgi.services_"
)

$cp = New-Object System.Collections.Generic.List[string]
foreach ($prefix in $need) {
    $hit = Get-ChildItem -LiteralPath $Pool -Filter "$prefix*.jar" -File -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending | Select-Object -First 1
    if (-not $hit) {
        Write-Warning "Missing plugin JAR prefix: $prefix"
        continue
    }
    $cp.Add($hit.FullName)
}
$classpath = ($cp -join ";")

# Bump Bundle-Version in MANIFEST
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
$mfSrc = Join-Path $PluginRoot "META-INF\MANIFEST.MF"
$mfText = [System.IO.File]::ReadAllText($mfSrc)
$mfText = [regex]::Replace($mfText, "Bundle-Version:\s*[\d.]+", "Bundle-Version: $Ver")
# OSGi MANIFEST: ASCII/UTF-8 without BOM
[System.IO.File]::WriteAllText($mfSrc, $mfText.TrimEnd() + "`r`n", $utf8NoBom)
Write-Host "MANIFEST Bundle-Version -> $Ver"

# Collect sources
$javaFiles = Get-ChildItem -LiteralPath $SrcRoot -Filter "*.java" -Recurse -File
if (-not $javaFiles) { throw "No .java under $SrcRoot" }

if (Test-Path -LiteralPath $Classes) { Remove-Item -LiteralPath $Classes -Recurse -Force }
New-Item -ItemType Directory -Force -Path $Classes | Out-Null
New-Item -ItemType Directory -Force -Path $Build | Out-Null

$sourcesTxt = Join-Path $Build "sources.txt"
[System.IO.File]::WriteAllLines($sourcesTxt, @($javaFiles.FullName), $utf8NoBom)
[System.IO.File]::WriteAllText((Join-Path $Build "classpath.txt"), $classpath, $utf8NoBom)

Write-Host "Compiling $($javaFiles.Count) Java files..."
& javac --release 11 -encoding UTF-8 -cp $classpath -d $Classes "@$sourcesTxt"
if ($LASTEXITCODE -ne 0) { throw "javac failed with exit $LASTEXITCODE" }

# Stage plugin layout
if (Test-Path -LiteralPath $Stage) { Remove-Item -LiteralPath $Stage -Recurse -Force }
New-Item -ItemType Directory -Force -Path (Join-Path $Stage "META-INF") | Out-Null
Copy-Item -LiteralPath $mfSrc -Destination (Join-Path $Stage "META-INF\MANIFEST.MF") -Force
Copy-Item -LiteralPath (Join-Path $PluginRoot "plugin.xml") -Destination (Join-Path $Stage "plugin.xml") -Force
# Copy compiled classes (LiteralPath + "*" does NOT expand wildcards)
$orgPkg = Join-Path $Classes "org"
if (-not (Test-Path -LiteralPath $orgPkg)) {
    throw "No compiled package org/ under $Classes (javac output missing)"
}
Copy-Item -LiteralPath $orgPkg -Destination (Join-Path $Stage "org") -Recurse -Force
$classCount = @(Get-ChildItem -LiteralPath $Stage -Filter "*.class" -Recurse -File).Count
Write-Host "Staged $classCount .class files"
if ($classCount -lt 50) {
    throw "Too few class files in stage ($classCount); aborting jar"
}

# Optional icons / other resources under plugin root
foreach ($extra in @("icons", "OSGI-INF")) {
    $p = Join-Path $PluginRoot $extra
    if (Test-Path -LiteralPath $p) {
        Copy-Item -LiteralPath $p -Destination (Join-Path $Stage $extra) -Recurse -Force
    }
}

$jarName = "org.myau.shaya.ide_$Ver.jar"
$jarOut = Join-Path $Build $jarName
if (Test-Path -LiteralPath $jarOut) { Remove-Item -LiteralPath $jarOut -Force }

Push-Location $Stage
try {
    & jar cfm $jarOut "META-INF\MANIFEST.MF" .
    if ($LASTEXITCODE -ne 0) { throw "jar failed with exit $LASTEXITCODE" }
} finally {
    Pop-Location
}

# Also copy to repo root for install_dropins convenience
Copy-Item -LiteralPath $jarOut -Destination (Join-Path $RepoRoot $jarName) -Force
Write-Host "Built: $jarOut"
Write-Host "Copied: $(Join-Path $RepoRoot $jarName)"
Write-Host "Next: .\install_dropins.ps1 -PluginJar   (after bumping `$PluginVer to $Ver)"
