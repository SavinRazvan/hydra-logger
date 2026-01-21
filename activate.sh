#!/bin/bash
# Quick activation script for hydra-logger environment

if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Run: ./setup_env.sh first"
    exit 1
fi

source .venv/bin/activate
echo "✅ Virtual environment activated"
echo "   Python: $(which python)"
echo "   Version: $(python --version)"
echo ""
echo "Run examples with: python examples/01_format_control.py"
