#!/bin/bash

# DupeRangerAi Ubuntu Build Script
# Creates a portable executable for Ubuntu 22.04

set -e  # Exit on any error

echo "=== DupeRangerAi Ubuntu Build Script ==="
echo "Building portable executable for Ubuntu 22.04"
echo

# Configuration
SCRIPT_NAME="DupeRangerAi"
BUILD_DIR="build"
DIST_DIR="dist"
OUTPUT_DIR="${SCRIPT_NAME}_ubuntu"

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf "$BUILD_DIR" "$DIST_DIR" "$OUTPUT_DIR"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Virtual environment detected: $VIRTUAL_ENV"
    PYTHON_CMD="python"
    PIP_CMD="pip"
else
    echo "No virtual environment detected. Using system Python."
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
fi

# Install PyInstaller if not present
echo "Checking for PyInstaller..."
if ! $PYTHON_CMD -c "import PyInstaller" 2>/dev/null; then
    echo "Installing PyInstaller..."
    $PIP_CMD install pyinstaller
fi

# Install/update required packages
echo "Installing required packages..."
$PIP_CMD install --upgrade pip
$PIP_CMD install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
$PIP_CMD install transformers xxhash pillow psutil requests tqdm

# Verify CUDA/torch setup (will fallback to CPU if no CUDA)
echo "Verifying PyTorch installation..."
$PYTHON_CMD -c "
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
echo "Building executable with PyInstaller..."
$PYTHON_CMD -m PyInstaller \
    --onefile \
    --windowed \
    --name="DupeRangerAi" \
    --add-data "docs:docs" \
    --hidden-import=torch \
    --hidden-import=torchvision \
    --hidden-import=torchaudio \
    --hidden-import=transformers \
    --hidden-import=xxhash \
    --hidden-import=PIL \
    --hidden-import=psutil \
    --hidden-import=requests \
    --hidden-import=tqdm \
    --hidden-import=sklearn \
    --hidden-import=tokenizers \
    --hidden-import=safetensors \
    --hidden-import=yaml \
    --hidden-import=regex \
    --hidden-import=packaging \
    --hidden-import=filelock \
    --hidden-import=huggingface_hub \
    --hidden-import=jinja2 \
    --hidden-import=markupsafe \
    --hidden-import=numpy \
    --hidden-import=accelerate \
    --hidden-import=tqdm \
    --collect-data transformers \
    --collect-data torch \
    DupeRangerAi.py

# Create output directory
echo "Creating output directory: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Copy executable
echo "Copying executable..."
cp "$DIST_DIR/$SCRIPT_NAME" "$OUTPUT_DIR/"

# Copy documentation and scripts
echo "Copying documentation and scripts..."
cp -r docs/* "$OUTPUT_DIR/" 2>/dev/null || true
cp install_deps.ps1 "$OUTPUT_DIR/" 2>/dev/null || true
cp synthetic_test.py "$OUTPUT_DIR/" 2>/dev/null || true
cp test_actions.py "$OUTPUT_DIR/" 2>/dev/null || true

# Create Ubuntu-specific dependency installer
cat > "$OUTPUT_DIR/install_deps_ubuntu.sh" << 'EOF'
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

EOF

# Make the installer executable
chmod +x "$OUTPUT_DIR/install_deps_ubuntu.sh"

# Create a README for Ubuntu
cat > "$OUTPUT_DIR/README_ubuntu.md" << EOF
# DupeRangerAi for Ubuntu

This is a portable version of DupeRangerAi built for Ubuntu 22.04.

## Quick Start

1. Make the executable runnable:
   \`\`\`bash
    chmod +x DupeRangerAi
   \`\`\`

2. Run the application:
   \`\`\`bash
    ./DupeRangerAi
   \`\`\`

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

## Development Setup

If you want to modify the source code:

1. Run the dependency installer:
   \`\`\`bash
   ./install_deps_ubuntu.sh
   \`\`\`

2. The script will create a virtual environment and install all dependencies.

## Troubleshooting

- If the executable won't run, ensure it has execute permissions:
  \`\`\`bash
    chmod +x DupeRangerAi
  \`\`\`

- For GPU support, install CUDA-compatible PyTorch (not included in portable build)

## Build Information

Built on: $(date)
Python version: $($PYTHON_CMD --version)
PyTorch: $($PYTHON_CMD -c "import torch; print(torch.__version__)")
CUDA: $($PYTHON_CMD -c "import torch; print('Available' if torch.cuda.is_available() else 'Not available')")

EOF

# Set executable permissions
echo "Setting executable permissions..."
chmod +x "$OUTPUT_DIR/$SCRIPT_NAME"

# Show build results
echo
echo "=== Build Complete ==="
echo "Output directory: $OUTPUT_DIR"
echo "Contents:"
ls -la "$OUTPUT_DIR"
echo
echo "To test the build:"
echo "cd $OUTPUT_DIR && ./$SCRIPT_NAME"
echo
echo "To create a distribution archive:"
echo "tar -czf ${OUTPUT_DIR}.tar.gz $OUTPUT_DIR"
echo

# Test the executable (basic check)
echo "Testing executable..."
if [ -x "$OUTPUT_DIR/$SCRIPT_NAME" ]; then
    echo "✅ Executable is ready!"
    # Try to get version info (if available)
    timeout 5s "$OUTPUT_DIR/$SCRIPT_NAME" --version 2>/dev/null || echo "GUI application - no version flag available"
else
    echo "❌ Executable not found or not executable"
    exit 1
fi

echo
echo "=== Ubuntu Package Ready ==="
echo "The $OUTPUT_DIR folder contains everything needed for Ubuntu 22.04 distribution."