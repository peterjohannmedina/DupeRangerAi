<#
PowerShell installer for DupeRanger dependencies.
# Usage:
#   .\install_deps.ps1           # CPU install (default)
#   .\install_deps.ps1 -UseGPU   # Attempt GPU install (tries cu130/cu121/cu118 wheels, falls back to CPU)
#>
param(
    [switch]$UseGPU
)

function Write-Status($msg) {
    Write-Host "[installer] $msg"
}

# Ensure python is available
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Python not found in PATH. Please install Python 3.10+ and add it to PATH: https://www.python.org/downloads/"
    exit 1
}

# Create venv if missing
$venvPath = Join-Path -Path (Get-Location) -ChildPath ".venv"
$venvPython = Join-Path -Path $venvPath -ChildPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Status "Creating virtual environment at '$venvPath'..."
    & python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) { Write-Error "Failed to create virtual environment"; exit 1 }
} else {
    Write-Status "Virtual environment detected at '$venvPath'"
}

# Use venv python to install packages
Write-Status "Upgrading pip in the venv..."
& $venvPython -m pip install --upgrade pip setuptools wheel | Out-Host
if ($LASTEXITCODE -ne 0) { Write-Warning "pip upgrade may have failed; continuing..." }

# Basic Python packages
$basePkgs = @(
    'transformers',
    'huggingface_hub',
    'accelerate',
    'sentencepiece',
    'xxhash'
)

Write-Status "Installing base Python packages: $($basePkgs -join ', ')"
& $venvPython -m pip install $basePkgs | Out-Host
if ($LASTEXITCODE -ne 0) { Write-Warning "One or more base packages failed to install; check output." }

# Install torch (GPU or CPU)
if ($UseGPU) {
    Write-Status "Attempting GPU-enabled PyTorch install. The installer will try to detect CUDA via nvidia-smi and choose a matching wheel (falls back to CPU on failure)."
    # Prefer recent CUDA runtime tag (try cu130 first), then fallback to other known tags
    $cuTag = 'cu130'
    $nvsCmd = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if ($nvsCmd) {
        try {
            $nvsOut = & nvidia-smi 2>&1
            if ($nvsOut -match 'CUDA Version:\s*(\d+\.\d+)') {
                $cudaVer = $Matches[1]
                # convert 13.0 -> 130, 12.1 -> 121, 11.8 -> 118
                $digits = $cudaVer -replace '\.',''
                $cuTagDetected = "cu$digits"
                Write-Status "Detected CUDA version $cudaVer -> suggested PyTorch tag $cuTagDetected"
                # prefer cu130 if detected matches; otherwise keep cuTagDetected as first preference
                if ($cuTagDetected -eq 'cu130') { $cuTag = 'cu130' } else { $cuTag = $cuTagDetected }
            } else {
                Write-Warning "Could not parse CUDA version from nvidia-smi output; defaulting to $cuTag"
            }
        } catch {
            Write-Warning "Failed to run nvidia-smi; defaulting to $cuTag"
        }
    } else {
        Write-Warning "nvidia-smi not found in PATH; defaulting to $cuTag"
    }

    # Try tags in order: cu130, <detected>, cu121, cu118, cu117
    $candidateTags = @('cu130')
    if ($cuTag -and ($cuTag -ne 'cu130')) { $candidateTags += $cuTag }
    $candidateTags += @('cu121','cu118','cu117')
    $preferredTags = $candidateTags | Select-Object -Unique

    $installed = $false
    foreach ($tag in $preferredTags) {
        try {
            Write-Status "Attempting PyTorch wheel with tag: $tag"
            & $venvPython -m pip install --index-url "https://download.pytorch.org/whl/$tag" torch torchvision torchaudio --extra-index-url https://pypi.org/simple | Out-Host
            if ($LASTEXITCODE -eq 0) {
                Write-Status "Installed torch with tag: $tag"
                $installed = $true
                break
            } else {
                Write-Warning "Install attempt with $tag returned non-zero exit code"
            }
        } catch {
            Write-Warning "Install attempt with $tag failed: $_"
        }
    }

    if (-not $installed) {
        Write-Warning "All GPU wheel attempts failed. Falling back to CPU-only install."
        & $venvPython -m pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio --extra-index-url https://pypi.org/simple | Out-Host
        if ($LASTEXITCODE -ne 0) { Write-Error "Fallback CPU torch install failed. Please install manually."; exit 1 }
    }

    # Quick verification: print torch build info from the venv python
    try {
        Write-Status "Verifying installed torch build..."
        & $venvPython -c "import torch,sys; print('torch.__version__:', getattr(torch,'__version__',None)); print('torch.version.cuda:', getattr(torch.version,'cuda',None)); print('torch.cuda.is_available():', torch.cuda.is_available())" | Out-Host
    } catch {
        Write-Warning "Could not run verification command: $_"
    }
} else {
    Write-Status "Installing CPU-only PyTorch wheels. (For GPU use, rerun with -UseGPU and ensure CUDA and drivers are installed.)"
    & $venvPython -m pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio --extra-index-url https://pypi.org/simple | Out-Host
    if ($LASTEXITCODE -ne 0) { Write-Error "CPU torch install failed. Please install manually."; exit 1 }
}

Write-Status "Installation complete. You can run the UI with:"
Write-Host "  .\.venv\Scripts\Activate.ps1  # (optional) activate the venv"
Write-Host "  .\.venv\Scripts\python.exe AiDupeRanger.py"

Write-Status "If you plan to download large models, consider setting a cache location before running the app in this shell:"
Write-Host "  $env:HF_HOME = 'D:\hf_cache'"
Write-Host "  $env:TRANSFORMERS_CACHE = 'D:\hf_cache\transformers'"

exit 0
