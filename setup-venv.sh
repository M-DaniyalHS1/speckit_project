#!/bin/bash
# setup-venv.sh - Script to set up the virtual environment for the AI-Enhanced Interactive Book Agent

set -e  # Exit on any error

echo "Setting up virtual environment for AI-Enhanced Interactive Book Agent..."

# Check if Python 3.12+ is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not in PATH"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MIN_VERSION="3.12"

if [[ "$(printf '%s\n' "$MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$MIN_VERSION" ]]; then
    echo "Error: Python 3.12 or higher is required, but $PYTHON_VERSION is installed"
    exit 1
fi

echo "Python version: $PYTHON_VERSION is compatible"

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    # Add Poetry to PATH for this session
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "Poetry version: $(poetry --version)"

# Check if virtual environment exists, create if not
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "Virtual environment created successfully."
else
    echo "Virtual environment already exists."
fi

# Activate the virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install project dependencies using Poetry
echo "Installing project dependencies..."
poetry install

echo "Virtual environment setup complete!"
echo "To activate the virtual environment in the future, run: source .venv/bin/activate"
echo "Then navigate to your project directory and run: poetry install"