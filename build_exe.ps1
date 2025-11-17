# Build script for AiDupeRanger_grok executable
# Creates a standalone Windows executable and collates all files

param(
    [switch]$Clean,
    [switch]$OneFile,
    [string]$OutputDir = "AiDupeRanger_grok",
    [string]$EntryScript = "AiDupeRanger_grok.py"  # entry script to build (default: grok variant)
)

$ErrorActionPreference = "Stop"

Write-Host "Building AiDupeRanger_grok executable..." -ForegroundColor Cyan

# Clean previous builds if requested
if ($Clean) {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue dist, build, *.spec, $OutputDir
}

# Activate venv
$venvPath = ".venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
} else {
    Write-Error "Virtual environment not found. Run install_deps.ps1 first."
    exit 1
}

# Install PyInstaller if needed
Write-Host "Ensuring PyInstaller is installed..." -ForegroundColor Green
python -m pip install --quiet pyinstaller

# Determine build mode
$buildMode = if ($OneFile) { "--onefile" } else { "--onedir" }
Write-Host "Build mode: $buildMode" -ForegroundColor Cyan

# Build with PyInstaller
Write-Host "Running PyInstaller..." -ForegroundColor Green
Write-Host "Building entry script: $EntryScript" -ForegroundColor Cyan

$name = [System.IO.Path]::GetFileNameWithoutExtension($EntryScript)
$pyInstallerArgs = @(
    "--name=$name",
    $buildMode,
    "--windowed",
    "--clean",
    "--noconfirm",
    "--hidden-import=torch",
    "--hidden-import=transformers",
    "--hidden-import=tokenizers",
    "--hidden-import=huggingface_hub",
    "--hidden-import=xxhash",
    "--hidden-import=accelerate",
    "--hidden-import=sentencepiece",
    "--collect-all=torch",
    "--collect-all=transformers",
    "--collect-all=tokenizers",
    "--collect-data=torch",
    "--collect-data=transformers",
    "--collect-data=tokenizers",
    "--add-data=.venv/Lib/site-packages/transformers;transformers",
    "--add-data=.venv/Lib/site-packages/tokenizers;tokenizers",
    $EntryScript
)

& python -m PyInstaller @pyInstallerArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed!"
    exit 1
}

# Create output directory
Write-Host "Creating output directory: $OutputDir" -ForegroundColor Cyan
if (Test-Path $OutputDir) {
    Remove-Item -Recurse -Force $OutputDir
}
New-Item -ItemType Directory -Path $OutputDir | Out-Null

# Copy executable
Write-Host "Copying executable..." -ForegroundColor Green
if ($OneFile) {
    Copy-Item "dist\$name.exe" $OutputDir\
} else {
    Copy-Item -Recurse "dist\$name\*" $OutputDir\
}

# Copy documentation and scripts
Write-Host "Copying documentation and scripts..." -ForegroundColor Green
Copy-Item "docs\*" $OutputDir\ -Recurse -ErrorAction SilentlyContinue
Copy-Item "synthetic_test.py" $OutputDir\
Copy-Item "test_actions.py" $OutputDir\
Copy-Item "install_deps.ps1" $OutputDir\
Copy-Item "README.md" $OutputDir\ -ErrorAction SilentlyContinue

# Create a simple README for the packaged version
$readmeContent = @"
# AiDupeRanger_grok

AI-powered duplicate file finder and organizer for Windows.

## Features
- Fast duplicate detection using xxHash and SHA-256
- AI-powered file categorization using Hugging Face transformers
- Automatic organization by file type
- Duplicate handling with retention policies
- ZFS-aware design

## Usage
Run AiDupeRanger_grok.exe to start the application.

## Requirements
- Windows 10/11
- NVIDIA GPU recommended for AI features
- ~2-4 GB free disk space for AI models (downloaded on first run)

## Safety
- Always create ZFS snapshots before applying actions
- Use dry-run mode to preview changes
- Test on small directories first

## Support
Built with PyTorch and Transformers. Requires compatible GPU drivers for CUDA acceleration.
"@

$readmeContent | Out-File -FilePath "$OutputDir\README.md" -Encoding UTF8

# Get build info
$exePath = if ($OneFile) { "$OutputDir\$name.exe" } else { "$OutputDir\$name.exe" }
$exeSize = if (Test-Path $exePath) {
    [math]::Round((Get-Item $exePath).Length / 1MB, 2)
} else { "N/A" }

Write-Host "`nBuild complete!" -ForegroundColor Green
Write-Host "Output directory: $OutputDir" -ForegroundColor Cyan
Write-Host "Executable size: $exeSize MB" -ForegroundColor Cyan
Write-Host "Files included:" -ForegroundColor Cyan
Get-ChildItem $OutputDir -Recurse | Where-Object { !$_.PSIsContainer } | ForEach-Object {
    $relativePath = $_.FullName.Replace((Resolve-Path $OutputDir).Path + "\", "")
    Write-Host "  $relativePath" -ForegroundColor Gray
}

Write-Host "`nTo run: $OutputDir\$name.exe" -ForegroundColor Yellow