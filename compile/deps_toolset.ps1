#!/usr/bin/env pwsh

[CmdletBinding(PositionalBinding=$false)]
param(
  [switch]$noprompt,
  [string]$venv_name = ".venv"
)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Resolve-Path -LiteralPath "$scriptPath/..").Path

$qtApi = if ($env:QT_API) { $env:QT_API } else { "PyQt5" }
$brewPackage = if ($qtApi -match "6") { "qt@6" } else { "qt@5" }

$argsList = @(
    "--tool-path", (Resolve-Path -LiteralPath "$rootPath/Tools/HolocronToolset").Path
    "--venv-name", $venv_name
    "--pip-requirements", (Resolve-Path -LiteralPath "$rootPath/Libraries/PyKotor/requirements.txt").Path
    "--linux-package-profile", "qt_gui"
    "--qt-api", $qtApi
    "--qt-install-using-brew"
    "--brew-package", $brewPackage
)
if ($noprompt) { $argsList += "--noprompt" }

& "$scriptPath/deps_tool.ps1" @argsList
exit $LASTEXITCODE
