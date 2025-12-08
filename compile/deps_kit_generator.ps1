#!/usr/bin/env pwsh

[CmdletBinding(PositionalBinding=$false)]
param(
  [switch]$noprompt,
  [string]$venv_name = ".venv"
)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Resolve-Path -LiteralPath "$scriptPath/..").Path

$argsList = @(
    "--tool-path", (Resolve-Path -LiteralPath "$rootPath/Tools/KitGenerator").Path
    "--venv-name", $venv_name
    "--pip-requirements", (Resolve-Path -LiteralPath "$rootPath/Libraries/PyKotor/requirements.txt").Path
    "--pypy-pyinstaller-spec", "pyinstaller>=6.3.0,!=6.15.0,!=6.15.1,!=6.16.0"
    "--windows-extra-pip", "pywin32-ctypes"
    "--windows-cpython-pip", "pywin32"
)
if ($noprompt) { $argsList += "--noprompt" }

& "$scriptPath/deps_tool.ps1" @argsList
exit $LASTEXITCODE
