#!/bin/bash
# Install PowerShell Core on Linux and macOS
# This script ensures PowerShell is available for running .ps1 scripts

set -e

# Check if PowerShell is already installed
if command -v pwsh &> /dev/null; then
    echo "PowerShell is already installed: $(pwsh --version)"
    exit 0
fi

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux installation
    echo "Installing PowerShell on Linux..."
    
    # Check if we're on Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        # Update package list
        sudo apt-get update -qq
        
        # Install dependencies
        sudo apt-get install -y -qq wget apt-transport-https software-properties-common
        
        # Download Microsoft signing key
        # Try to get Ubuntu version, fallback to 22.04 if lsb_release is not available
        if command -v lsb_release &> /dev/null; then
            UBUNTU_VERSION=$(lsb_release -rs)
        else
            # Fallback: try to detect from /etc/os-release
            if [ -f /etc/os-release ]; then
                UBUNTU_VERSION=$(grep VERSION_ID /etc/os-release | cut -d'"' -f2 | cut -d'.' -f1,2)
            else
                # Default to 22.04 if we can't detect
                UBUNTU_VERSION="22.04"
            fi
        fi
        
        wget -q "https://packages.microsoft.com/config/ubuntu/${UBUNTU_VERSION}/packages-microsoft-prod.deb" -O packages-microsoft-prod.deb || {
            echo "Warning: Failed to download packages-microsoft-prod.deb for Ubuntu ${UBUNTU_VERSION}, trying 22.04..."
            wget -q "https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb" -O packages-microsoft-prod.deb
        }
        sudo dpkg -i packages-microsoft-prod.deb
        rm packages-microsoft-prod.deb
        
        # Update package list again
        sudo apt-get update -qq
        
        # Install PowerShell
        sudo apt-get install -y -qq powershell
        
    # Check if we're on RHEL/CentOS/Fedora
    elif command -v yum &> /dev/null || command -v dnf &> /dev/null; then
        # For RHEL/CentOS/Fedora
        if command -v dnf &> /dev/null; then
            PKG_MGR=dnf
        else
            PKG_MGR=yum
        fi
        
        # Register Microsoft repository
        sudo $PKG_MGR install -y -q https://packages.microsoft.com/config/rhel/7/packages-microsoft-prod.rpm
        
        # Install PowerShell
        sudo $PKG_MGR install -y -q powershell
        
    else
        echo "Unsupported Linux distribution. Attempting generic installation..."
        # Fallback: try to install via snap or download binary
        if command -v snap &> /dev/null; then
            sudo snap install powershell --classic
        else
            echo "ERROR: Cannot install PowerShell on this Linux distribution automatically"
            exit 1
        fi
    fi
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS installation
    echo "Installing PowerShell on macOS..."
    
    # Check if Homebrew is available
    if command -v brew &> /dev/null; then
        brew install --cask powershell
    else
        # Fallback: download and install manually
        echo "Homebrew not found. Downloading PowerShell manually..."
        LATEST_VERSION=$(curl -s https://api.github.com/repos/PowerShell/PowerShell/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
        PKG_URL="https://github.com/PowerShell/PowerShell/releases/download/${LATEST_VERSION}/powershell-${LATEST_VERSION}-osx-x64.pkg"
        
        curl -L -o /tmp/powershell.pkg "$PKG_URL"
        sudo installer -pkg /tmp/powershell.pkg -target /
        rm /tmp/powershell.pkg
    fi
    
else
    echo "ERROR: Unsupported operating system: $OSTYPE"
    exit 1
fi

# Verify installation
if command -v pwsh &> /dev/null; then
    echo "PowerShell installed successfully: $(pwsh --version)"
    pwsh --version
else
    echo "ERROR: PowerShell installation completed but 'pwsh' command not found"
    exit 1
fi