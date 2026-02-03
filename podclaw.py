#!/usr/bin/env python3
"""
PodClaw CLI entry point.

Usage:
    python podclaw.py generate "Topic here"
    python podclaw.py generate --voices roger,george --duration 2m "Topic"
    python podclaw.py voices
    python podclaw.py formats
"""

from podclaw.cli import main

if __name__ == "__main__":
    main()
