# AiDupeRanger Development Guide

## Project Overview
AiDupeRanger is a Python desktop application for intelligent duplicate file detection and organization. It combines fast hashing algorithms with AI-powered file categorization using Hugging Face transformers, built as a standalone Windows executable via PyInstaller.

**Primary Variant**: `AiDupeRanger_grok.py` is the main developed version with full AI integration. Other variants (`AiDupeRanger_claude.py`, `AiDupeRanger.py`) exist for different configurations or legacy compatibility.

## Architecture

### Core Components
- **FileScanner**: Multi-threaded scanner using two-phase hashing (xxhash → SHA-256)
- **FileClassifier**: AI categorization via zero-shot classification pipeline
- **FileOrganizerApp**: Tkinter-based GUI with incremental UI updates
- **FileRecord/ScanResults**: Data structures for file metadata and scan results

### Key Design Patterns
- **Two-phase duplicate detection**: Fast xxhash fingerprinting groups candidates, SHA-256 verifies true duplicates
- **Threaded execution**: Configurable worker pools with incremental UI updates via Queue
- **GPU/CPU fallback**: Automatic device detection with graceful degradation for AI features
- **Preview-before-apply**: All file operations shown in preview dialog before execution
- **ZFS-aware**: Designed for filesystem snapshots and safe operations

## Development Workflow

### Environment Setup
```powershell
# Install dependencies (CPU-only)
.\install_deps.ps1

# Install with GPU support
.\install_deps.ps1 -UseGPU
```

### Building Executables
```powershell
# Quick build (grok variant with AI)
.\build_exe.ps1

# Clean rebuild
.\build_exe.ps1 -Clean

# One-file executable
.\build_exe.ps1 -OneFile
```

### Testing
```python
# Performance testing with synthetic data
python synthetic_test.py

# Action testing (file operations)
python test_actions.py
```

## Code Patterns & Conventions

### File Scanning Architecture
```python
# Two-phase scanning pattern
class FileScanner:
    def run(self):
        # Phase 1: Fast fingerprinting + optional AI classification
        self._scan_with_xxhash_and_optional_ai()
        
        # Phase 2: SHA-256 verification for candidate duplicates
        if self.compute_hashes:
            self._verify_candidates_with_sha256()
```

### AI Classification Pattern
```python
class FileClassifier:
    def classify(self, record: FileRecord) -> str:
        prompt = f"Classify this file: {record.path.name} ({record.extension})"
        result = self._pipeline(prompt, candidate_labels=CATEGORY_LABELS)
        return result["labels"][0]
```

### Threading with UI Updates
```python
# Producer-consumer pattern for incremental updates
scanner = FileScanner(queue=self.queue, ...)
scanner.start()

while True:
    message = self.queue.get()
    if message["type"] == "record":
        self._update_ui_incrementally(message["record"])
    elif message["type"] == "done":
        break
```

### Error Handling Patterns
```python
# Graceful AI fallback
try:
    classifier = FileClassifier(device_preference="auto")
except RuntimeError:
    # Fallback to CPU or disable AI features
    classifier = None

# Safe file operations with permission handling
try:
    record = self._inspect_file(file_path)
except (PermissionError, FileNotFoundError):
    return None
```

## Configuration & Dependencies

### Build Configuration
- **PyInstaller spec files**: `AiDupeRanger_*.spec` control executable bundling
- **Hidden imports**: AI libraries bundled separately to reduce base executable size
- **Data collection**: Model files and tokenizers collected for standalone operation

### Dependency Management
```python
# Core (always bundled)
pyinstaller, xxhash

# AI (bundled in grok variant, external in base/claude variants)
torch, transformers, huggingface_hub, accelerate, sentencepiece
```

### Performance Tuning
- **Chunk sizes**: 8MB fast hash, 1MB SHA-256 (configurable)
- **Worker count**: Auto-detected (CPU cores × 2), max 32
- **GPU memory**: Automatic fallback to CPU on OOM
- **Model selection**: DistilBART for compact zero-shot classification

#### Storage-Specific Optimization
- **NVMe SSD**: Fast chunks 8-16MB, SHA chunks 1-2MB, workers CPU×2
- **SATA SSD/HDD**: Fast chunks 4-8MB, SHA chunks 0.5-1MB, workers CPU×1.5
- **Network/SMB**: Fast chunks 1-4MB, SHA chunks 0.25-0.5MB, workers 4-8 max
- **USB/External**: Fast chunks 0.5-2MB, SHA chunks 0.125-0.25MB, workers 2-4 max

## Common Development Tasks

### Adding New File Categories
1. Update `CATEGORY_LABELS` in `FileClassifier`
2. Test classification accuracy with diverse file types
3. Update UI display logic if needed

### Performance Optimization
1. Profile with `synthetic_test.py` using large file sets
2. Adjust chunk sizes based on storage type (NVMe: 8-16MB, Network: 1-4MB)
3. Monitor GPU memory usage during AI classification
4. Use storage-appropriate worker counts (NVMe: CPU×2, Network: 4-8 max)

### Build Optimization
1. Use `--onedir` for development, `--onefile` for distribution
2. Exclude unused modules in spec files
3. Enable UPX compression for smaller executables

### Testing File Operations
1. Use `test_actions.py` to validate rename/organize operations
2. Test on various filesystem types (NTFS, ZFS)
3. Verify operation rollback via JSON logs

## Debugging & Troubleshooting

### Common Issues
- **AI unavailable**: Check PyTorch installation and CUDA compatibility
- **Slow scanning**: Increase chunk sizes for local storage, decrease for network
- **Permission errors**: Run as administrator or check file/folder permissions
- **Build failures**: Ensure all dependencies installed in virtual environment

### Debug Builds
```python
# Enable console output in spec file
console=True

# Add debug prints to scanner threads
print(f"Processing: {file_path}")
```

### Performance Monitoring
```python
# Time scanning phases
start = time.time()
# ... operation ...
elapsed = time.time() - start
print(f"Phase completed in {elapsed:.2f}s")
```

## File Organization Standards

### Source Files
- `DupeRangerAi.py`: **Primary developed version** with full AI integration and file organization
- `AiDupeRanger_grok.py`: Previous grok variant (deprecated)
- `AiDupeRanger_claude.py`: Alternative variant with different configuration
- `AiDupeRanger.py`: Base implementation without AI features
- `tk_file_organizer.py`: Legacy/backup implementation
- `*_test.py`: Test scripts for validation

### Build Artifacts
- `build/`: PyInstaller temporary files (safe to delete)
- `dist/`: PyInstaller output (safe to delete)
- `AiDupeRanger_*_Package/`: Final distributable packages

### Configuration Files
- `*.spec`: PyInstaller specifications
- `requirements.txt`: Python dependencies
- `install_deps.ps1`: Automated dependency installation
- `build_*.ps1`: Build scripts for different platforms

## Integration Points

### External Dependencies
- **Hugging Face**: Model downloads and caching (~2-5GB)
- **PyTorch**: GPU acceleration via CUDA
- **Tkinter**: Native Windows GUI
- **PyInstaller**: Cross-platform executable creation

### System Integration
- **Filesystem**: NTFS/ZFS snapshot awareness
- **GPU**: NVIDIA CUDA detection and utilization
- **Environment**: Virtual environment isolation
- **Caching**: HF_HOME and TRANSFORMERS_CACHE configuration

## Safety & Best Practices

### File Operations
- Always preview operations before applying
- Create filesystem snapshots before bulk operations
- Log all operations to JSON for rollback
- Handle locked files gracefully

### AI Model Management
- Download models on-demand to reduce bundle size
- Cache models locally to avoid repeated downloads
- Fallback to CPU if GPU memory insufficient
- Handle network timeouts during model loading

### Cross-Platform Considerations
- Built primarily for Windows (Tkinter + PyInstaller)
- Linux/Mac builds possible but not primary target
- CUDA support Windows/Linux only

## Performance Characteristics

### Scanning Performance
- **Fast phase**: xxhash at 8MB chunks, ~500MB/s SSD
- **Verify phase**: SHA-256 at 1MB chunks, ~100MB/s SSD
- **AI phase**: Variable, GPU ~10x faster than CPU

### Memory Usage
- **Base scanning**: ~50MB RAM
- **AI classification**: +2-4GB GPU memory
- **Large scans**: Scales with file count, not size

### Build Sizes
- **Base executable** (`AiDupeRanger.py`): ~30MB (no AI bundled)
- **AI executable** (`AiDupeRanger_grok.py`): ~1.5GB (with PyTorch GPU)
- **Build time**: 2-30 minutes depending on configuration