#!/usr/bin/env pwsh

[CmdletBinding(PositionalBinding=$false)]
param(
  [switch]$noprompt,
  [string]$venv_name = ".venv"
)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Resolve-Path -LiteralPath "$scriptPath/..").Path

$argsList = @(
    "--tool-path", (Resolve-Path -LiteralPath "$rootPath/Tools/BatchPatcher").Path
    "--venv-name", $venv_name
    "--linux-package-profile", "tk"
    "--pip-requirements", (Resolve-Path -LiteralPath "$rootPath/Libraries/PyKotor/requirements.txt").Path
)
if ($noprompt) { $argsList += "--noprompt" }

& "$scriptPath/deps_tool.ps1" @argsList
exit $LASTEXITCODE
