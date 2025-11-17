# Build Script for DupeRangerAi
# This script packages the application into a Windows executable using PyInstaller

param(
    [switch]$Clean,
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DupeRangerAi Build Script for Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$ScriptName = "DupeRangerAi"
$OutputFolder = "DupeRangerAi_Package"
$DistFolder = "dist"
$BuildFolder = "build"

# Clean previous builds if requested
if ($Clean) {
    Write-Host "[1/6] Cleaning previous builds..." -ForegroundColor Yellow
    if (Test-Path $DistFolder) {
        Remove-Item -Recurse -Force $DistFolder
        Write-Host "  ✓ Removed $DistFolder" -ForegroundColor Green
    }
    if (Test-Path $BuildFolder) {
        Remove-Item -Recurse -Force $BuildFolder
        Write-Host "  ✓ Removed $BuildFolder" -ForegroundColor Green
    }
    if (Test-Path $OutputFolder) {
        Remove-Item -Recurse -Force $OutputFolder
        Write-Host "  ✓ Removed $OutputFolder" -ForegroundColor Green
    }
    Write-Host ""
}

# Check if Python is available
Write-Host "[2/6] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "  ✓ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found in PATH!" -ForegroundColor Red
    Write-Host "  Please install Python 3.8+ and add it to PATH" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Install PyInstaller if not already installed
if (-not $SkipInstall) {
    Write-Host "[3/6] Installing/Updating PyInstaller..." -ForegroundColor Yellow
    try {
        & python -m pip install --upgrade pyinstaller | Out-Null
        Write-Host "  ✓ PyInstaller ready" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed to install PyInstaller" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
} else {
    Write-Host "[3/6] Skipping PyInstaller installation..." -ForegroundColor Yellow
    Write-Host ""
}

# Build the executable
Write-Host "[4/6] Building executable with PyInstaller..." -ForegroundColor Yellow
Write-Host "  This may take several minutes..." -ForegroundColor Gray
try {
    & pyinstaller --clean --noconfirm "$ScriptName.spec"
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE"
    }
    Write-Host "  ✓ Executable built successfully" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Build failed: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Create package folder structure
Write-Host "[5/6] Creating package folder..." -ForegroundColor Yellow

# Create main package folder
if (-not (Test-Path $OutputFolder)) {
    New-Item -ItemType Directory -Path $OutputFolder | Out-Null
}

# Copy executable from dist
$exePath = Join-Path $DistFolder "$ScriptName.exe"
if (Test-Path $exePath) {
    Copy-Item $exePath -Destination $OutputFolder
    Write-Host "  ✓ Copied executable: $ScriptName.exe" -ForegroundColor Green
} else {
    Write-Host "  ✗ Executable not found at $exePath" -ForegroundColor Red
    exit 1
}

# Copy README if exists
$readmePath = "README_Package.md"
if (Test-Path $readmePath) {
    Copy-Item $readmePath -Destination (Join-Path $OutputFolder "README.md")
    Write-Host "  ✓ Copied README" -ForegroundColor Green
}

# Copy LICENSE if exists
if (Test-Path "LICENSE.txt") {
    Copy-Item "LICENSE.txt" -Destination $OutputFolder
    Write-Host "  ✓ Copied LICENSE" -ForegroundColor Green
}

# Create Examples folder
$examplesFolder = Join-Path $OutputFolder "Examples"
if (-not (Test-Path $examplesFolder)) {
    New-Item -ItemType Directory -Path $examplesFolder | Out-Null
}

Write-Host "  ✓ Package folder created: $OutputFolder" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "[6/6] Build Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Package Location: $OutputFolder\" -ForegroundColor Cyan
Write-Host "Executable: $OutputFolder\$ScriptName.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host "To distribute:" -ForegroundColor Yellow
Write-Host "  1. Zip the '$OutputFolder' folder" -ForegroundColor White
Write-Host "  2. Users can extract and run $ScriptName.exe" -ForegroundColor White
Write-Host "  3. No Python installation required for end users!" -ForegroundColor White
Write-Host ""
Write-Host "To test:" -ForegroundColor Yellow
Write-Host "  cd $OutputFolder" -ForegroundColor White
Write-Host "  .\$ScriptName.exe" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
