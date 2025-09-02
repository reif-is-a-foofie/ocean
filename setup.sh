#!/bin/bash

# OCEAN Setup Script
echo "🌊 Setting up OCEAN..."

# Check if Python 3.11+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+ first."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install package
echo "📥 Installing OCEAN package..."
pip install -e .

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌊 To get started:"
echo "  1. Activate environment: source venv/bin/activate"
echo "  2. Run tests: ocean test"
echo "  3. Start application: ocean run"
echo "  4. View UI: http://127.0.0.1:8000/ui"
echo ""
echo "💡 Optional: Run './install-global.sh' to install globally"
