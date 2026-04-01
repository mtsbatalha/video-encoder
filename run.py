#!/usr/bin/env python3
"""
Video Encoder CLI Wrapper
=========================

This is a convenience wrapper to run the video-encoder CLI.
It can be executed directly from the project root directory.

Usage:
    python3 run.py [options]
    python3 run.py --interactive
    python3 run.py --help

Alternative execution methods:
    python3 -m src [options]
    python3 -m src.cli [options]
"""

import sys
from pathlib import Path

# Add the project root to Python path to enable imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the main CLI function
from src.cli import main

if __name__ == '__main__':
    main()
