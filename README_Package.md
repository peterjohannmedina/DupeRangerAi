# AiDupeRanger - Enhanced File Organizer

**Version:** Claude Enhanced Edition
**Platform:** Windows
**License:** MIT (or your license)

## Overview

AiDupeRanger is an intelligent file organization tool that helps you:

- **Detect Duplicate Files** using SHA-256 cryptographic hashing
- **AI-Powered Categorization** using state-of-the-art language models
- **Automatic Organization** by file type and category
- **Smart Duplicate Handling** with configurable primary file selection
- **Safe Operations** with preview, logging, and rollback capability

---

## Features

### 🔍 Duplicate Detection
- Fast initial fingerprinting using xxhash
- SHA-256 verification for true duplicates
- Choose which file to keep (oldest or most recently modified)
- Automatically mark duplicates with `._dr_` prefix

### 🤖 AI Categorization
- Uses transformer-based models for intelligent file classification
- Categories: Photos, Videos, Audio, Documents, Archives, Code, Spreadsheets, Presentations, Backups, Miscellaneous
- GPU acceleration support (CUDA)
- Falls back to CPU if GPU unavailable

### 📁 File Organization
- Organize files into category-based folders automatically
- Choose destination: subfolders in place or custom directory
- Smart collision handling with numbered suffixes
- Preserves original files until operations are confirmed

### 🛡️ Safety Features
- **Preview Dialog**: Review all planned operations before execution
- **Operation Logging**: Complete transaction log for rollback
- **Error Handling**: Graceful handling of locked files, permission issues
- **Stop Button**: Cancel operations mid-execution
- **Symlink Skipping**: Optionally skip symbolic links and shortcuts

---

## Quick Start

### Basic Usage (Without AI)

1. **Launch the application**: Double-click `DupeRangerAi.exe` (preferred — canonical)

2. **Select a directory**: Click "Browse" and choose the folder to scan

3. **Enable duplicate detection**: Check "Compute SHA-256 hashes"

4. **Scan**: Click the "Scan" button

5. **Review results** in the three tabs:
   - **By Extension**: File type summary
   - **Duplicates**: Detected duplicate files
   - **AI Categories**: (requires AI features enabled)

6. **Mark duplicates** (optional):
   - Check "Mark duplicate files with ._dr_ prefix"
   - Choose primary file mode (oldest or last modified)
   - Click "Apply File Operations..."
   - Review the preview and click "Apply Operations"

### Advanced Usage (With AI Categorization)

**Note:** AI features require PyTorch and Transformers to be installed. The base executable does not include these due to size (~2GB). See "Installing AI Dependencies" below.

1. **Enable AI categorization**: Check "Enable AI categorization"

2. **Choose compute device**: Select Auto, GPU, or CPU

3. **Scan with AI**: Click "Scan" (will be slower than basic scan)

4. **Organize files**:
   - Check "Organize files into category folders"
   - Choose organization location
   - Click "Apply File Operations..."

---

## Installing AI Dependencies

The AI features require additional packages. Install them with:

```powershell
# Open PowerShell in the program directory

# For GPU support (NVIDIA CUDA):
pip install torch transformers --index-url https://download.pytorch.org/whl/cu118

# For CPU-only (smaller, no GPU required):
pip install torch transformers
```

**System Requirements for AI:**
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 2-5GB for models
- **GPU** (optional): NVIDIA GPU with CUDA support for faster processing

---

## Configuration Options

### Scanning Options

| Option | Description | Recommended |
|--------|-------------|-------------|
| **SHA-256 Hashes** | Compute cryptographic hashes for duplicate detection | Enable for duplicate finding |
| **AI Categorization** | Use AI to classify files by type | Enable if AI installed |
| **Workers** | Number of parallel threads | Auto-detected (CPU cores × 2) |
| **Fast Chunk (MB)** | Chunk size for xxhash | 8 MB (local), 1-4 MB (network) |
| **SHA Chunk (MB)** | Chunk size for SHA-256 | 1 MB (good default) |

### Duplicate Handling

| Option | Description |
|--------|-------------|
| **Mark duplicates** | Rename duplicates with `._dr_` prefix |
| **Primary: Oldest** | Keep the oldest file as primary (by creation date) |
| **Primary: Last Modified** | Keep most recently edited file as primary |

### File Organization

| Option | Description |
|--------|-------------|
| **Organize by category** | Move files into category-based folders |
| **Subfolders** | Create folders in the scanned directory |
| **Custom directory** | Specify a different target location |

### Safety Options

| Option | Description | Recommended |
|--------|-------------|-------------|
| **Skip symbolic links** | Don't process symlinks/shortcuts | Enable (default) |
| **Create operation log** | Save detailed log for rollback | Enable (default) |

---

## File Operations

### Duplicate Renaming

When you mark duplicates:

```
Original:
  C:\Photos\image.jpg (primary - oldest)
  C:\Photos\copy\image.jpg (duplicate)
  C:\Downloads\image.jpg (duplicate)

After operation:
  C:\Photos\image.jpg (unchanged)
  C:\Photos\copy\._dr_image.jpg (marked as duplicate)
  C:\Downloads\._dr_image.jpg (marked as duplicate)
```

### Category Organization

When you organize by category:

```
Original:
  C:\Files\document.pdf
  C:\Files\photo.jpg
  C:\Files\song.mp3

After operation:
  C:\Files\Documents\document.pdf
  C:\Files\Photos\photo.jpg
  C:\Files\Audio\song.mp3
```

---

## Operation Log

When "Create operation log" is enabled, the application saves a detailed JSON log:

**Location:** `<scanned_directory>\duperanger_operations.json`

**Contains:**
- Operation type (rename_duplicate or organize_category)
- Source and destination paths
- Status (completed, failed, skipped)
- Error messages (if any)
- Timestamp

This log can be used to manually rollback operations if needed.

---

## Troubleshooting

### "AI categorization unavailable"

**Cause:** PyTorch/Transformers not installed
**Solution:** Install AI dependencies (see "Installing AI Dependencies" above)

### "Permission denied" errors

**Cause:** Files are open in another program or insufficient permissions
**Solution:**
- Close files before scanning
- Run as Administrator if needed
- Check file/folder permissions

### "File is in use by another process"

**Cause:** Windows has the file locked
**Solution:**
- Close programs using the file
- Retry the operation
- Check the skipped files in the operation summary

### Scan is very slow

**Causes:**
- Large number of files
- AI categorization enabled (slower)
- Network storage (slower)

**Solutions:**
- Reduce worker count
- Decrease chunk sizes for network storage
- Disable AI if not needed
- Use GPU for AI (if available)

### Executable won't start

**Cause:** Missing system dependencies
**Solution:** Install Visual C++ Redistributables:
- Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Run installer and restart computer

---

## Performance Tips

### For Local Storage (SSD/NVMe)
- Workers: 8-16
- Fast Chunk: 8-16 MB
- SHA Chunk: 1-2 MB

### For Network Storage (NAS/SMB)
- Workers: 4-8
- Fast Chunk: 1-4 MB
- SHA Chunk: 0.5-1 MB

### For AI Categorization
- Use GPU if available (much faster)
- Reduce worker count if running out of memory
- Close other applications to free RAM

---

## Command Line Usage

The executable also supports running from command line:

```powershell
# Launch GUI normally
.\AiDupeRanger_claude.exe

# Future: Command-line mode (not yet implemented)
# .\DupeRangerAi.exe --scan "C:\Photos" --duplicates --organize
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Browse for directory (when path entry focused) |
| `Ctrl+S` | Start scan (when not scanning) |
| `Esc` | Stop scan (when scanning) |

---

## Privacy & Security

- **No Network Activity**: All processing happens locally on your computer
- **No Data Collection**: No telemetry or analytics
- **No Cloud**: AI models run entirely on your machine
- **Safe Operations**: Preview all changes before applying
- **Reversible**: Operation logs allow manual rollback

---

## System Requirements

### Minimum (Basic Features)
- **OS**: Windows 10 or later (64-bit)
- **RAM**: 2GB
- **Disk**: 100MB free space
- **CPU**: Any modern processor

### Recommended (With AI)
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 8GB
- **Disk**: 5GB free space (for AI models)
- **CPU**: Quad-core or better
- **GPU**: NVIDIA GPU with 4GB+ VRAM (optional, for acceleration)

---

## Credits

**Enhanced by:** Claude (Anthropic)
**Based on:** ZFS File Organizer Helper
**AI Models:** Hugging Face Transformers (DistilBART)

**Key Technologies:**
- Python 3.8+
- PyInstaller (for executable packaging)
- Tkinter (GUI framework)
- PyTorch & Transformers (AI features)
- xxhash (fast hashing)

---

## Support

For issues, questions, or feature requests:
- Check the troubleshooting section above
- Review the operation log for error details
- Ensure all dependencies are installed

---

## License

[Add your license information here]

---

## Changelog

### Version: Claude Enhanced Edition
- ✨ Added smart duplicate handling with ._dr_ prefix
- ✨ Added primary file selection (oldest/last modified)
- ✨ Added AI-powered file organization
- ✨ Added preview dialog for operations
- ✨ Added operation logging and rollback capability
- ✨ Added safety options (symlink skipping)
- ✨ Enhanced UI with new control sections
- ✨ Improved error handling and reporting
- 🐛 Fixed various edge cases in file operations
- 📝 Comprehensive documentation

---

**Thank you for using AiDupeRanger!** 🚀
