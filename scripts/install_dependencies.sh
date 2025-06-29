#!/bin/bash
# Multi-Agent TDD System - Dependency Installation Script

set -e  # Exit on any error

echo "============================================================"
echo "Multi-Agent TDD System - Dependency Installation"
echo "============================================================"

# Check if virtual environment is active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "   It's recommended to activate virtual environment first:"
    echo "   source .venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled"
        exit 1
    fi
fi

echo "🐍 Python Environment:"
python --version
echo "📍 Python Path: $(which python)"
echo "📦 Pip Version: $(pip --version)"
echo ""

# Upgrade pip first
echo "📦 Upgrading pip..."
pip install --upgrade pip
echo ""

# Install core dependencies
echo "📦 Installing core dependencies..."
pip install -r requirements.txt
echo ""

# Ask about development dependencies
read -p "Install development dependencies? (Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "Skipping development dependencies"
else
    echo "📦 Installing development dependencies..."
    pip install -r requirements-dev.txt
    echo ""
fi

# Verify installation
echo "🔍 Verifying installation..."
python scripts/verify_dependencies.py

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and configure API keys"
echo "2. Run verification: python scripts/verify_dependencies.py"
echo "3. Start development with Phase 1 implementation"