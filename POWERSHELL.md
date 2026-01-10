# PowerShell Setup for PyKotor

This guide helps Windows users configure PowerShell to run PyKotor scripts and addresses common execution policy issues.

## Installation

### Windows

PowerShell comes pre-installed on modern Windows versions. To update to the latest version:

1. Visit the [PowerShell GitHub releases](https://github.com/PowerShell/PowerShell/releases)
2. Download the installer for your Windows version
3. Run the installer and follow the prompts

### Linux/macOS

Install PowerShell using your package manager:

**Ubuntu/Debian:**
```bash
sudo apt-get install -y powershell
```

**Fedora:**
```bash
sudo dnf install -y powershell
```

**macOS:**
```bash
brew install --cask powershell
# or
brew install pwsh
```

**Alternative:** Use the automated installer:
```bash
./install_powershell.sh
```

Launch PowerShell by typing `pwsh` in your terminal.

## Execution Policy

By default, PowerShell restricts script execution for security. To run PyKotor scripts:

### Set Policy Globally (Requires Administrator)

1. Open PowerShell as administrator
2. Run:
   ```powershell
   Set-ExecutionPolicy Unrestricted
   ```
3. Confirm with `Y`

### Bypass Policy for Single Script

If you lack admin privileges or prefer temporary bypass:

```powershell
PowerShell.exe -ExecutionPolicy Bypass -File path\to\script.ps1
```

Replace `path\to\script.ps1` with your actual script path.

## PyKotor Development Scripts

### Running Development Setup

After cloning the repository:

**Windows:**
```powershell
./install_python_venv.ps1
```

**macOS/Linux:**
```bash
pwsh
./install_python_venv.ps1
```

This script:
- Checks for Python 3.8+
- Creates a virtual environment
- Installs PyKotor dependencies
- Configures environment variables

### Building Executables

The `compile/` folder contains PowerShell scripts for building standalone executables:

**Setup dependencies:**
```powershell
./compile/deps_holopatcher.ps1
./compile/deps_toolset.ps1
```

**Build executables:**
```powershell
./compile/compile_holopatcher.ps1
./compile/compile_toolset.ps1
```

Output executables are placed in the `dist/` folder.

## Troubleshooting

### "Script is not digitally signed"

Use the bypass method shown above, or set execution policy to `RemoteSigned`:

```powershell
Set-ExecutionPolicy RemoteSigned
```

### Permission Denied

Run PowerShell as administrator or use the `-ExecutionPolicy Bypass` flag.

### Script Not Found

Ensure you're in the correct directory:
```powershell
cd path\to\PyKotor
```

## Additional Resources

- [Official PowerShell Documentation](https://learn.microsoft.com/en-us/powershell/)
- [PowerShell GitHub Repository](https://github.com/PowerShell/PowerShell)
- [About Execution Policies](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies)