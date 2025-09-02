#!/usr/bin/env python3

"""
OCEAN Entrypoint Script
This script is called by the global ocean-cli script.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Import and run the entrypoint
from ocean.cli import entrypoint

if __name__ == "__main__":
    entrypoint()
