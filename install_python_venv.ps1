#!/usr/bin/env pwsh
<# 
    install_python_venv.ps1
    Robust, idempotent Python + venv bootstrapper for PyKotor.

    Key improvements:
    - Single consistent error trap; respects -noprompt.
    - Structured logging with configurable levels (Trace|Debug|Info|Warn|Error|Silent).
    - OS/distro detection without WMI on non-Windows.
    - Idempotent venv creation/activation; clear reuse semantics.
    - Non-interactive mode honored everywhere (no stray Read-Host).
    - Secure downloads with retry logic and optional SHA256 verification.
    - Centralized version map; defaults to Python 3.13.x, pip/setuptools recent pins.
    - Proper dry-run support throughout all operations.
    - Enhanced .env loading with value masking (unless -ShowEnvValues).
    - Proper exit codes for success/failure scenarios.
#>

[CmdletBinding(PositionalBinding = $false)]
param(
    [switch]$noprompt,
    [string]$venv_name = ".venv",
    [string]$force_python_version,     # MAJOR.MINOR; overrides default target
    [switch]$forceInstall,             # proceed with installs without prompts
    [switch]$skipVenv,                 # only detect/ensure python, skip venv creation
    [switch]$skipEnvLoad,              # skip loading .env
    [switch]$dryRun,                   # print planned actions, make no changes
    [switch]$acceptLicense,            # auto-accept external installer licenses
    [string]$logLevel = "Info",        # Trace|Debug|Info|Warn|Error|Silent
    [string]$venvPathOverride,         # explicit venv path if not repo-root joined
    [switch]$ShowEnvValues             # when loading .env, print full values (otherwise masked)
)

#region Globals and configuration
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
$script:ExitCode = 1
$script:ErrorVerbosity = 3  # Compatibility with old error handler

# Detect whether this script is being dot-sourced.
# When dot-sourced, we MUST NOT call `exit`, because that terminates the caller's PowerShell session
# (e.g., a GitHub Actions step). In that case, we `return` on success and `throw` on failure,
# while still setting $env:pythonExePath and activating the venv in the caller session.
$script:IsDotSourced = $MyInvocation.InvocationName -eq '.'

# Normalize log level
$script:LogLevels = @{
    "Trace"  = 0
    "Debug"  = 1
    "Info"   = 2
    "Warn"   = 3
    "Error"  = 4
    "Silent" = 5
}
if (-not $script:LogLevels.ContainsKey($logLevel)) { $logLevel = "Info" }
$script:CurrentLogLevel = $script:LogLevels[$logLevel]

# Centralized version pins (override with -force_python_version if desired)
$script:VersionPins = [pscustomobject]@{
    PythonDefaultMajorMinor = "3.13"
    PythonAltMajors         = @("3.13", "3.12", "3.11", "3.10", "3.9", "3.8")
    PythonSources           = @{
        "3.7"  = "3.7.17"
        "3.8"  = "3.8.19"
        "3.9"  = "3.9.20"
        "3.10" = "3.10.15"
        "3.11" = "3.11.10"
        "3.12" = "3.12.8"
        "3.13" = "3.13.0"
    }
    PythonSourcesMac = @{
        "3.7"  = "3.7.9"
        "3.8"  = "3.8.10"
        "3.9"  = "3.9.13"
        "3.10" = "3.10.11"
        "3.11" = "3.11.8"
        "3.12" = "3.12.2"
        "3.13" = "3.13.0"
    }
    PythonSourcesWin = @{
        "3.7"  = "3.7.9"
        "3.8"  = "3.8.10"
        "3.9"  = "3.9.13"
        "3.10" = "3.10.11"
        "3.11" = "3.11.8"
        "3.12" = "3.12.2"
        "3.13" = "3.13.0"
    }
    PipVersion        = "24.3.1"
    SetuptoolsVersion = "75.2.0"
    TclTkVersion      = "8.6.14"
    MinPythonVersion  = [Version]"3.7.0"
    MaxPythonVersion  = [Version]"3.14.0"
    RecommendedVersion = [Version]"3.8.10"
}

# Repo paths
$scriptPath   = $MyInvocation.MyCommand.Definition
$repoRootPath = (Resolve-Path -LiteralPath (Join-Path -Path $scriptPath -ChildPath "..")).Path
$pathSep      = [IO.Path]::DirectorySeparatorChar
$venvPath     = if ($venvPathOverride) { $venvPathOverride } else { Join-Path -Path $repoRootPath -ChildPath $venv_name }

# Global python state
$global:force_python_version = $force_python_version
$global:pythonInstallPath = ""
$global:pythonVersion = ""

# Console colors toggle
$script:UseColor = $Host.UI -and $Host.UI.SupportsVirtualTerminal
#endregion Globals

#region Logging helpers
function Write-Log {
    param(
        [Parameter(Mandatory = $true)][ValidateSet("Trace", "Debug", "Info", "Warn", "Error")]
        [string]$Level,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if ($script:LogLevels[$Level] -lt $script:CurrentLogLevel) { return }
    $prefix = "[{0}] " -f $Level.ToUpper()
    $color = switch ($Level) {
        "Trace" { "DarkGray" }
        "Debug" { "Gray" }
        "Info"  { "White" }
        "Warn"  { "Yellow" }
        "Error" { "Red" }
    }
    if ($script:UseColor) { Write-Host "$prefix$Message" -ForegroundColor $color }
    else { Write-Host "$prefix$Message" }
}

function Throw-Logged {
    param([string]$Message)
    Write-Log -Level "Error" -Message $Message
    throw $Message
}
#endregion Logging

#region Error handling
trap {
    $err = $_
    if ($null -eq $err) { $err = $Error[0] }
    
    Write-Log -Level "Error" -Message ("Unhandled error: {0}" -f $err.Exception.Message)
    
    if ($script:ErrorVerbosity -ge 2 -and $err.ScriptStackTrace) {
        Write-Log -Level "Debug" -Message $err.ScriptStackTrace
    }
    
    if ($script:ErrorVerbosity -ge 3 -and $err.InvocationInfo) {
        $inv = $err.InvocationInfo
        Write-Log -Level "Debug" -Message "At line $($inv.ScriptLineNumber): $($inv.Line.Trim())"
    }
    
    $global:LASTEXITCODE = 1
    $script:ExitCode = 1
    
    if (-not $noprompt) {
        Write-Host "Press Enter to exit..."
        Read-Host
    }
    if ($script:IsDotSourced) {
        throw $err
    }
    exit 1
}

function Handle-Error {
    param (
        [Parameter(Mandatory = $true)][System.Management.Automation.ErrorRecord]$ErrorRecord,
        [int]$Verbosity = $script:ErrorVerbosity
    )
    if ($Verbosity -eq 0 -or $Verbosity -eq 5) { return }

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss,fff"
    $excType = $ErrorRecord.Exception.GetType().FullName
    $excMessage = $ErrorRecord.Exception.Message
    $helpLink = $ErrorRecord.Exception.HelpLink

    if ($Verbosity -ge 1) {
        Write-Host -ForegroundColor Red "$timestamp - $excType"
        Write-Host -ForegroundColor Red $excMessage
        if ($ErrorRecord.InvocationInfo) {
            Write-Host -ForegroundColor Red "Line $($ErrorRecord.InvocationInfo.ScriptLineNumber): $($ErrorRecord.InvocationInfo.Line.Trim())"
        }
    }

    if ($Verbosity -ge 2) {
        Write-Host -ForegroundColor Red "Traceback (most recent call last):"
        if ($null -ne (Get-Member -InputObject $ErrorRecord -Name ScriptStackTrace -ErrorAction SilentlyContinue)) {
            Write-Host -ForegroundColor Red $ErrorRecord.ScriptStackTrace
        }
        else {
            $callStack = Get-PSCallStack
            for ($i = 0; $i -lt $callStack.Count; $i++) {
                $frame = $callStack[$i]
                Write-Host -ForegroundColor Red "  File `"$($frame.ScriptName)`", line $($frame.ScriptLineNumber), in $($frame.FunctionName)"
            }
        }
    }

    if ($Verbosity -ge 3 -and $null -ne $ErrorRecord.InvocationInfo) {
        $invInfo = $ErrorRecord.InvocationInfo
        Write-Host -ForegroundColor Red "    OffsetInLine = $($invInfo.OffsetInLine)"
        Write-Host -ForegroundColor Red "    ScriptName = `"$($invInfo.ScriptName)`""
        Write-Host -ForegroundColor Red "    InvocationName = `"$($invInfo.InvocationName)`""
    }
}

function Format-VariableOutput {
    param ($value, [int]$maxLength = 100, [int]$maxDepth = 3, [int]$currentDepth = 0)
    if ($currentDepth -ge $maxDepth) { return "<max depth reached>" }
    if ($null -eq $value) { return "None" }
    elseif ($value -is [string]) { return "`"$($value.Substring(0, [Math]::Min($value.Length, $maxLength)))$(if ($value.Length -gt $maxLength) {"..."})`"" }
    elseif ($value -is [int] -or $value -is [double]) { return $value.ToString() }
    elseif ($value -is [bool]) { return $value.ToString().ToLower() }
    elseif ($value -is [array] -or $value -is [System.Collections.IList]) {
        $elements = $value | Select-Object -First 10 | ForEach-Object { Format-VariableOutput $_ -maxLength $maxLength -maxDepth $maxDepth -currentDepth ($currentDepth + 1) }
        $var_output = "[" + ($elements -join ", ") + $(if ($value.Count -gt 10) { ", ..." }) + "]"
        return $(if ($var_output.Length -gt $maxLength) { $var_output.Substring(0, $maxLength) + "..." } else { $var_output })
    }
    elseif ($value -is [hashtable] -or $value -is [System.Collections.IDictionary]) {
        $elements = $value.GetEnumerator() | Select-Object -First 10 | ForEach-Object { 
            "$((Format-VariableOutput $_.Key -maxLength $maxLength -maxDepth $maxDepth -currentDepth ($currentDepth + 1))) = $((Format-VariableOutput $_.Value -maxLength $maxLength -maxDepth $maxDepth -currentDepth ($currentDepth + 1)))"
        }
        $var_output = "{" + ($elements -join ", ") + $(if ($value.Count -gt 10) { ", ..." }) + "}"
        return $(if ($var_output.Length -gt $maxLength) { $var_output.Substring(0, $maxLength) + "..." } else { $var_output })
    }
    else {
        $var_output = $value.ToString()
        return $(if ($var_output.Length -gt $maxLength) { $var_output.Substring(0, $maxLength) + "..." } else { $var_output })
    }
}
#endregion Error handling

#region Utility helpers
function Test-Command {
    param([Parameter(Mandatory = $true)][string]$Name)
    return [bool](Get-Command -Name $Name -ErrorAction SilentlyContinue)
}

function Require-Command {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [string]$InstallHint
    )
    if (-not (Test-Command $Name)) {
        if ($InstallHint) {
            Throw-Logged "$Name is required. $InstallHint"
        }
        else {
            Throw-Logged "$Name is required but not found."
        }
    }
}

function Confirm-Action {
    param(
        [string]$Prompt,
        [switch]$DefaultYes
    )
    if ($dryRun) {
        Write-Log -Level "Info" -Message "[dry-run] Would prompt: $Prompt"
        return $true
    }
    if ($noprompt -or $forceInstall) { return $true }
    $suffix = if ($DefaultYes) { " [Y/n]" } else { " [y/N]" }
    $resp = Read-Host "$Prompt$suffix"
    if ($DefaultYes) { return ($resp -eq "" -or $resp -match '^(?i)y') }
    return ($resp -match '^(?i)y')
}

function Mask-Value {
    param([string]$Value)
    if ($ShowEnvValues) { return $Value }
    if ($Value.Length -le 4) { return "***" }
    return ("{0}***" -f $Value.Substring(0, 4))
}
#endregion Utility helpers

#region OS detection
function Get-OS {
    if ($IsWindows) { return "Windows" }
    elseif ($IsMacOS) { return "Mac" }
    elseif ($IsLinux) { return "Linux" }
    
    # Fallback for older PowerShell
    try {
        $os = (Get-WmiObject -Class Win32_OperatingSystem -ErrorAction SilentlyContinue).Caption
        if ($os -match "Windows") { return "Windows" }
        elseif ($os -match "Mac") { return "Mac" }
        elseif ($os -match "Linux") { return "Linux" }
    }
    catch {
        Write-Log -Level "Warn" -Message "Could not determine OS via WMI"
    }
    
    Write-Error "Unknown Operating System"
    if (-not $noprompt) {
        Write-Host "Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    exit 1
}

function Get-Linux-Distro-Name {
    if (-not (Test-Path "/etc/os-release" -ErrorAction SilentlyContinue)) { return $null }
    $osInfo = Get-Content "/etc/os-release" -Raw
    if ($osInfo -match '\nID="?([^"\n]*)"?') {
        $distroName = $Matches[1].Trim('"')
        if ($distroName -eq "ol") { return "oracle" }
        return $distroName
    }
    return $null
}

function Get-Linux-Distro-Version {
    if (-not (Test-Path "/etc/os-release" -ErrorAction SilentlyContinue)) { return $null }
    $osInfo = Get-Content "/etc/os-release" -Raw
    if ($osInfo -match '\nVERSION_ID="?([^"\n]*)"?') {
        return $Matches[1].Trim('"')
    }
    return $null
}
#endregion OS detection

#region Path/environment setup
$currentOS = Get-OS
Write-Log -Level "Debug" -Message "Detected OS: $currentOS"
Write-Log -Level "Debug" -Message "Script path: $scriptPath"
Write-Log -Level "Debug" -Message "Repo root: $repoRootPath"

# Setup LD_LIBRARY_PATH on Unix
if ($currentOS -ne "Windows") {
    $ldLibraryPath = [System.Environment]::GetEnvironmentVariable('LD_LIBRARY_PATH', 'Process')
    if ([string]::IsNullOrEmpty($ldLibraryPath)) {
        Write-Log -Level "Warn" -Message "LD_LIBRARY_PATH not defined, creating it with /usr/lib:/usr/local/lib"
        [System.Environment]::SetEnvironmentVariable('LD_LIBRARY_PATH', '/usr/lib:/usr/local/lib', 'Process')
    }
    elseif (-not $ldLibraryPath.Contains('/usr/local/lib')) {
        Write-Log -Level "Warn" -Message "Adding /usr/local/lib to LD_LIBRARY_PATH"
        $newLdLibraryPath = $ldLibraryPath + ':/usr/local/lib'
        if (-not $newLdLibraryPath.Contains('/usr/lib')) {
            $newLdLibraryPath += ':/usr/lib'
        }
        [System.Environment]::SetEnvironmentVariable('LD_LIBRARY_PATH', $newLdLibraryPath, 'Process')
    }
}

# Check for admin rights on Windows
if ($currentOS -eq "Windows" -and -NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Log -Level "Warn" -Message "Please run PowerShell with administrator rights for best results"
}
#endregion Path/environment setup

#region Download + checksum
function Invoke-Download {
    param(
        [Parameter(Mandatory = $true)][string]$Uri,
        [Parameter(Mandatory = $true)][string]$Destination,
        [string]$Sha256,
        [string]$Description = "file",
        [int]$Retries = 3
    )
    if ($dryRun) {
        Write-Log -Level "Info" -Message "[dry-run] Would download $Description from $Uri to $Destination"
        return $true
    }
    
    for ($i = 1; $i -le $Retries; $i++) {
        try {
            Write-Log -Level "Info" -Message "Downloading $Description (attempt $i/$Retries)..."
            Invoke-WebRequest -Uri $Uri -OutFile $Destination -UseBasicParsing
            
            if ($Sha256) {
                $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Destination).Hash.ToLowerInvariant()
                if ($hash -ne $Sha256.ToLowerInvariant()) {
                    Throw-Logged "SHA256 mismatch for $Description. Expected $Sha256, got $hash"
                }
                Write-Log -Level "Debug" -Message "SHA256 verified for $Description"
            }
            return $true
        }
        catch {
            if ($i -eq $Retries) {
                Handle-Error -ErrorRecord $_
                throw
            }
            Write-Log -Level "Warn" -Message "Download attempt $i failed, retrying..."
            Start-Sleep -Seconds 2
        }
    }
    return $false
}
#endregion Download + checksum

#region Bash command helpers
function Invoke-BashCommand {
    param ([string]$Command)
    
    if ($dryRun) {
        Write-Log -Level "Info" -Message "[dry-run] Would run bash: $Command"
        return ""
    }
    
    try {
        $output = & bash -c $Command 2>&1
        if (-not $? -or $LASTEXITCODE -ne 0) {
            throw "Bash command '$Command' failed with exit code $LASTEXITCODE. Output: $output"
        }
        return $output
    }
    catch {
        throw "Failed to execute Bash command '$Command'. Error: $_"
    }
}

function Invoke-BashCommandOptional {
    param (
        [string]$Command,
        [string]$FallbackMessage = "Command failed but continuing"
    )
    
    if ($dryRun) {
        Write-Log -Level "Info" -Message "[dry-run] Would run bash (optional): $Command"
        return $true
    }
    
    try {
        & bash -c $Command 2>&1
        if (-not $? -or $LASTEXITCODE -ne 0) {
            Write-Log -Level "Warn" -Message "$FallbackMessage. Exit code: $LASTEXITCODE"
            return $false
        }
        return $true
    }
    catch {
        Write-Log -Level "Warn" -Message "$FallbackMessage. Error: $_"
        return $false
    }
}
#endregion Bash command helpers

#region Python version parsing
function Get-Python-Version {
    Param ([string]$pythonPath)

    $parseVersionString = {
        param([string]$versionString)
        if ([string]::IsNullOrWhiteSpace($versionString)) { return $null }
        $trimmed = $versionString.Trim()
        $match = [System.Text.RegularExpressions.Regex]::Match($trimmed, '(\d+)(\.\d+){1,3}')
        if (-not $match.Success) { return $null }
        $numericVersion = $match.Value
        $segments = $numericVersion.Split('.')
        while ($segments.Count -lt 3) { $segments += '0' }
        return [Version]::Parse(($segments -join '.'))
    }

    try {
        if (-not (Test-Path $pythonPath -ErrorAction SilentlyContinue)) {
            return [Version]"0.0.0"
        }
        
        $pythonVersionOutput = & $pythonPath --version 2>&1 | Out-String
        $pythonVersion = & $parseVersionString $pythonVersionOutput

        if ($null -eq $pythonVersion) {
            $platformVersionOutput = & $pythonPath -c "import platform; print(platform.python_version())" 2>&1 | Out-String
            $pythonVersion = & $parseVersionString $platformVersionOutput
        }

        if ($null -eq $pythonVersion) {
            $sysVersionOutput = & $pythonPath -c "import sys; print('.'.join(str(x) for x in sys.version_info[:3]))" 2>&1 | Out-String
            $pythonVersion = & $parseVersionString $sysVersionOutput
        }

        if ($null -ne $pythonVersion) { return $pythonVersion }
    }
    catch {
        Write-Log -Level "Debug" -Message "Failed to parse python version for path '$pythonPath': $($_.Exception.Message)"
    }

    return [Version]"0.0.0"
}
#endregion Python version parsing

#region Python discovery
function Get-PythonPaths {
    Param ([string]$version)

    $windowsVersion = $version -replace '\.', ''

    $windowsPaths = @(
        "C:\Program Files\Python$windowsVersion\python.exe",
        "$env:ProgramFiles\Python$windowsVersion\python.exe",
        "C:\Program Files (x86)\Python$windowsVersion\python.exe",
        "$env:ProgramFiles(x86)\Python$windowsVersion\python.exe"
        "C:\Program Files\Python$windowsVersion-32\python.exe",
        "C:\Program Files (x86)\Python$windowsVersion-32\python.exe",
        "$env:USERPROFILE\AppData\Local\Programs\Python\Python$windowsVersion\python.exe",
        "$env:USERPROFILE\AppData\Local\Programs\Python\Python$windowsVersion-32\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python$windowsVersion-64\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python$windowsVersion\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python$windowsVersion-32\python.exe"
    )

    $linuxAndMacPaths = @(
        "/usr/local/bin/python$version",
        "/usr/bin/python$version",
        "/bin/python$version",
        "/sbin/python$version",
        "~/.local/bin/python$version",
        "~/.pyenv/versions/$version/bin/python3",
        "~/.pyenv/versions/$version/bin/python",
        "/usr/local/Cellar/python/$version/bin/python3",
        "/opt/local/bin/python$version",
        "/opt/python$version"
    )

    return @{ Windows = $windowsPaths; Linux = $linuxAndMacPaths; Mac = $linuxAndMacPaths }
}

function Test-PythonCommand {
    param ([string]$CommandName)
    
    $pythonCommand = Get-Command -Name $CommandName -ErrorAction SilentlyContinue
    if ($null -eq $pythonCommand) { return $false }
    
    $testPath = $pythonCommand.Source
    $testVersion = Get-Python-Version $testPath
    
    if ($testVersion -ge $VersionPins.MinPythonVersion -and $testVersion -lt $VersionPins.MaxPythonVersion) {
        Write-Log -Level "Info" -Message "Found python command '$CommandName' with version $testVersion at path $testPath"
        $global:pythonInstallPath = $testPath
        $global:pythonVersion = $testVersion
        return $true
    }
    else {
        Write-Log -Level "Debug" -Message "Python '$testPath' version '$testVersion' not in supported range"
    }
    return $false
}

function Find-Python {
    Param ([bool]$installIfNotFound)
    
    # Check existing global path
    if ($global:pythonInstallPath) {
        $testVersion = Get-Python-Version -pythonPath $global:pythonInstallPath
        if ($testVersion -ne [Version]"0.0.0" -and 
            $testVersion -ge $VersionPins.MinPythonVersion -and 
            $testVersion -lt $VersionPins.MaxPythonVersion) {
            Write-Log -Level "Info" -Message "Using existing Python $testVersion at $global:pythonInstallPath"
            $global:pythonVersion = $testVersion
            return
        }
    }

    # Determine versions to search for
    if ($global:force_python_version) {
        $fallbackVersion = $global:force_python_version
        $pythonVersions = @("python$fallbackVersion")
    }
    else {
        $fallbackVersion = "{0}.{1}" -f $VersionPins.RecommendedVersion.Major, $VersionPins.RecommendedVersion.Minor
        $pythonVersions = @('python3.13', 'python3.12', 'python3.11', 'python3.10', 'python3.9', 'python3.8', 'python3', 'python')
    }

    # Search via commands
    foreach ($pyCmd in $pythonVersions) {
        if (Test-PythonCommand -CommandName $pyCmd) {
            break
        }
    }

    # Search via paths if not found
    if (-not $global:pythonInstallPath) {
        foreach ($version in $pythonVersions) {
            $versionNum = $version -replace "python", ""
            if (-not $versionNum) { continue }
            $paths = (Get-PythonPaths $versionNum)[$currentOS]
            foreach ($path in $paths) {
                try {
                    $resolvedPath = [Environment]::ExpandEnvironmentVariables($path)
                    if (Test-Path $resolvedPath -ErrorAction SilentlyContinue) {
                        $thisVersion = Get-Python-Version $resolvedPath
                        if ($thisVersion -ge $VersionPins.MinPythonVersion -and $thisVersion -le $VersionPins.MaxPythonVersion) {
                            if (-not $global:pythonInstallPath -or $thisVersion -le $VersionPins.RecommendedVersion) {
                                Write-Log -Level "Info" -Message "Found Python $thisVersion at '$resolvedPath'"
                                $global:pythonInstallPath = $resolvedPath
                                $global:pythonVersion = $thisVersion
                            }
                            
                            # Special handling for Debian/Ubuntu altinstall
                            if ($resolvedPath.StartsWith("/usr/local/bin/python")) {
                                $distro = Get-Linux-Distro-Name
                                if ($distro -eq "debian" -or $distro -eq "ubuntu") {
                                    Write-Log -Level "Debug" -Message "Altinstall detected, using $resolvedPath"
                                    return
                                }
                            }
                        }
                    }
                }
                catch {
                    Write-Log -Level "Debug" -Message "Error checking path ${path}: $_"
                }
            }
        }
    }
    
    # Debian/Ubuntu: ensure venv packages even if Python exists
    if ($installIfNotFound) {
        $distro = Get-Linux-Distro-Name
        if ($distro -eq "debian" -or $distro -eq "ubuntu") {
            if ($global:pythonVersion) {
                $shortVersion = "{0}.{1}" -f $global:pythonVersion.Major, $global:pythonVersion.Minor
            }
            else {
                $shortVersion = $fallbackVersion
            }
            Write-Log -Level "Debug" -Message "Ensuring venv packages for Python $shortVersion on $distro"
            Install-Python-Linux -pythonVersion $shortVersion
        }
    }

    # Install if not found
    if (-not $global:pythonInstallPath) {
        if (-not $installIfNotFound) { return }
        
        $displayVersion = if ($global:force_python_version) { $global:force_python_version } else { $VersionPins.RecommendedVersion }
        
        if (-not (Confirm-Action -Prompt "Python $displayVersion not found. Install it?" -DefaultYes)) {
            Throw-Logged "User declined installation; cannot proceed."
        }
        
        try {
            switch ($currentOS) {
                "Windows" { Install-PythonWindows -pythonVersion $fallbackVersion }
                "Linux"   { Install-Python-Linux -pythonVersion $fallbackVersion }
                "Mac"     { Install-Python-Mac -pythonVersion $fallbackVersion }
            }
        }
        catch {
            Handle-Error -ErrorRecord $_
            Throw-Logged "Python installation failed"
        }
        
        Write-Log -Level "Info" -Message "Searching for Python again after installation..."
        Find-Python -installIfNotFound $false
    }
}
#endregion Python discovery

#region Tcl/Tk installation
function Install-TclTk {
    function Test-TclTkVersion($command, $scriptCommand, $requiredVersion) {
        $commandInfo = Get-Command -Name $command -ErrorAction SilentlyContinue
        if (-not $commandInfo) {
            if ($command -eq 'wish') {
                $versionSpecificCommand = Get-Command 'wish*' -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($null -ne $versionSpecificCommand) {
                    Write-Log -Level "Info" -Message "Symlinking $($versionSpecificCommand.Source) to /usr/local/bin/wish"
                    Invoke-BashCommand "sudo ln -sv $($versionSpecificCommand.Source) /usr/local/bin/wish"
                    return $true
                }
            }
            return $false
        }
    
        try {
            $versionScript = "echo `$scriptCommand` | $command"
            $versionString = Invoke-Expression $versionScript 2>&1
            if ([string]::IsNullOrWhiteSpace($versionString)) { return $false }
            $versionString = $versionString -replace '[^\d.]+', ''
            if ([string]::IsNullOrEmpty($versionString)) { return $false }
            $version = New-Object System.Version $versionString.Trim()
            return $version -ge $requiredVersion
        }
        catch {
            return $false
        }
    }
    
    $tclVersionScript = "puts [info patchlevel];exit"
    $tkVersionScript = "puts [info patchlevel];exit"
    $recommendedVersion = $VersionPins.TclTkVersion
    $requiredVersion = New-Object System.Version "8.6.0"
    
    $tclCheck = Test-TclTkVersion "tclsh" $tclVersionScript $requiredVersion
    $tkCheck = Test-TclTkVersion "wish" $tkVersionScript $requiredVersion

    if ($tclCheck -and $tkCheck) {
        Write-Log -Level "Info" -Message "Tcl/Tk $requiredVersion or higher already installed"
        return
    }

    Write-Log -Level "Info" -Message "Tcl/Tk needs to be installed or updated"

    if ($currentOS -eq "Mac") {
        try {
            $macOSVersion = Invoke-BashCommand -Command "sw_vers -productVersion"
            $majorMacOSVersion = [int]$macOSVersion.Split('.')[0]
            if ($majorMacOSVersion -ge 11 -or ($majorMacOSVersion -eq 10 -and [int]$macOSVersion.Split('.')[1] -ge 12)) {
                Invoke-BashCommandOptional -Command 'brew install tcl-tk --overwrite --force || true' -FallbackMessage "Brew install tcl-tk failed"
                return
            }
        }
        catch {
            Write-Log -Level "Warn" -Message "Could not install Tcl/Tk via brew: $_"
        }
    }

    # Install from source
    if ($dryRun) {
        Write-Log -Level "Info" -Message "[dry-run] Would install Tcl/Tk $recommendedVersion from source"
        return
    }
    
    $originalDir = Get-Location
    try {
        Write-Log -Level "Info" -Message "Installing Tcl from source..."
        Invoke-BashCommand "curl -O -L https://prdownloads.sourceforge.net/tcl/tcl$recommendedVersion-src.tar.gz"
        Invoke-BashCommand "tar -xzvf tcl$recommendedVersion-src.tar.gz"
        Set-Location "tcl$recommendedVersion/unix"
        Invoke-BashCommand "./configure --prefix=/usr/local"
        Invoke-BashCommand "make"
        Invoke-BashCommand "sudo make install"

        Set-Location $originalDir
        Write-Log -Level "Info" -Message "Installing Tk from source..."
        Invoke-BashCommand "curl -O -L https://prdownloads.sourceforge.net/tcl/tk$recommendedVersion-src.tar.gz"
        Invoke-BashCommand "tar -xzvf tk$recommendedVersion-src.tar.gz"
        Set-Location "tk$recommendedVersion/unix"
        Invoke-BashCommand "./configure --prefix=/usr/local --with-tcl=/usr/local/lib"
        Invoke-BashCommand "make"
        Invoke-BashCommand "sudo make install"
    }
    finally {
        Set-Location $originalDir
    }
}
#endregion Tcl/Tk installation

#region Python installation - Windows
function Install-PythonWindows {
    Param ([string]$pythonVersion)
    
    $pyVersion = $VersionPins.PythonSourcesWin[$pythonVersion]
    if (-not $pyVersion) {
        Throw-Logged "Unsupported Python version '$pythonVersion' for Windows"
    }
    
    $installerName = if ([System.Environment]::Is64BitOperatingSystem) {
        "python-$pyVersion-amd64.exe"
    }
    else {
        "python-$pyVersion.exe"
    }
    
    if ($env:GITHUB_ACTIONS -eq "true" -and $env:MATRIX_ARCH) {
        $installerName = switch ($env:MATRIX_ARCH) {
            "x86" { "python-$pyVersion.exe" }
            "x64" { "python-$pyVersion-amd64.exe" }
            default { $installerName }
        }
    }

    $pythonInstallerUrl = "https://www.python.org/ftp/python/$pyVersion/$installerName"
    $installerPath = "$env:TEMP\$installerName"
    
    Invoke-Download -Uri $pythonInstallerUrl -Destination $installerPath -Description "Python $pyVersion installer"
    
    if ($dryRun) { return $true }
    
    $logPath = Join-Path (Get-Location).Path "PythonInstall.log"
    Write-Log -Level "Info" -Message "Installing Python $pyVersion..."
    Start-Process -FilePath $installerPath -Args "/quiet /log $logPath InstallAllUsers=0 PrependPath=1 InstallLauncherAllUsers=0" -Wait -NoNewWindow
    
    Write-Log -Level "Debug" -Message "Python installation log:"
    if (Test-Path $logPath) {
        Get-Content -Path $logPath | ForEach-Object { Write-Log -Level "Debug" -Message $_ }
    }
    
    # Refresh PATH
    $systemPath = Get-ItemProperty -Path 'Registry::HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Session Manager\Environment' -Name PATH | Select-Object -ExpandProperty PATH
    $userPath = Get-ItemProperty -Path 'Registry::HKEY_CURRENT_USER\Environment' -Name PATH | Select-Object -ExpandProperty PATH
    $env:Path = $userPath + ";" + $systemPath
    
    Remove-Item -LiteralPath $installerPath -ErrorAction SilentlyContinue
    return $true
}
#endregion Python installation - Windows

#region Python installation - macOS
function Install-Python-Mac {
    Param ([string]$pythonVersion)

    $pyVersion = $VersionPins.PythonSourcesMac[$pythonVersion]
    if (-not $pyVersion) {
        Throw-Logged "Unsupported Python version '$pythonVersion' for macOS"
    }
    
    $pythonInstallers = @{
        "3.7"  = @("python-$pyVersion-macosx10.9.pkg")
        "3.8"  = @("python-$pyVersion-macos11.pkg", "python-$pyVersion-macosx10.9.pkg")
        "3.9"  = @("python-$pyVersion-macos11.pkg", "python-$pyVersion-macosx10.9.pkg")
        "3.10" = @("python-$pyVersion-macos11.pkg")
        "3.11" = @("python-$pyVersion-macos11.pkg")
        "3.12" = @("python-$pyVersion-macos11.pkg")
        "3.13" = @("python-$pyVersion-macos11.pkg")
    }

    Install-TclTk

    try {
        $macOSVersion = bash -c "sw_vers -productVersion"
        $majorMacOSVersion = [int]$macOSVersion.Split('.')[0]

        $installerSelection = $pythonInstallers[$pythonVersion] | Where-Object {
            $_ -match "macos($majorMacOSVersion)"
        } | Select-Object -First 1

        if (-not $installerSelection) {
            $installerSelection = $pythonInstallers[$pythonVersion] | Select-Object -First 1
            Write-Log -Level "Warn" -Message "No exact macOS version match, using $installerSelection"
        }

        $pythonInstallerUrl = "https://www.python.org/ftp/python/$pyVersion/$installerSelection"
        $installerPath = "/tmp/$installerSelection"
        
        Invoke-Download -Uri $pythonInstallerUrl -Destination $installerPath -Description "Python $pyVersion pkg"
        
        if (-not $dryRun) {
            Invoke-BashCommand "sudo installer -pkg $installerPath -target /"
            Remove-Item -LiteralPath $installerPath -ErrorAction SilentlyContinue
        }
        return $true
    }
    catch {
        Handle-Error -ErrorRecord $_
        Write-Log -Level "Warn" -Message "PKG install failed, trying source build..."
        try {
            Install-PythonUnixSource -pythonVersion $pythonVersion
            return $true
        }
        catch {
            Handle-Error -ErrorRecord $_
            Write-Log -Level "Warn" -Message "Source build failed, trying brew..."
            bash -c "brew install python@$pyVersion python-tk@$pyVersion"
            return $true
        }
    }
}
#endregion Python installation - macOS

#region Python installation - Linux
function Install-Python-Linux {
    Param ([string]$pythonVersion)

    if (-not $pythonVersion) { $pythonVersion = "3" }

    if (-not (Test-Path "/etc/os-release")) {
        Throw-Logged "Cannot determine Linux distribution"
    }

    $distro = Get-Linux-Distro-Name
    $versionId = Get-Linux-Distro-Version
    
    Write-Log -Level "Info" -Message "Installing Python $pythonVersion on $distro $versionId"
    
    try {
        switch ($distro) {
            "debian" {
                Invoke-BashCommand -Command "sudo apt-get update -y"
                $pipSuccess = Invoke-BashCommandOptional -Command "sudo apt-get install -y tk tcl libpython$pythonVersion-dev python$pythonVersion python$pythonVersion-dev python$pythonVersion-venv python$pythonVersion-pip" -FallbackMessage "pip package not available"
                if (-not $pipSuccess) {
                    Invoke-BashCommand -Command "sudo apt-get install -y tk tcl libpython$pythonVersion-dev python$pythonVersion python$pythonVersion-dev python$pythonVersion-venv"
                }
            }
            "ubuntu" {
                Invoke-BashCommand -Command "sudo apt-get update -y"
                $pipSuccess = Invoke-BashCommandOptional -Command "sudo apt-get install -y tk tcl libpython$pythonVersion-dev python$pythonVersion python$pythonVersion-dev python$pythonVersion-venv python$pythonVersion-pip" -FallbackMessage "pip package not available"
                if (-not $pipSuccess) {
                    Invoke-BashCommand -Command "sudo apt-get install -y tk tcl libpython$pythonVersion-dev python$pythonVersion python$pythonVersion-dev python$pythonVersion-venv"
                }
            }
            "alpine" {
                if ($pythonVersion -eq "3") {
                    Invoke-BashCommand -Command "sudo apk update"
                    Invoke-BashCommand -Command "sudo apk add --update --no-cache tk-dev tcl-dev tcl tk python$pythonVersion python$pythonVersion-tkinter"
                    Invoke-BashCommand -Command "if [ ! -f /usr/local/bin/python3 ]; then sudo ln -sf /usr/bin/python$pythonVersion /usr/local/bin/python3; fi"
                    Invoke-BashCommand -Command "sudo ln -sf /usr/bin/python$pythonVersion /usr/local/bin/python$pythonVersion"
                    Invoke-BashCommand -Command "/usr/local/bin/python$pythonVersion -m ensurepip"
                    Invoke-BashCommand -Command "/usr/local/bin/python$pythonVersion -m pip install --no-cache --upgrade pip setuptools"
                }
                else {
                    throw "Python version $pythonVersion not supported on Alpine via package manager"
                }
            }
            "fedora" {
                Invoke-BashCommand -Command "sudo dnf update -y"
                Invoke-BashCommand -Command "sudo dnf install python$pythonVersion python$pythonVersion-devel tk tcl tk-devel tcl-devel dnf-plugins-core -y"
            }
            "almalinux" {
                Invoke-BashCommand -Command "sudo dnf update -y"
                Invoke-BashCommand -Command "sudo dnf install python$pythonVersion python$pythonVersion-devel tk tcl tk-devel tcl-devel -y"
            }
            "centos" {
                Invoke-BashCommand -Command "sudo yum update -y"
                if ($versionId -eq "7") {
                    Invoke-BashCommand -Command "sudo yum install epel-release -y"
                }
                Invoke-BashCommand -Command "sudo yum install python$pythonVersion python$pythonVersion-devel tk tcl tk-devel tcl-devel -y"
            }
            "arch" {
                if ($pythonVersion -eq "3") {
                    Invoke-BashCommand -Command "sudo pacman-key --init"
                    Invoke-BashCommand -Command "sudo pacman-key --populate archlinux"
                    Invoke-BashCommand -Command "sudo pacman -Sy archlinux-keyring --noconfirm"
                    Invoke-BashCommand -Command "sudo pacman -Sy --noconfirm"
                    Invoke-BashCommand -Command "sudo pacman -Sy base-devel python-pip python tk tcl --noconfirm"
                }
                else {
                    throw "Package manager does not support version '$pythonVersion' on Arch"
                }
            }
            default {
                throw "Unsupported Linux distribution for package manager install: $distro"
            }
        }
        
        Find-Python -installIfNotFound $false
        if (-not $global:pythonInstallPath) {
            throw "Python not found after package install"
        }

        # Ensure pip
        try {
            & $global:pythonInstallPath -m pip --version 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Log -Level "Info" -Message "Bootstrapping pip with ensurepip..."
                & $global:pythonInstallPath -m ensurepip --upgrade --default-pip
            }
        }
        catch {
            Write-Log -Level "Warn" -Message "Failed to check/bootstrap pip: $_"
        }
    }
    catch {
        Handle-Error -ErrorRecord $_        
        if ($noprompt) {
            Write-Log -Level "Error" -Message "Non-interactive mode: cannot build from source"
            throw "Python installation failed in non-interactive mode"
        }
        
        if (-not (Confirm-Action -Prompt "Package install failed. Build from source?" -DefaultYes:$false)) {
            Throw-Logged "User declined source build"
        }

        # Install build dependencies
        Install-TclTk
        switch ($distro) {
            { $_ -in @("debian", "ubuntu") } {
                Invoke-BashCommand -Command 'sudo apt-get update -y'
                Invoke-BashCommand -Command 'sudo apt-get install -y tk tcl build-essential zlib1g-dev libncurses5-dev libgdbm-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev libbz2-dev tk-dev tcl-dev'
            }
            "alpine" {
                Invoke-BashCommand -Command 'sudo apk add --update --no-cache tk tcl tk-dev tcl-dev alpine-sdk linux-headers zlib-dev bzip2-dev readline-dev sqlite-dev openssl-dev libffi-dev'
            }
            { $_ -in @("fedora", "almalinux", "centos") } {
                $pkgMgr = if ($distro -eq "centos") { "yum" } else { "dnf" }
                Invoke-BashCommand -Command "sudo $pkgMgr groupinstall `"Development Tools`" -y"
                Invoke-BashCommand -Command "sudo $pkgMgr install -y tk tcl tk-devel tcl-devel zlib-devel bzip2-devel readline-devel sqlite-devel openssl-devel libffi-devel"
            }
            default {
                Write-Log -Level "Warn" -Message "No specific build dependency install for $distro, attempting generic..."
            }
        }
        
        Install-PythonUnixSource -pythonVersion $pythonVersion
    }
}

function Install-PythonUnixSource {
    Param ([string]$pythonVersion)
    
    $pyVersion = $VersionPins.PythonSources[$pythonVersion]
    if (-not $pyVersion) {
        Throw-Logged "Unsupported Python version '$pythonVersion' for source build"
    }

    $pythonSrcUrl = "https://www.python.org/ftp/python/$pyVersion/Python-$pyVersion.tgz"
    $tarPath = "Python-$pyVersion.tgz"
    
    Invoke-Download -Uri $pythonSrcUrl -Destination $tarPath -Description "Python $pyVersion source"
    
    if ($dryRun) {
        Write-Log -Level "Info" -Message "[dry-run] Would build Python from source"
        return
    }
    
    Invoke-BashCommand -Command "tar -xvf $tarPath"
    $currentDir = (Get-Location).Path
    Set-Location -LiteralPath "Python-$pyVersion"

    $configureOptions = "--enable-optimizations --with-ensurepip=install --enable-shared"
    if ($currentOS -eq "Linux") {
        $configureOptions += ' LDFLAGS="-Wl,--disable-new-dtags"'
    }

    Invoke-BashCommand -Command "sudo ./configure $configureOptions"

    $makeParallel = if ($currentOS -eq "Linux") { 
        Invoke-BashCommand -Command 'nproc'
    } 
    elseif ($currentOS -eq "Mac") { 
        Invoke-BashCommand -Command 'sysctl -n hw.ncpu'
    } 
    else { "1" }

    Invoke-BashCommand -Command "sudo make -j $makeParallel"
    Invoke-BashCommand -Command "sudo make altinstall"
    Set-Location -LiteralPath $currentDir
    $global:pythonInstallPath = "/usr/local/bin/python$pythonVersion"
}
#endregion Python installation - Linux

#region Virtual environment management
function global:deactivate ([switch]$NonDestructive) {
    if (Test-Path -Path Function:_OLD_VIRTUAL_PROMPT) {
        Copy-Item -Path Function:_OLD_VIRTUAL_PROMPT -Destination Function:prompt
        Remove-Item -Path Function:_OLD_VIRTUAL_PROMPT
    }
    if (Test-Path -Path Env:_OLD_VIRTUAL_PYTHONHOME) {
        Copy-Item -Path Env:_OLD_VIRTUAL_PYTHONHOME -Destination Env:PYTHONHOME
        Remove-Item -Path Env:_OLD_VIRTUAL_PYTHONHOME
    }
    if (Test-Path -Path Env:_OLD_VIRTUAL_PATH) {
        Copy-Item -Path Env:_OLD_VIRTUAL_PATH -Destination Env:PATH
        Remove-Item -Path Env:_OLD_VIRTUAL_PATH
    }
    if (Test-Path -Path Env:VIRTUAL_ENV) {
        Remove-Item -Path env:VIRTUAL_ENV
    }
    if (Test-Path -Path Env:VIRTUAL_ENV_PROMPT) {
        Remove-Item -Path env:VIRTUAL_ENV_PROMPT
    }
    if (Get-Variable -Name "_PYTHON_VENV_PROMPT_PREFIX" -ErrorAction SilentlyContinue) {
        Remove-Variable -Name _PYTHON_VENV_PROMPT_PREFIX -Scope Global -Force
    }
    if (-not $NonDestructive) {
        Remove-Item -Path function:deactivate
    }
}

function Activate-PythonVenv {
    param (
        [Parameter(Mandatory = $true)][string]$venvPath,
        [switch]$noRecurse
    )

    if (-not (Test-Path -LiteralPath $venvPath)) {
        Throw-Logged "Virtual environment path '$venvPath' does not exist"
    }

    Write-Log -Level "Info" -Message "Activating venv at '$venvPath'"
    
    $venvScriptBinPath = if ($currentOS -eq "Windows") {
        Join-Path -Path $venvPath -ChildPath "Scripts"
    }
    else {
        Join-Path -Path $venvPath -ChildPath "bin"
    }
    
    $activateScriptPathPwsh = Join-Path -Path $venvScriptBinPath -ChildPath "Activate.ps1"
    $activateScriptPathBash = Join-Path -Path $venvScriptBinPath -ChildPath "activate"
    
    $activated = $false
    
    if (Test-Path $activateScriptPathPwsh) {
        try {
            if (-not $dryRun) { . $activateScriptPathPwsh }
            $activated = $true
        }
        catch {
            Write-Log -Level "Warn" -Message "PowerShell activation failed: $_"
        }
    }
    
    if (-not $activated -and (Test-Path $activateScriptPathBash)) {
        try {
            if (-not $dryRun) { . $activateScriptPathBash }
            $activated = $true
        }
        catch {
            Write-Log -Level "Warn" -Message "Bash activation failed: $_"
        }
    }
    
    if (-not $activated) {
        Throw-Logged "Could not activate venv - no activation scripts found or all failed"
    }
}
#endregion Virtual environment management

#region .env loader
function Set-EnvironmentVariablesFromEnvFile {
    Param ([string]$envFilePath)
    
    if (-not (Test-Path -LiteralPath $envFilePath)) {
        return $false
    }
    
    Get-Content $envFilePath | ForEach-Object {
        if ($_ -match '^\s*(\w+)\s*=\s*(?:"(.*?)"|''(.*?)''|(.*?))\s*$') {
            $key = $matches[1]
            $value = $matches[2] + $matches[3] + $matches[4]
            
            Write-Log -Level "Debug" -Message "Processing env var: $key"
            
            # Expand ${env:VAR} references
            $value = $value -replace '\$\{env:(.*?)\}', {
                $envVarName = $matches[1]
                $retrievedEnvValue = [System.Environment]::GetEnvironmentVariable($envVarName, [System.EnvironmentVariableTarget]::Process)
                if ($null -eq $retrievedEnvValue) { $retrievedEnvValue = "" }
                Write-Log -Level "Trace" -Message "Expanding ${env:$envVarName} to '$retrievedEnvValue'"
                return $retrievedEnvValue
            }
            
            # Handle path lists
            $uniquePaths = @{}
            ($value -split ';').ForEach({
                $trimmedPath = $_.Trim()
                if (-not [string]::IsNullOrWhiteSpace($trimmedPath)) {
                    $absolutePath = Join-Path -Path $repoRootPath -ChildPath $trimmedPath
                    if (Test-Path -LiteralPath $absolutePath -ErrorAction SilentlyContinue) {
                        $resolvedPath = (Resolve-Path -LiteralPath $absolutePath).Path
                        if ($null -ne $resolvedPath) {
                            $uniquePaths[$resolvedPath] = $true
                        }
                    }
                }
            })
            $value = ($uniquePaths.Keys -join ';')

            Write-Log -Level "Debug" -Message "Setting env:$key = $(Mask-Value $value)"
            Set-Item -LiteralPath "env:$key" -Value $value
        }
    }
    
    Write-Log -Level "Info" -Message "Environment variables loaded from .env file"
    return $true
}
#endregion .env loader

#region Main execution flow
Write-Log -Level "Info" -Message "PyKotor Python/Venv bootstrap starting..."
Write-Log -Level "Debug" -Message "OS: $currentOS"
Write-Log -Level "Debug" -Message "Target venv: $venvPath"
if ($dryRun) {
    Write-Log -Level "Info" -Message "DRY-RUN MODE: No changes will be made"
}

# 1) Find or install Python
$targetVersion = if ($force_python_version) { $force_python_version } else { $VersionPins.PythonDefaultMajorMinor }
Write-Log -Level "Info" -Message "Target Python version: $targetVersion"

Find-Python -installIfNotFound $true

if (-not $global:pythonInstallPath) {
    Throw-Logged "Python installation/discovery failed"
}

# Validate version
if ($global:pythonVersion -lt $VersionPins.MinPythonVersion -or $global:pythonVersion -gt $VersionPins.MaxPythonVersion) {
    Throw-Logged "Python version $global:pythonVersion is outside supported range ($($VersionPins.MinPythonVersion) - $($VersionPins.MaxPythonVersion))"
}

Write-Log -Level "Info" -Message "Using Python $global:pythonVersion at $global:pythonInstallPath"

# 2) Create/activate venv (unless skipped)
$pythonExePath = $global:pythonInstallPath
$installPipToVenvManually = $false

if (-not $skipVenv) {
    if (Get-ChildItem Env:VIRTUAL_ENV -ErrorAction SilentlyContinue) {
        Write-Log -Level "Info" -Message "Deactivating existing venv: $env:VIRTUAL_ENV"
        deactivate
    }

    if (Test-Path $venvPath -ErrorAction SilentlyContinue) {
        Write-Log -Level "Info" -Message "Using existing venv at '$venvPath'"
    }
    else {
        Write-Log -Level "Info" -Message "Creating virtual environment at '$venvPath'..."
        
        if (-not $dryRun) {
            $pythonVenvCreation = & $global:pythonInstallPath -m venv $venvPath 2>&1
            if ($pythonVenvCreation -like "*Error*") {
                Handle-Error -ErrorRecord $pythonVenvCreation
                
                if (-not (Confirm-Action -Prompt "venv creation failed. Use system Python instead (not recommended)?" -DefaultYes:$false)) {
                    Throw-Logged "Cannot proceed without venv"
                }
                $pythonExePath = $global:pythonInstallPath
            }
            else {
                Write-Log -Level "Info" -Message "Virtual environment created"
                
                # Check for activation scripts on Unix
                if ($currentOS -ne "Windows") {
                    $activateScriptBash = Join-Path -Path $venvPath -ChildPath "bin/activate"
                    $activateScriptPs1 = Join-Path -Path $venvPath -ChildPath "bin/Activate.ps1"
                    
                    if (-not (Test-Path $activateScriptPs1) -and -not (Test-Path $activateScriptBash)) {
                        Write-Log -Level "Warn" -Message "Activation scripts missing, recreating venv without pip..."
                        Remove-Item -LiteralPath $venvPath -Recurse -Force
                        & $global:pythonInstallPath -m venv --without-pip $venvPath 2>&1
                        $installPipToVenvManually = $true
                    }
                }
            }
        }
    }

    # Find venv Python executable
    $pythonExePaths = switch ($currentOS) {
        'Windows' { @("$venvPath\Scripts\python.exe") }
        'Linux'   { @("$venvPath/bin/python3", "$venvPath/bin/python") }
        'Mac'     { @("$venvPath/bin/python3", "$venvPath/bin/python") }
    }

    $pythonExePath = $pythonExePaths | Where-Object { Test-Path $_ -ErrorAction SilentlyContinue } | Select-Object -First 1
    if (-not $pythonExePath) {
        Throw-Logged "No python executable found in venv at $venvPath"
    }
    
    Write-Log -Level "Info" -Message "Venv Python: $pythonExePath"
    
    # Activate venv
    if (-not $dryRun) {
        Activate-PythonVenv -venvPath $venvPath
    }
    
    # Manually install pip if needed
    if ($installPipToVenvManually -and -not $dryRun) {
        Write-Log -Level "Info" -Message "Installing pip manually..."
        $originalLocation = Get-Location
        $tempPath = [System.IO.Path]::GetTempPath()
        try {
            $getPipScriptPath = Join-Path -Path $tempPath -ChildPath "get-pip.py"
            Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPipScriptPath
            & $pythonExePath $getPipScriptPath
            
            $pipPath = Join-Path -Path $venvPath -ChildPath "bin/pip"
            if (-not $? -or -not (Test-Path $pipPath -ErrorAction SilentlyContinue)) {
                Write-Log -Level "Warn" -Message "get-pip.py failed, using fallback method"
                
                $latestPipVersion = $VersionPins.PipVersion
                $latestSetuptoolsVersion = $VersionPins.SetuptoolsVersion
                $setuptoolsUrl = "https://files.pythonhosted.org/packages/aa/60/5db2249526c9b453c5bb8b9f6965fcab0e1f9e2c3c77ea0564bb49436084/setuptools-$latestSetuptoolsVersion.tar.gz"
                $pipUrl = "https://files.pythonhosted.org/packages/4d/16/0a14ca596f30316efd412a60bdfac02a7259bf8673d4d917dc60b9a21812/pip-$latestPipVersion.tar.gz"
                
                Invoke-WebRequest -Uri $setuptoolsUrl -OutFile "setuptools-$latestSetuptoolsVersion.tar.gz"
                Invoke-BashCommand "tar -xzf `"setuptools-$latestSetuptoolsVersion.tar.gz`""
                Set-Location -LiteralPath "setuptools-$latestSetuptoolsVersion"
                & $pythonExePath setup.py install
                Set-Location -LiteralPath $originalLocation
                
                Invoke-WebRequest -Uri $pipUrl -OutFile "pip-$latestPipVersion.tar.gz"
                Invoke-BashCommand -Command "tar -xzf `"pip-$latestPipVersion.tar.gz`""
                Set-Location -LiteralPath "pip-$latestPipVersion"
                & $pythonExePath setup.py install
            }
        }
        finally {
            Set-Location -LiteralPath $originalLocation
        }
    }
}

# 3) Verify Python executable
$finalPythonVersion = Get-Python-Version $pythonExePath
Write-Log -Level "Info" -Message "Final Python: $finalPythonVersion at $pythonExePath"

# 4) Get site-packages path
if (-not $dryRun) {
    $sitePackagesPath = & $pythonExePath -c "import sysconfig; print(sysconfig.get_paths()['purelib'])" 2>&1
    Write-Log -Level "Info" -Message "Site-Packages: $sitePackagesPath"
}

# 5) Load .env
if (-not $skipEnvLoad) {
    $dotenv_path = Join-Path -Path $repoRootPath -ChildPath ".env"
    Write-Log -Level "Info" -Message "Loading .env from: $dotenv_path"
    $envFileFound = Set-EnvironmentVariablesFromEnvFile $dotenv_path
    if (-not $envFileFound) {
        Write-Log -Level "Warn" -Message ".env file not found - may need to fetch latest repo changes"
    }
}
else {
    Write-Log -Level "Info" -Message ".env loading skipped"
}

$script:ExitCode = 0
Write-Log -Level "Info" -Message "Bootstrap complete!"

# Export commonly needed values for callers (workflows/scripts) that dot-source this script.
# - $pythonExePath is a local variable in this script; persist it to both $global: and $env:
# - The venv activation modifies env vars in the current session; keeping pythonExePath explicit
#   makes subsequent tooling deterministic.
$global:pythonExePath = $pythonExePath
$env:pythonExePath = $pythonExePath
$global:venvPath = $venvPath
$env:PYKOTOR_VENV_PATH = $venvPath

if ($script:IsDotSourced) {
    return
}
exit $script:ExitCode
#endregion Main execution flow
