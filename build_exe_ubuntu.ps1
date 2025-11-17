# DupeRangerAi Ubuntu Build Script (PowerShell for cross-platform)
# Run this on Ubuntu 22.04 or WSL Ubuntu to create portable executable

param(
    [switch]$Clean,
    [switch]$Test
)

Write-Host "=== DupeRangerAi Ubuntu Build Script ===" -ForegroundColor Green
Write-Host "Building portable executable for Ubuntu 22.04" -ForegroundColor Green
Write-Host

# Configuration
$ScriptName = "DupeRangerAi"
$BuildDir = "build"
$DistDir = "dist"
$OutputDir = "${ScriptName}_ubuntu"

# Clean previous builds if requested
if ($Clean) {
    Write-Host "Cleaning previous builds..."
    if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
    if (Test-Path $DistDir) { Remove-Item -Recurse -Force $DistDir }
    if (Test-Path $OutputDir) { Remove-Item -Recurse -Force $OutputDir }
}

# Check if we're on Linux/WSL
$IsOnLinux = $PSVersionTable.Platform -eq "Unix" -or $env:WSL_DISTRO_NAME

if (-not $IsOnLinux) {
    Write-Warning "This script is designed for Ubuntu/Linux systems."
    Write-Host "To build for Ubuntu:"
    Write-Host "1. Copy this script to an Ubuntu 22.04 system"
    Write-Host "2. Run: pwsh ./build_exe_ubuntu.ps1"
    Write-Host "3. Or run: ./build_exe_ubuntu.sh (bash version)"
    exit 1
}

# Check if we're in a virtual environment
$PythonCmd = if ($env:VIRTUAL_ENV) { "python" } else { "python3" }
$PipCmd = if ($env:VIRTUAL_ENV) { "pip" } else { "pip3" }

if ($env:VIRTUAL_ENV) {
    Write-Host "Virtual environment detected: $env:VIRTUAL_ENV"
} else {
    Write-Host "No virtual environment detected. Using system Python."
}

# Install PyInstaller if not present
Write-Host "Checking for PyInstaller..."
try {
    & $PythonCmd -c "import PyInstaller" 2>$null
    Write-Host "PyInstaller is available."
} catch {
    Write-Host "Installing PyInstaller..."
    & $PipCmd install pyinstaller
}

# Install/update required packages
Write-Host "Installing required packages..."
& $PipCmd install --upgrade pip
& $PipCmd install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
& $PipCmd install transformers xxhash pillow psutil requests tqdm

# Verify PyTorch setup
Write-Host "Verifying PyTorch installation..."
& $PythonCmd -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU count: {torch.cuda.device_count()}')
else:
    print('Using CPU mode')
"

# Build the executable
Write-Host "Building executable with PyInstaller..."
$PyInstallerArgs = @(
    "--onefile",
    "--windowed",
    "--name=$ScriptName",
    "--add-data", "docs:docs",
    "--hidden-import=torch",
    "--hidden-import=torchvision",
    "--hidden-import=torchaudio",
    "--hidden-import=transformers",
    "--hidden-import=xxhash",
    "--hidden-import=PIL",
    "--hidden-import=psutil",
    "--hidden-import=requests",
    "--hidden-import=tqdm",
    "--hidden-import=sklearn",
    "--hidden-import=tokenizers",
    "--hidden-import=safetensors",
    "--hidden-import=yaml",
    "--hidden-import=regex",
    "--hidden-import=packaging",
    "--hidden-import=filelock",
    "--hidden-import=huggingface_hub",
    "--hidden-import=jinja2",
    "--hidden-import=markupsafe",
    "--hidden-import=numpy",
    "--hidden-import=accelerate",
    "--hidden-import=tqdm",
    "--collect-data", "transformers",
    "--collect-data", "torch",
    "DupeRangerAi.py"
)

& $PythonCmd -m PyInstaller @PyInstallerArgs

# Create output directory
Write-Host "Creating output directory: $OutputDir"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# Copy executable
Write-Host "Copying executable..."
Copy-Item "$DistDir/$ScriptName" "$OutputDir/"

# Copy documentation and scripts
Write-Host "Copying documentation and scripts..."
if (Test-Path "docs") {
    Copy-Item "docs/*" "$OutputDir/" -ErrorAction SilentlyContinue
}
if (Test-Path "install_deps.ps1") {
    Copy-Item "install_deps.ps1" "$OutputDir/" -ErrorAction SilentlyContinue
}
if (Test-Path "local_tests\synthetic_test.py") {
    Copy-Item "local_tests\synthetic_test.py" "$OutputDir/" -ErrorAction SilentlyContinue
}
if (Test-Path "local_tests\test_actions.py") {
    Copy-Item "local_tests\test_actions.py" "$OutputDir/" -ErrorAction SilentlyContinue
}

# Create Ubuntu-specific dependency installer
$InstallerScript = @'
#!/bin/bash

# DupeRangerAi Ubuntu Dependencies Installer
# Run this script to install system dependencies on Ubuntu 22.04

echo "=== DupeRangerAi Ubuntu Dependencies Installer ==="
echo "Installing system dependencies for Ubuntu 22.04..."
echo

# Update package list
sudo apt update

# Install Python and pip if not present
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3..."
    sudo apt install -y python3 python3-pip python3-venv
fi

# Install system libraries needed for PyTorch and other dependencies
echo "Installing system libraries..."
sudo apt install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tcl8.6-dev \
    tk8.6-dev \
    libsqlite3-dev \
    libreadline-dev \
    libbz2-dev

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers xxhash pillow psutil requests tqdm

echo
echo "Dependencies installed successfully!"
echo "You can now run the DupeRangerAi executable."
echo
echo "To run:"
echo "./DupeRangerAi"
echo
echo "Note: The executable is self-contained and includes all Python dependencies."
echo "This installer was mainly for setting up a development environment."

'@

$InstallerScript | Out-File -FilePath "$OutputDir/install_deps_ubuntu.sh" -Encoding UTF8

# Make the installer executable (using bash since we're on Linux)
bash -c "chmod +x '$OutputDir/install_deps_ubuntu.sh'"

# Create a README for Ubuntu
$ReadmeContent = @"
# DupeRangerAi for Ubuntu

This is a portable version of DupeRangerAi built for Ubuntu 22.04.

## Quick Start

1. Make the executable runnable:
   ```bash
    chmod +x DupeRangerAi
   ```

2. Run the application:
   ```bash
    ./DupeRangerAi
   ```

## System Requirements

- Ubuntu 22.04 or compatible Linux distribution
- No additional Python installation required (all dependencies are bundled)

## Features

- Duplicate file detection using fast hashing (xxHash + SHA-256)
- AI-powered file categorization using Hugging Face transformers
- Automatic file organization by categories
- Duplicate retention policies (keep oldest/newest)
- Safe operations with dry-run mode
- ZFS-compatible file operations

## Included Files

- `DupeRangerAi` - Main executable
- `INSTRUCTIONS.html` - Detailed user guide
- `INSTRUCTIONS.txt` - Text version of instructions
- `install_deps_ubuntu.sh` - Ubuntu dependency installer (for development)
- `synthetic_test.py` - Test script for duplicate detection
- `test_actions.py` - Test script for file operations

## Development Setup

If you want to modify the source code:

1. Run the dependency installer:
   ```bash
   ./install_deps_ubuntu.sh
   ```

2. The script will create a virtual environment and install all dependencies.

## Troubleshooting

- If the executable won't run, ensure it has execute permissions:
    ```bash
    chmod +x DupeRangerAi
    ```

- For GPU support, install CUDA-compatible PyTorch (not included in portable build)

## Build Information

Built on: $(Get-Date)
Python version: $(& $PythonCmd --version 2>$null)
PyTorch: $(& $PythonCmd -c "import torch; print(torch.__version__)" 2>$null)
CUDA: $(& $PythonCmd -c "import torch; print('Available' if torch.cuda.is_available() else 'Not available')" 2>$null)

"@

$ReadmeContent | Out-File -FilePath "$OutputDir/README_ubuntu.md" -Encoding UTF8

# Set executable permissions
Write-Host "Setting executable permissions..."
bash -c "chmod +x '$OutputDir/$ScriptName'"

# Show build results
Write-Host
Write-Host "=== Build Complete ===" -ForegroundColor Green
Write-Host "Output directory: $OutputDir"
Write-Host "Contents:"
Get-ChildItem $OutputDir | Format-Table -AutoSize
Write-Host
Write-Host "To test the build:"
Write-Host "cd $OutputDir && ./$ScriptName"
Write-Host
Write-Host "To create a distribution archive:"
Write-Host "tar -czf ${OutputDir}.tar.gz $OutputDir"
Write-Host

# Test the executable if requested
if ($Test) {
    Write-Host "Testing executable..."
    if (Test-Path "$OutputDir/$ScriptName" -PathType Leaf) {
        Write-Host "✅ Executable is ready!"
        # Try to get version info (if available)
        try {
            $timeout = [System.Diagnostics.Stopwatch]::StartNew()
            $process = Start-Process -FilePath "$OutputDir/$ScriptName" -ArgumentList "--version" -NoNewWindow -PassThru
            while (!$process.HasExited -and $timeout.Elapsed.TotalSeconds -lt 5) {
                Start-Sleep -Milliseconds 100
        # Make executable naming consistent with DupeRangerAi
                Write-Host "GUI application - no version flag available"
            }
        } catch {
            Write-Host "GUI application - no version flag available"
        }
    } else {
        Write-Error "❌ Executable not found or not executable"
        exit 1
    }
}

Write-Host
Write-Host "=== Ubuntu Package Ready ===" -ForegroundColor Green
Write-Host "The $OutputDir folder contains everything needed for Ubuntu 22.04 distribution."