#!/bin/bash

# OCEAN Global Installation Script
echo "🌊 Installing OCEAN globally..."

# Get the current directory
OCEAN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create global symlink
echo "📦 Creating global symlink..."
sudo ln -sf "$OCEAN_DIR/ocean" /usr/local/bin/ocean

# Check if successful
if [ $? -eq 0 ]; then
    echo "✅ OCEAN installed globally!"
    echo "🚀 You can now use 'ocean' from anywhere"
    echo ""
    echo "Try:"
    echo "  ocean --help"
    echo "  ocean run"
    echo "  ocean test"
else
    echo "❌ Installation failed"
    exit 1
fi
