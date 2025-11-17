# Build Instructions for AiDupeRanger_claude

This document explains how to build the Windows executable from source.

---

## Prerequisites

### Required Software

1. **Python 3.8 or later** (3.10+ recommended)
   - Download from: https://www.python.org/downloads/
   - ✅ **Important**: Check "Add Python to PATH" during installation

2. **Git** (optional, for version control)
   - Download from: https://git-scm.com/downloads/

3. **Visual C++ Redistributables** (for PyInstaller)
   - Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Python Packages

Install required packages:

```powershell
# Core dependencies
pip install pyinstaller xxhash

# Optional: AI features (adds ~5GB)
pip install torch transformers
# Or for GPU support:
pip install torch transformers --index-url https://download.pytorch.org/whl/cu118
```

Or install all from requirements.txt:

```powershell
pip install -r requirements.txt
```

---

## Build Methods

### Method 1: Using PowerShell Script (Recommended)

The easiest way to build:

```powershell
# Navigate to project directory
cd C:\Users\NM2\Documents\DevProjects\DupeRanger

# Run build script
.\build_windows.ps1

# Or for clean build (removes previous builds first):
.\build_windows.ps1 -Clean
```

**Output:** `AiDupeRanger_claude_Package\` folder with the executable

### Method 2: Using Batch File

For users who prefer batch files:

```cmd
REM Navigate to project directory
cd C:\Users\NM2\Documents\DevProjects\DupeRanger

REM Normal build
build.bat

REM Clean build
build.bat clean
```

### Method 3: Manual PyInstaller Command

For advanced users:

```powershell
# Using the spec file (recommended)
pyinstaller --clean --noconfirm DupeRangerAi.spec

# Or build without spec file
pyinstaller --onefile --windowed --name=AiDupeRanger_claude AiDupeRanger_claude.py
```

---

## Build Configuration

### Spec File Options

Edit `AiDupeRanger_claude.spec` to customize the build (note: this grok/claude variant is archived; prefer `DupeRangerAi.py` for current builds):

#### Include AI Dependencies

By default, AI libraries (torch, transformers) are **not bundled** to reduce executable size.

To bundle AI features:

1. Open `AiDupeRanger_claude.spec`
2. Uncomment these lines in `hiddenimports`:
   ```python
   'torch',
   'transformers',
   'huggingface_hub',
   ```
3. Rebuild

**Warning:** This will increase the executable size to ~1-2 GB and build time to 10-30 minutes.

#### Add Application Icon

1. Create or obtain a `.ico` file (256x256 recommended)
2. Place it in the project directory
3. Edit `AiDupeRanger_claude.spec`, change:
   ```python
   icon=None,  # Change to:
   icon='your_icon.ico',
   ```

#### Console Window

To show a console window (for debugging):

Edit `AiDupeRanger_claude.spec`, change:
```python
console=False,  # Change to:
console=True,
```

#### UPX Compression

UPX compression is enabled by default to reduce file size.

To disable (faster builds, larger file):
```python
upx=True,  # Change to:
upx=False,
```

---

## Build Process Details

### What the Build Script Does

1. **Cleans** previous builds (if `-Clean` flag used)
2. **Checks** Python installation
3. **Installs/Updates** PyInstaller
4. **Runs** PyInstaller with the spec file
5. **Creates** package folder structure
6. **Copies** executable and documentation
7. **Reports** build status

### Build Output

After a successful build, you'll have:

```
DupeRanger/
├── DupeRangerAi.py          # Source code (canonical entry)
├── DupeRangerAi.spec        # PyInstaller configuration (preferred)
├── build_windows.ps1               # Build script
├── build.bat                       # Batch build script
├── requirements.txt                # Python dependencies
├── README_Package.md               # User documentation
├── BUILD_INSTRUCTIONS.md           # This file
│
├── build/                          # Temporary build files (safe to delete)
├── dist/                           # PyInstaller output (safe to delete)
│   └── AiDupeRanger_claude.exe
│
└── AiDupeRanger_claude_Package/    # Final package (ready to distribute)
    ├── AiDupeRanger_claude.exe
    ├── README.md
    └── Examples/
```

---

## Build Options Reference

### PowerShell Script Flags

| Flag | Description |
|------|-------------|
| `-Clean` | Remove previous builds before building |
| `-SkipInstall` | Skip PyInstaller installation check |

Example:
```powershell
.\build_windows.ps1 -Clean -SkipInstall
```

### PyInstaller Spec File Options

| Option | Default | Description |
|--------|---------|-------------|
| `name` | `AiDupeRanger_claude` | Executable name |
| `console` | `False` | Show console window |
| `upx` | `True` | Enable UPX compression |
| `icon` | `None` | Application icon |
| `hiddenimports` | See spec | Modules to include |
| `excludes` | See spec | Modules to exclude |

---

## Build Sizes

Approximate executable sizes:

| Configuration | Size | Build Time |
|---------------|------|------------|
| **Base** (no AI) | ~30 MB | 2-5 min |
| **With xxhash** | ~32 MB | 2-5 min |
| **With PyTorch (CPU)** | ~500 MB | 10-20 min |
| **With PyTorch (GPU)** | ~1.5 GB | 20-30 min |

---

## Troubleshooting Build Issues

### "pyinstaller: command not found"

**Solution:**
```powershell
pip install --upgrade pyinstaller
# Then verify:
pyinstaller --version
```

### "ModuleNotFoundError" during build

**Cause:** Missing dependency

**Solution:** Add to `hiddenimports` in spec file:
```python
hiddenimports=[
    'missing_module_name',
    # ... other imports
],
```

### Build succeeds but executable won't run

**Cause:** Missing DLL or runtime

**Solutions:**
1. Install Visual C++ Redistributables
2. Build with `console=True` to see error messages
3. Check for missing imports in spec file

### "RecursionError" during build

**Cause:** Too many nested imports

**Solution:** Increase recursion limit in spec file:
```python
import sys
sys.setrecursionlimit(5000)
```

### Build is very slow

**Causes & Solutions:**
- **UPX compression:** Disable with `upx=False`
- **Large dependencies:** Use `excludes` to skip unused modules
- **Antivirus:** Add project folder to exceptions

### Executable is too large

**Solutions:**
1. Don't bundle AI dependencies (install separately)
2. Add more items to `excludes` in spec file
3. Disable UPX compression (paradoxically sometimes helps)
4. Use `--onefile` instead of `--onedir`

---

## Testing the Build

### Quick Test

```powershell
cd AiDupeRanger_claude_Package
.\AiDupeRanger_claude.exe
```

### Comprehensive Test

1. **Launch**: Verify application opens
2. **Browse**: Select a test directory
3. **Scan**: Run a basic scan without AI
4. **Review**: Check all three tabs populate
5. **Duplicate Detection**: Enable SHA-256, scan again
6. **Operations**: Try marking duplicates (preview only, cancel)
7. **Export**: Test JSON export functionality

### Testing AI Features

Only if AI dependencies are installed:

1. Enable "AI categorization"
2. Verify model downloads on first run
3. Check category assignments
4. Test file organization

---

## Distribution

### Creating Release Package

1. Build the application
2. Test the executable
3. Zip the package folder:
   ```powershell
   Compress-Archive -Path AiDupeRanger_claude_Package -DestinationPath AiDupeRanger_claude_v1.0.zip
   ```

### What to Distribute

**Minimum:**
- `AiDupeRanger_claude.exe`
- `README.md`

**Recommended:**
- Full `AiDupeRanger_claude_Package/` folder
- Installation instructions for AI features
- License file
- Changelog

### Size Considerations

**Without AI bundled (Recommended):**
- ✅ Smaller download (~30 MB)
- ✅ Faster build
- ✅ Users can choose AI installation
- ❌ Requires Python for AI features

**With AI bundled:**
- ✅ Complete standalone package
- ✅ No Python needed
- ❌ Very large download (1-2 GB)
- ❌ Long build time

---

## Advanced Build Scenarios

### Cross-Platform Build (Not Recommended)

PyInstaller creates platform-specific executables. To build for Windows from Linux/Mac:
- Use a Windows VM or Wine
- Or build on Windows machine directly

### Automated CI/CD Build

Example GitHub Actions workflow:

```yaml
name: Build Windows Executable

on: [push, pull_request]

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install pyinstaller xxhash
      - run: pyinstaller --clean --noconfirm AiDupeRanger_claude.spec
      - uses: actions/upload-artifact@v3
        with:
          name: AiDupeRanger_claude
          path: dist/AiDupeRanger_claude.exe
```

### Multi-Version Builds

To build multiple versions (with/without AI):

```powershell
# Build base version
pyinstaller --clean AiDupeRanger_claude.spec
Rename-Item dist\AiDupeRanger_claude.exe AiDupeRanger_claude_base.exe

# Modify spec to include AI dependencies
# (uncomment hiddenimports)

# Build AI version
pyinstaller --clean AiDupeRanger_claude.spec
Rename-Item dist\AiDupeRanger_claude.exe AiDupeRanger_claude_ai.exe
```

---

## Code Signing (Optional)

To sign the executable for Windows SmartScreen:

1. Obtain a code signing certificate
2. Sign the executable:
   ```powershell
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com AiDupeRanger_claude.exe
   ```

---

## Performance Optimization

### Faster Builds

- Use `--noconfirm` flag (skip prompts)
- Disable UPX: `upx=False`
- Use build cache (don't use `--clean` every time)
- Exclude unnecessary modules

### Smaller Executables

- Use `--onefile` mode
- Aggressive excludes in spec file
- Don't bundle AI dependencies
- Enable UPX compression

### Faster Runtime

- Build with AI on CPU if GPU not available to users
- Optimize chunk sizes in default config
- Reduce default worker count

---

## Build Checklist

Before releasing:

- [ ] Test build on clean Windows VM
- [ ] Verify all features work
- [ ] Test without Python installed
- [ ] Check executable size is reasonable
- [ ] Verify README is included
- [ ] Test on Windows 10 and 11
- [ ] Run antivirus scan on executable
- [ ] Document any limitations
- [ ] Update version number/changelog
- [ ] Code sign (if applicable)

---

## Support & Resources

**PyInstaller Documentation:**
https://pyinstaller.org/en/stable/

**Common Issues:**
https://github.com/pyinstaller/pyinstaller/wiki/If-Things-Go-Wrong

**Python Packaging:**
https://packaging.python.org/

---

## License

[Add your license information]

---

**Happy Building!** 🛠️
