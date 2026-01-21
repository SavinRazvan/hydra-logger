#!/bin/bash
# Setup script for hydra-logger development environment
# This script creates a virtual environment and installs all dependencies

set -e  # Exit on error

echo "=========================================="
echo "Hydra-Logger Environment Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python 3.11+ required. Found: $PYTHON_VERSION"
    echo "   Please install Python 3.11 or higher"
    exit 1
fi

echo "✅ Python version: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel --quiet

# Install package in development mode
echo "Installing hydra-logger in development mode..."
pip install -e . --quiet

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "To activate the environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run examples:"
echo "  python examples/01_format_control.py"
echo "  python examples/run_all_examples.py"
echo ""
echo "To deactivate:"
echo "  deactivate"
echo ""
