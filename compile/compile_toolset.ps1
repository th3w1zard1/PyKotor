#!/usr/bin/env pwsh

[CmdletBinding(PositionalBinding=$false)]
param(
    [switch]$noprompt,
    [string]$venv_name = ".venv",
    [string]$force_python_version,
    [string]$upx_dir
)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRootPath = (Resolve-Path -LiteralPath "$scriptPath/..").Path

function Get-LocalOS {
    if ($IsWindows) { return "Windows" }
    if ($IsMacOS) { return "Mac" }
    if ($IsLinux) { return "Linux" }
    return "Unknown"
}

$toolPath = (Resolve-Path -LiteralPath "$repoRootPath/Tools/HolocronToolset").Path
$toolSrcDir = (Resolve-Path -LiteralPath "$toolPath/src").Path
$iconExtension = if ((Get-LocalOS) -eq 'Mac') { 'icns' } else { 'ico' }
$iconPath = "$toolSrcDir/resources/icons/sith.$iconExtension"
$dataSeparator = if ((Get-LocalOS) -eq "Windows") { ";" } else { ":" }
$argsList = @(
    "--tool-path", $toolPath
    "--entrypoint", "toolset/__main__.py"
    "--name", "HolocronToolset"
    "--distpath", "$repoRootPath/dist"
    "--workpath", "$toolSrcDir/build"
    "--icon", $iconPath
    "--windowed"
    "--onefile"
    "--noconfirm"
    "--clean"
    "--hidden-import", "utility"
    "--hidden-import", "utility.error_handling"
    "--hidden-import", "utility.common"
    "--hidden-import", "utility.system"
    "--hidden-import", "utility.ui_libraries"
    "--hidden-import", "utility.updater"
    "--exclude-module", "dl_translate"
    "--exclude-module", "torch"
    "--include-wiki-if-present"
    "--add-data-if-exists", "$repoRootPath/vendor/kotorblender/io_scene_kotor${dataSeparator}kotorblender/io_scene_kotor"
    "--venv-name", $venv_name
)

$qtApi = if ($env:QT_API) { $env:QT_API } else { "PyQt5" }
$argsList += @("--qt-api", $qtApi, "--exclude-other-qt")

$upxExcludes = @(
    "_uuid.pyd",
    "api-ms-win-crt-environment-l1-1-0.dll",
    "api-ms-win-crt-string-l1-1-0.dll",
    "api-ms-win-crt-convert-l1-1-0.dll",
    "api-ms-win-crt-heap-l1-1-0.dll",
    "api-ms-win-crt-conio-l1-1-0.dll",
    "api-ms-win-crt-filesystem-l1-1-0.dll",
    "api-ms-win-crt-stdio-l1-1-0.dll",
    "api-ms-win-crt-process-l1-1-0.dll",
    "api-ms-win-crt-locale-l1-1-0.dll",
    "api-ms-win-crt-time-l1-1-0.dll",
    "api-ms-win-crt-math-l1-1-0.dll",
    "api-ms-win-crt-runtime-l1-1-0.dll",
    "api-ms-win-crt-utility-l1-1-0.dll",
    "python3.dll",
    "api-ms-win-crt-private-l1-1-0.dll",
    "api-ms-win-core-timezone-l1-1-0.dll",
    "api-ms-win-core-file-l1-1-0.dll",
    "api-ms-win-core-processthreads-l1-1-1.dll",
    "api-ms-win-core-processenvironment-l1-1-0.dll",
    "api-ms-win-core-debug-l1-1-0.dll",
    "api-ms-win-core-localization-l1-2-0.dll",
    "api-ms-win-core-processthreads-l1-1-0.dll",
    "api-ms-win-core-errorhandling-l1-1-0.dll",
    "api-ms-win-core-handle-l1-1-0.dll",
    "api-ms-win-core-util-l1-1-0.dll",
    "api-ms-win-core-profile-l1-1-0.dll",
    "api-ms-win-core-rtlsupport-l1-1-0.dll",
    "api-ms-win-core-namedpipe-l1-1-0.dll",
    "api-ms-win-core-libraryloader-l1-1-0.dll",
    "api-ms-win-core-file-l1-2-0.dll",
    "api-ms-win-core-synch-l1-2-0.dll",
    "api-ms-win-core-sysinfo-l1-1-0.dll",
    "api-ms-win-core-console-l1-1-0.dll",
    "api-ms-win-core-string-l1-1-0.dll",
    "api-ms-win-core-memory-l1-1-0.dll",
    "api-ms-win-core-synch-l1-1-0.dll",
    "api-ms-win-core-interlocked-l1-1-0.dll",
    "api-ms-win-core-datetime-l1-1-0.dll",
    "api-ms-win-core-file-l2-1-0.dll",
    "api-ms-win-core-heap-l1-1-0.dll"
)
foreach ($item in $upxExcludes) { $argsList += @("--upx-exclude", $item) }
if ($upx_dir) { $argsList += @("--upx-dir", $upx_dir) }
if ($noprompt) { $argsList += "--noprompt" }

# If pythonExePath is set (venv already created by workflow), pass --skip-venv and --python-exe
$pythonExeToUse = $null
if ($env:pythonExePath) {
    $pythonExeToUse = $env:pythonExePath
} else {
    # Try to construct from venv_name (workflow creates venv with specific naming)
    $os = Get-LocalOS
    if ($os -eq "Windows") {
        $possiblePython = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) "..\$venv_name\Scripts\python.exe"
    } else {
        $possiblePython = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) "..\$venv_name\bin\python"
    }
    if (Test-Path $possiblePython) {
        $pythonExeToUse = $possiblePython
    }
}

if ($pythonExeToUse) {
    $argsList += "--skip-venv"
    $argsList += @("--python-exe", $pythonExeToUse)
    Write-Host "Using pre-created venv Python: $pythonExeToUse"
}

& "$scriptPath/compile_tool.ps1" @argsList
exit $LASTEXITCODE