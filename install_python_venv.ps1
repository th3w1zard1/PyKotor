#!/usr/bin/env pwsh
<# 
    install_python_venv.ps1
    Robust, idempotent Python + venv bootstrapper for PyKotor.

    Key improvements:
    - Single consistent error trap; respects -noprompt.
    - OS/distro detection without WMI on non-Windows.
    - Idempotent venv creation/activation; clear reuse semantics.
    - Fixed undefined variables (env refresh, activation fallbacks).
    - Non-interactive mode honored everywhere (no stray Read-Host).
    - Secure downloads with optional SHA256 verification and cleanup.
    - Centralized version map; defaults to Python 3.13.x, pip/setuptools recent pins.
    - Optional dry-run, verbose logging, and skip toggles for env load/venv.
    - Avoids echoing secrets from .env; masks values unless -ShowEnvValues.
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

# Normalize log level
$script:LogLevels = @{
    "Trace"  = 0
    "Debug"  = 1
    "Info"   = 2
    "Warn"   = 3
    "Error"  = 4
    "Silent" = 5
}
if (-not $LogLevels.ContainsKey($logLevel)) { $logLevel = "Info" }
$script:CurrentLogLevel = $LogLevels[$logLevel]

# Version pins (override with -force_python_version if desired)
$script:VersionPins = [pscustomobject]@{
    PythonDefaultMajorMinor = "3.13"
    PythonAltMajors         = @("3.13","3.12","3.11","3.10","3.9","3.8")
    PythonSources           = @{
        "3.13" = "3.13.0"
        "3.12" = "3.12.8"
        "3.11" = "3.11.10"
        "3.10" = "3.10.15"
        "3.9"  = "3.9.20"
        "3.8"  = "3.8.19"
    }
    PipVersion        = "24.3.1"
    SetuptoolsVersion = "75.2.0"
    TclTkVersion      = "8.6.14"
}

# Repo paths
$scriptPath   = $MyInvocation.MyCommand.Definition
$repoRootPath = (Resolve-Path -LiteralPath (Join-Path -Path $scriptPath -ChildPath "..")).Path
$pathSep      = [IO.Path]::DirectorySeparatorChar
$venvPath     = if ($venvPathOverride) { $venvPathOverride } else { Join-Path -Path $repoRootPath -ChildPath $venv_name }

# Console colors toggle
$script:UseColor = $Host.Name -notmatch "VSCode" -and $Host.UI -and $Host.UI.RawUI -and $Host.UI.SupportsVirtualTerminal
#endregion Globals

#region Logging helpers
function Write-Log {
    param(
        [Parameter(Mandatory = $true)][ValidateSet("Trace","Debug","Info","Warn","Error")]
        [string]$Level,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if ($LogLevels[$Level] -lt $CurrentLogLevel) { return }
    $prefix = "[{0}] " -f $Level.ToUpper()
    $color = switch ($Level) {
        "Trace" { "DarkGray" }
        "Debug" { "Gray" }
        "Info"  { "White" }
        "Warn"  { "Yellow" }
        "Error" { "Red" }
    }
    if ($UseColor) { Write-Host "$prefix$Message" -ForegroundColor $color }
    else { Write-Host "$prefix$Message" }
}

function Throw-Logged {
    param([string]$Message)
    Write-Log -Level "Error" -Message $Message
    throw $Message
}
#endregion Logging

#region Error trap
trap {
    $err = $_
    Write-Log -Level "Error" -Message ("Unhandled error: {0}" -f $err)
    if ($err.ScriptStackTrace) {
        Write-Log -Level "Debug" -Message $err.ScriptStackTrace
    }
    $global:LASTEXITCODE = 1
    exit 1
}
#endregion Error trap

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
        } else {
            Throw-Logged "$Name is required but not found."
        }
    }
}

function Confirm-Action {
    param(
        [string]$Prompt,
        [switch]$DefaultYes
    )
    if ($dryRun) { return $true }
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
    return ("{0}***" -f $Value.Substring(0,4))
}

function New-TempFileIn {
    param([Parameter(Mandatory = $true)][string]$Directory)
    if (-not (Test-Path $Directory)) { New-Item -ItemType Directory -Path $Directory | Out-Null }
    $name = [System.IO.Path]::GetRandomFileName()
    return Join-Path -Path $Directory -ChildPath $name
}
#endregion Utility helpers

#region OS detection
function Get-OSInfo {
    $isWin = $IsWindows
    $isMac = $IsMacOS
    $isLin = $IsLinux

    $distroId = $null
    $distroVersion = $null

    if ($isLin -and (Test-Path "/etc/os-release")) {
        $kv = @{}
        Get-Content "/etc/os-release" | ForEach-Object {
            if ($_ -match '^\s*([^=]+)=(.*)$') {
                $k = $matches[1].Trim()
                $v = $matches[2].Trim('"')
                $kv[$k] = $v
            }
        }
        $distroId = $kv["ID"]
        $distroVersion = $kv["VERSION_ID"]
    }
    return [pscustomobject]@{
        IsWindows = $isWin
        IsMacOS   = $isMac
        IsLinux   = $isLin
        DistroId  = $distroId
        DistroVer = $distroVersion
        Name      = if ($isWin) { "Windows" } elseif ($isMac) { "Mac" } elseif ($isLin) { "Linux" } else { "Unknown" }
    }
}
$OSInfo = Get-OSInfo
#endregion OS detection

#region Download + checksum
function Invoke-Download {
    param(
        [Parameter(Mandatory = $true)][string]$Uri,
        [Parameter(Mandatory = $true)][string]$Destination,
        [string]$Sha256,
        [string]$Description = "download",
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
            }
            return $true
        } catch {
            if ($i -eq $Retries) { throw }
            Start-Sleep -Seconds 2
        }
    }
    return $false
}
#endregion Download + checksum

#region Python version parsing
function Parse-PythonVersionString {
    param([string]$VersionString)
    if ([string]::IsNullOrWhiteSpace($VersionString)) { return $null }
    $match = [regex]::Match($VersionString, '(\d+)(\.\d+){1,3}')
    if (-not $match.Success) { return $null }
    $segments = $match.Value.Split('.')
    while ($segments.Count -lt 3) { $segments += '0' }
    return [version]($segments -join '.')
}
#endregion Python version parsing

#region Python discovery
function Get-CandidatePythonCommands {
    param([string]$forced)
    if ($forced) { return @("python$forced", "python$($forced.Replace('.',''))") }
    $defaults = @(
        "python3.13","python3.12","python3.11","python3.10","python3.9","python3.8","python3","python"
    )
    return $defaults
}

function Get-CandidatePythonPaths {
    param([string]$majorMinor,[string]$osName)
    $winVer = $majorMinor -replace '\.',''
    $pathsWin = @(
        "C:\Program Files\Python$winVer\python.exe",
        "C:\Program Files (x86)\Python$winVer\python.exe",
        "$env:USERPROFILE\AppData\Local\Programs\Python\Python$winVer\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python$winVer\python.exe"
    )
    $pathsNix = @(
        "/usr/local/bin/python$majorMinor",
        "/usr/bin/python$majorMinor",
        "/bin/python$majorMinor",
        "/usr/local/bin/python3",
        "/usr/bin/python3",
        "/bin/python3"
    )
    switch ($osName) {
        "Windows" { return $pathsWin }
        default   { return $pathsNix }
    }
}

function Find-Python {
    param(
        [string]$TargetMajorMinor,
        [switch]$InstallIfMissing
    )
    $preferred = $TargetMajorMinor
    $allTargets = if ($TargetMajorMinor) { @($TargetMajorMinor) } else { $VersionPins.PythonAltMajors }
    $found = @()

    # Command search
    foreach ($majMin in $allTargets) {
        foreach ($cmd in Get-CandidatePythonCommands -forced $majMin) {
            if (Test-Command $cmd) {
                $path = (Get-Command $cmd).Source
                $ver = Parse-PythonVersionString (& $path --version 2>&1 | Out-String)
                if ($ver) {
                    $found += [pscustomobject]@{ Path=$path; Version=$ver; Source="command:$cmd" }
                }
            }
        }
    }

    # Path search
    foreach ($majMin in $allTargets) {
        foreach ($p in Get-CandidatePythonPaths -majorMinor $majMin -osName $OSInfo.Name) {
            $resolved = [Environment]::ExpandEnvironmentVariables($p)
            if (Test-Path $resolved) {
                $ver = Parse-PythonVersionString (& $resolved --version 2>&1 | Out-String)
                if ($ver) {
                    $found += [pscustomobject]@{ Path=$resolved; Version=$ver; Source="path" }
                }
            }
        }
    }

    # Choose best
    $best = $found |
        Sort-Object @{Expression = { $_.Version.Major }; Descending=$false},
                    @{Expression = { $_.Version.Minor }; Descending=$false} |
        Select-Object -First 1

    if ($best) {
        Write-Log -Level "Info" -Message ("Found Python {0} at {1} ({2})" -f $best.Version, $best.Path, $best.Source)
        return $best
    }

    if (-not $InstallIfMissing) { return $null }
    return $null
}
#endregion Python discovery

#region Python install helpers
function Ensure-SudoAvailable {
    if ($OSInfo.IsLinux -or $OSInfo.IsMacOS) {
        if (-not (Test-Command "sudo")) {
            Throw-Logged "sudo is required to install system packages."
        }
    }
}

function Install-PythonWindows {
    param([string]$MajorMinor,[switch]$AcceptLicense)
    $full = $VersionPins.PythonSources[$MajorMinor]
    if (-not $full) { Throw-Logged "Unsupported Python version $MajorMinor for Windows installer." }
    $installer = if ([Environment]::Is64BitOperatingSystem) { "python-$full-amd64.exe" } else { "python-$full.exe" }
    $uri = "https://www.python.org/ftp/python/$full/$installer"
    $tmp = New-TempFileIn -Directory $env:TEMP
    $dest = "$tmp.exe"
    Write-Log -Level "Info" -Message "Downloading Python $full for Windows..."
    Invoke-Download -Uri $uri -Destination $dest -Description "python-installer"
    if ($dryRun) { return $true }
    $args = "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0"
    if ($AcceptLicense -or $forceInstall -or $noprompt) { $args += " Include_launcher=0" }
    Write-Log -Level "Info" -Message "Running installer..."
    $proc = Start-Process -FilePath $dest -ArgumentList $args -PassThru -Wait
    if ($proc.ExitCode -ne 0) { Throw-Logged "Python installer failed with exit code $($proc.ExitCode)" }
    Remove-Item -LiteralPath $dest -ErrorAction SilentlyContinue
    return $true
}

function Install-PythonMac {
    param([string]$MajorMinor,[switch]$AcceptLicense)
    $full = $VersionPins.PythonSources[$MajorMinor]
    if (-not $full) { Throw-Logged "Unsupported Python version $MajorMinor for macOS installer." }
    $pkg = "python-$full-macos11.pkg"
    $uri = "https://www.python.org/ftp/python/$full/$pkg"
    $dest = New-TempFileIn -Directory "/tmp"
    $pkgPath = "$dest.pkg"
    Write-Log -Level "Info" -Message "Downloading Python $full for macOS..."
    Invoke-Download -Uri $uri -Destination $pkgPath -Description "python-pkg"
    if ($dryRun) { return $true }
    if (-not $AcceptLicense -and -not $forceInstall -and -not $noprompt) {
        if (-not (Confirm-Action -Prompt "Proceed to install Python $full (pkg)?" -DefaultYes)) { Throw-Logged "User declined installation." }
    }
    Ensure-SudoAvailable
    $proc = Start-Process -FilePath "sudo" -ArgumentList @("installer","-pkg",$pkgPath,"-target","/") -PassThru -Wait
    if ($proc.ExitCode -ne 0) { Throw-Logged "Installer failed with exit code $($proc.ExitCode)" }
    Remove-Item -LiteralPath $pkgPath -ErrorAction SilentlyContinue
    return $true
}

function Install-PythonLinuxPackage {
    param([string]$MajorMinor)
    $distro = $OSInfo.DistroId
    Ensure-SudoAvailable
    switch ($distro) {
        "ubuntu" { $cmd = "sudo apt-get update && sudo apt-get install -y python$MajorMinor python$MajorMinor-venv python$MajorMinor-dev tk tcl" }
        "debian" { $cmd = "sudo apt-get update && sudo apt-get install -y python$MajorMinor python$MajorMinor-venv python$MajorMinor-dev tk tcl" }
        "alpine" { $cmd = "sudo apk add --no-cache python$MajorMinor python$MajorMinor-tkinter tk tcl" }
        "fedora" { $cmd = "sudo dnf install -y python$MajorMinor python$MajorMinor-devel tk tcl" }
        "almalinux" { $cmd = "sudo dnf install -y python$MajorMinor python$MajorMinor-devel tk tcl" }
        "centos" { $cmd = "sudo yum install -y python$MajorMinor python$MajorMinor-devel tk tcl" }
        "arch" { $cmd = "sudo pacman -Sy --noconfirm python tk tcl" }
        default { Throw-Logged "Unsupported or unknown Linux distro '$distro' for package install." }
    }
    Write-Log -Level "Info" -Message "Installing Python $MajorMinor via package manager..."
    if ($dryRun) { Write-Log -Level "Info" -Message "[dry-run] $cmd"; return $true }
    $proc = if ($IsWindows) { Throw-Logged "Package install not valid on Windows." } else { bash -lc $cmd }
    return $true
}

function Build-PythonFromSource {
    param([string]$MajorMinor)
    $full = $VersionPins.PythonSources[$MajorMinor]
    if (-not $full) { Throw-Logged "Unsupported Python version $MajorMinor for source build." }
    Ensure-SudoAvailable
    $uri = "https://www.python.org/ftp/python/$full/Python-$full.tgz"
    $tmpDir = Join-Path ([IO.Path]::GetTempPath()) ("pybuild-" + [Guid]::NewGuid().ToString("N"))
    $tarPath = Join-Path $tmpDir "Python-$full.tgz"
    if (-not $dryRun) { New-Item -ItemType Directory -Path $tmpDir | Out-Null }
    Write-Log -Level "Info" -Message "Downloading Python $full source..."
    Invoke-Download -Uri $uri -Destination $tarPath -Description "python-source"
    if ($dryRun) { Write-Log -Level "Info" -Message "[dry-run] Would unpack and build in $tmpDir"; return $true }

    Push-Location $tmpDir
    try {
        tar -xvf $tarPath | Out-Null
        Set-Location "Python-$full"
        $jobs = 1
        try {
            $jobs = if ($OSInfo.IsMacOS) { (sysctl -n hw.ncpu) } elseif ($OSInfo.IsLinux) { (nproc) } else { 1 }
        } catch { $jobs = 1 }
        Write-Log -Level "Info" -Message "Configuring..."
        ./configure --enable-optimizations --with-ensurepip=install --enable-shared
        Write-Log -Level "Info" -Message "Building with $jobs jobs..."
        make -j $jobs
        Write-Log -Level "Info" -Message "Installing with sudo make altinstall..."
        sudo make altinstall
    } finally {
        Pop-Location
        Remove-Item -LiteralPath $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    return $true
}

function Install-Python {
    param(
        [string]$MajorMinor,
        [switch]$AcceptLicense
    )
    Write-Log -Level "Info" -Message "Attempting to install Python $MajorMinor..."
    if ($OSInfo.IsWindows) {
        Install-PythonWindows -MajorMinor $MajorMinor -AcceptLicense:$AcceptLicense
    } elseif ($OSInfo.IsMacOS) {
        try {
            Install-PythonMac -MajorMinor $MajorMinor -AcceptLicense:$AcceptLicense
        } catch {
            Write-Log -Level "Warn" -Message "macOS pkg install failed, falling back to source build: $_"
            Build-PythonFromSource -MajorMinor $MajorMinor
        }
    } elseif ($OSInfo.IsLinux) {
        try {
            Install-PythonLinuxPackage -MajorMinor $MajorMinor
        } catch {
            Write-Log -Level "Warn" -Message "Package install failed, falling back to source build: $_"
            Build-PythonFromSource -MajorMinor $MajorMinor
        }
    } else {
        Throw-Logged "Unsupported OS."
    }
}
#endregion Python install helpers

#region Pip/Setuptools bootstrap
function Ensure-Pip {
    param(
        [string]$PythonExe
    )
    $pip = & $PythonExe -m pip --version 2>$null
    if ($pip) {
        Write-Log -Level "Info" -Message "pip already present ($pip)"
        return
    }
    Write-Log -Level "Info" -Message "Installing pip via ensurepip..."
    if ($dryRun) { Write-Log -Level "Info" -Message "[dry-run] python -m ensurepip --upgrade"; return }
    & $PythonExe -m ensurepip --upgrade
}

function Upgrade-PipSetuptools {
    param(
        [string]$PythonExe
    )
    $pipVer = $VersionPins.PipVersion
    $setVer = $VersionPins.SetuptoolsVersion
    if ($dryRun) {
        Write-Log -Level "Info" -Message "[dry-run] Would upgrade pip to $pipVer and setuptools to $setVer"
        return
    }
    Write-Log -Level "Info" -Message "Upgrading pip -> $pipVer, setuptools -> $setVer"
    & $PythonExe -m pip install --upgrade ("pip==$pipVer") ("setuptools==$setVer")
}
#endregion Pip/Setuptools bootstrap

#region Virtual environment
function Ensure-Venv {
    param(
        [string]$PythonExe,
        [string]$Path
    )
    if (Test-Path -LiteralPath $Path) {
        Write-Log -Level "Info" -Message "Existing venv detected at $Path (idempotent reuse)."
        return
    }
    if ($dryRun) { Write-Log -Level "Info" -Message "[dry-run] Would create venv at $Path"; return }
    Write-Log -Level "Info" -Message "Creating virtual environment at $Path..."
    & $PythonExe -m venv $Path
}

function Get-VenvPython {
    param([string]$Path)
    if ($OSInfo.IsWindows) { return (Join-Path $Path "Scripts\python.exe") }
    else { return (Join-Path $Path "bin/python3") }
}

function Activate-Venv {
    param([string]$Path)
    $scriptPath = if ($OSInfo.IsWindows) { Join-Path $Path "Scripts\Activate.ps1" } else { Join-Path $Path "bin/activate" }
    if (-not (Test-Path $scriptPath)) { Throw-Logged "Activation script not found at $scriptPath" }
    Write-Log -Level "Info" -Message "Activating venv at $Path"
    if (-not $dryRun) { . $scriptPath }
}
#endregion Virtual environment

#region .env loader
function Load-DotEnv {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath
    )
    if (-not (Test-Path -LiteralPath $FilePath)) {
        Throw-Logged ".env file not found at $FilePath"
    }
    $lines = Get-Content -LiteralPath $FilePath
    foreach ($line in $lines) {
        if ($line -match '^\s*#') { continue }
        if ($line -match '^\s*$') { continue }
        if ($line -match '^\s*([\w\.]+)\s*=\s*(.*)\s*$') {
            $key = $matches[1]
            $raw = $matches[2].Trim()
            # Strip optional quotes
            if ($raw.StartsWith('"') -and $raw.EndsWith('"')) { $raw = $raw.Trim('"') }
            elseif ($raw.StartsWith("'") -and $raw.EndsWith("'")) { $raw = $raw.Trim("'") }
            # Expand ${env:VAR}
            $value = [regex]::Replace($raw, '\$\{env:([^}]+)\}', { param($m) [Environment]::GetEnvironmentVariable($m.Groups[1].Value) })
            Set-Item -LiteralPath "env:$key" -Value $value
            Write-Log -Level "Info" -Message ("Loaded {0}={1}" -f $key, (Mask-Value $value))
        }
    }
}
#endregion .env loader

#region Main flow
Write-Log -Level "Info" -Message "PyKotor Python/Venv bootstrap starting..."
Write-Log -Level "Debug" -Message "OS: $($OSInfo.Name) Dist: $($OSInfo.DistroId) $($OSInfo.DistroVer)"
Write-Log -Level "Debug" -Message "Repo root: $repoRootPath"
Write-Log -Level "Debug" -Message "Target venv: $venvPath"

$targetVersion = if ($force_python_version) { $force_python_version } else { $VersionPins.PythonDefaultMajorMinor }

# 1) Find existing Python
$python = Find-Python -TargetMajorMinor $targetVersion -InstallIfMissing:$false

# 2) Install if missing
if (-not $python) {
    if (-not $noprompt -and -not $forceInstall) {
        if (-not (Confirm-Action -Prompt "Python $targetVersion not found. Install it?" -DefaultYes)) {
            Throw-Logged "User declined installation; cannot proceed."
        }
    }
    Install-Python -MajorMinor $targetVersion -AcceptLicense:$acceptLicense
    $python = Find-Python -TargetMajorMinor $targetVersion -InstallIfMissing:$false
    if (-not $python) { Throw-Logged "Python $targetVersion installation appears to have failed." }
}

# 3) Validate version range
$min = [version]"3.8.0"
$max = [version]"3.14.0"
if ($python.Version -lt $min -or $python.Version -gt $max) {
    Throw-Logged "Python version $($python.Version) is outside supported range $min - $max"
}

# 4) Ensure pip + upgraded packaging tools
Ensure-Pip -PythonExe $python.Path
Upgrade-PipSetuptools -PythonExe $python.Path

# 5) Create venv (if not skipped)
if (-not $skipVenv) {
    Ensure-Venv -PythonExe $python.Path -Path $venvPath
    $venvPy = Get-VenvPython -Path $venvPath
    if (-not (Test-Path $venvPy)) { Throw-Logged "Venv python not found at $venvPy" }
    Activate-Venv -Path $venvPath
    # Re-upgrade pip/setuptools inside venv
    Ensure-Pip -PythonExe $venvPy
    Upgrade-PipSetuptools -PythonExe $venvPy
}

# 6) Load .env (optional)
if (-not $skipEnvLoad) {
    $dotenv = Join-Path $repoRootPath ".env"
    Load-DotEnv -FilePath $dotenv
} else {
    Write-Log -Level "Info" -Message ".env loading skipped."
}

$script:ExitCode = 0
Write-Log -Level "Info" -Message "Bootstrap complete."
#endregion Main flow

exit $script:ExitCode
