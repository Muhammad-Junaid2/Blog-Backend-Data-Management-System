#!/usr/bin/env python3
"""
Blog Backend System — Entry Point
Usage:
    python main.py          # Launch GUI
    python main.py --cli    # Launch CLI
    python main.py --seed   # Seed sample data
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from modules.database import init_db


def main():
    init_db()

    if "--seed" in sys.argv:
        from seed import seed
        seed()
        return

    if "--cli" in sys.argv:
        from cli import main as cli_main
        cli_main()
        return

    # Default: GUI
    try:
        from gui import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"GUI unavailable ({e}). Falling back to CLI.")
        from cli import main as cli_main
        cli_main()


if __name__ == "__main__":
    main()
