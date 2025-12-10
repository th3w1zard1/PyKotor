#!/usr/bin/env pwsh

[CmdletBinding(PositionalBinding = $false)]
param(
  [switch]$noprompt,
  [string]$venv_name = ".venv",
  [string]$upx_dir
)
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRootPath = (Resolve-Path -LiteralPath "$($scriptDir)/..").Path
$toolPath = (Resolve-Path -LiteralPath "$repoRootPath/Tools/HoloPatcher").Path
$toolSrcDir = (Resolve-Path -LiteralPath "$toolPath/src").Path

function Get-LocalOS {
  if ($IsWindows) { return "Windows" }
  if ($IsMacOS) { return "Mac" }
  if ($IsLinux) { return "Linux" }
  return "Unknown"
}
$iconExtension = if ((Get-LocalOS) -eq 'Mac') { 'icns' } else { 'ico' }
$iconPath = "$toolSrcDir/holopatcher/resources/icons/patcher_icon_v2.$iconExtension"

$argsList = @(
  "--tool-path", $toolPath
  "--entrypoint", "holopatcher/__main__.py"
  "--name", "HoloPatcher"
  "--distpath", "$repoRootPath/dist"
  "--workpath", "$toolSrcDir/build"
  "--icon", $iconPath
  "--debug", "imports"
  "--log-level", "INFO"
  "--console"
  "--onefile"
  "--noconfirm"
  "--clean"
  "--exclude-module", "PyQt5"
  "--exclude-module", "PyOpenGL"
  "--exclude-module", "PyGLM"
  "--exclude-module", "dl_translate"
  "--exclude-module", "torch"
  "--exclude-module", "deep_translator"
  "--exclude-module", "cefpython3"
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
  "--venv-name", $venv_name
)

if ($noprompt) { $argsList += "--noprompt" }
if ($upx_dir) { $argsList += @("--upx-dir", $upx_dir) }

& "$scriptDir/compile_tool.ps1" @argsList
exit $LASTEXITCODE