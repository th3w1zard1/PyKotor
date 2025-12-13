#!/usr/bin/env pwsh

[CmdletBinding(PositionalBinding=$false)]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Passthru
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRoot = (Resolve-Path "$scriptDir/..").Path
$pythonScript = Join-Path $scriptDir "compile_tool.py"

# Source install_python_venv.ps1 to set up the venv and Python environment
# This properly activates the venv in the current PowerShell session
$venvInstaller = Join-Path $repoRoot "install_python_venv.ps1"
if (Test-Path $venvInstaller) {
    Write-Host "Sourcing install_python_venv.ps1 to set up Python environment..."
    # Extract venv_name and noprompt from Passthru if present
    $venvName = ".venv"
    $nopromptFlag = $false
    for ($i = 0; $i -lt $Passthru.Count; $i++) {
        if ($Passthru[$i] -eq "--venv-name" -and ($i + 1) -lt $Passthru.Count) {
            $venvName = $Passthru[$i + 1]
        }
        if ($Passthru[$i] -eq "--noprompt") {
            $nopromptFlag = $true
        }
    }
    
    # Source the script with . to run it in the current session
    if ($nopromptFlag) {
        . $venvInstaller -noprompt -venv_name $venvName
    } else {
        . $venvInstaller -venv_name $venvName
    }
    
    # Add --skip-venv to Passthru since we've already handled venv setup
    $Passthru += "--skip-venv"
}

$pythonExe = if ($env:pythonExePath) { $env:pythonExePath } else { "python" }

# If pythonExePath is set, pass it to compile_tool.py so it uses the venv Python
# This is critical when --skip-venv is used (venv already created)
if ($env:pythonExePath) {
    $Passthru += @("--python-exe", $env:pythonExePath)
}

Write-Host "Delegating to compile_tool.py with arguments: $Passthru"
& $pythonExe $pythonScript @Passthru
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

