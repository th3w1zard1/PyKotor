#!/usr/bin/env pwsh

[CmdletBinding(PositionalBinding=$false)]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Passthru
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptDir "deps_tool.py"
$pythonExe = if ($env:pythonExePath) { $env:pythonExePath } else { "python" }

Write-Host "Delegating to deps_tool.py with arguments: $Passthru"
& $pythonExe $pythonScript @Passthru
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

