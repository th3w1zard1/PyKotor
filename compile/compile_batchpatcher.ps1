#!/usr/bin/env pwsh

[CmdletBinding(PositionalBinding=$false)]
param(
  [switch]$noprompt,
  [string]$venv_name = ".venv",
  [string]$upx_dir
)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Resolve-Path -LiteralPath "$scriptPath/..").Path
$toolPath = (Resolve-Path -LiteralPath "$rootPath/Tools/BatchPatcher").Path
$toolSrcDir = (Resolve-Path -LiteralPath "$toolPath/src").Path

function Get-LocalOS {
    if ($IsWindows) { return "Windows" }
    if ($IsMacOS) { return "Mac" }
    if ($IsLinux) { return "Linux" }
    return "Unknown"
}

$argsList = @(
    "--tool-path", $toolPath
    "--entrypoint", "batchpatcher/__main__.py"
    "--name", "K_BatchPatcher"
    "--distpath", "$rootPath/dist"
    "--workpath", "$toolSrcDir/build"
    "--windowed"
    "--onefile"
    "--noconfirm"
    "--clean"
    "--exclude-module", "dl_translate"
    "--exclude-module", "torch"
    "--exclude-module", "PyQt5"
    "--exclude-module", "PyOpenGL"
    "--exclude-module", "PyGLM"
    "--exclude-module", "numpy"
    "--exclude-module", "pykotor-gl"
    "--upx-exclude", "_uuid.pyd"
    "--upx-exclude", "api-ms-win-crt-environment-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-crt-string-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-crt-convert-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-crt-heap-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-crt-conio-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-crt-filesystem-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-crt-stdio-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-crt-process-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-crt-locale-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-crt-time-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-crt-math-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-crt-runtime-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-crt-utility-l1-1-0.dll"
    "--upx-exclude", "python3.dll"
    "--upx-exclude", "api-ms-win-crt-private-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-timezone-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-file-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-processthreads-l1-1-1.dll"
    "--upx-exclude", "api-ms-win-core-processenvironment-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-debug-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-localization-l1-2-0.dll"
    "--upx-exclude", "api-ms-win-core-processthreads-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-errorhandling-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-handle-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-util-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-profile-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-rtlsupport-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-namedpipe-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-libraryloader-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-file-l1-2-0.dll"
    "--upx-exclude", "api-ms-win-core-synch-l1-2-0.dll"
    "--upx-exclude", "api-ms-win-core-sysinfo-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-console-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-string-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-memory-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-synch-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-interlocked-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-datetime-l1-1-0.dll"
    "--upx-exclude", "api-ms-win-core-file-l2-1-0.dll"
    "--upx-exclude", "api-ms-win-core-heap-l1-1-0.dll"
    "--preinstall-playwright"
    "--venv-name", $venv_name
)

if ($noprompt) { $argsList += "--noprompt" }
if ($upx_dir) { $argsList += @("--upx-dir", $upx_dir) }

# If pythonExePath is set (venv already created by workflow), pass --skip-venv and --python-exe
if ($env:pythonExePath) {
    $argsList += "--skip-venv"
    $argsList += @("--python-exe", $env:pythonExePath)
}

if ((Get-LocalOS) -eq "Mac") {
    try {
        $tclTkPath = $(brew --prefix tcl-tk)
        if ($tclTkPath) {
            $argsList += @("--extra-path", $tclTkPath)
        }
    } catch {
        Write-Warning "Unable to determine Tcl/Tk path using Homebrew"
    }
}

& "$scriptPath/compile_tool.ps1" @argsList
exit $LASTEXITCODE