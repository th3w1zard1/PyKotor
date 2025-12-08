#!/usr/bin/env pwsh

[CmdletBinding(PositionalBinding=$false)]
param(
  [switch]$noprompt,
  [string]$venv_name = ".venv",
  [string]$upx_dir
)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Resolve-Path -LiteralPath "$scriptPath/..").Path
$toolPath = (Resolve-Path -LiteralPath "$rootPath/Tools/KitGenerator").Path
$toolSrcDir = (Resolve-Path -LiteralPath "$toolPath/src").Path

$argsList = @(
    "--tool-path", $toolPath
    "--entrypoint", "kitgenerator/__main__.py"
    "--name", "KitGenerator"
    "--distpath", "$rootPath/dist"
    "--workpath", "$toolSrcDir/build"
    "--console"
    "--onefile"
    "--noconfirm"
    "--clean"
    "--venv-name", $venv_name
)
if ($upx_dir) { $argsList += @("--upx-dir", $upx_dir) }
if ($noprompt) { $argsList += "--noprompt" }

& "$scriptPath/compile_tool.ps1" @argsList
$exitCode = $LASTEXITCODE
if (-not $noprompt) {
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
exit $exitCode

