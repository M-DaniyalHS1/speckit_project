# setup-venv.ps1 - Script to set up the virtual environment for the AI-Enhanced Interactive Book Agent

Write-Host "Setting up virtual environment for AI-Enhanced Interactive Book Agent..." -ForegroundColor Green

# Check if Python 3.12+ is available
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
        exit 1
    }
    
    # Extract version numbers
    $versionMatch = [regex]::Match($pythonVersion, '(\d+)\.(\d+)')
    if ($versionMatch.Success) {
        $major = [int]$versionMatch.Groups[1].Value
        $minor = [int]$versionMatch.Groups[2].Value
        
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 12)) {
            Write-Host "Error: Python 3.12 or higher is required, but $($major).$($minor) is installed" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "Python version: $($major).$($minor) is compatible" -ForegroundColor Green
    } else {
        Write-Host "Could not parse Python version" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if poetry is installed
$poetryCheck = Get-Command poetry -ErrorAction SilentlyContinue
if (-not $poetryCheck) {
    Write-Host "Installing Poetry..." -ForegroundColor Yellow
    python -m pip install poetry
}

Write-Host "Poetry is available" -ForegroundColor Green

# Check if virtual environment exists, create if not
$venvPath = ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
    Write-Host "Virtual environment created successfully." -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Green
}

# Activate the virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "$venvPath\Scripts\Activate.ps1"

# Upgrade pip
python -m pip install --upgrade pip

# Install project dependencies using Poetry
Write-Host "Installing project dependencies..." -ForegroundColor Yellow
poetry install

Write-Host "Virtual environment setup complete!" -ForegroundColor Green
Write-Host "To activate the virtual environment in the future, run: .venv\Scripts\Activate.ps1" -ForegroundColor Green