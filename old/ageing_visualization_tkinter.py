#!/usr/bin/env python3
"""
Main entry point for the Tkinter-based Ageing Factors Visualization.

This script launches the Tkinter-based visualization dashboard as a standalone application.
"""

import argparse
import sys
import tkinter as tk
from pathlib import Path

from visualization.tkinter_dashboard import TkinterDashboard


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="FIT Detector Ageing Factors Visualization")
    parser.add_argument("--json", type=str, help="Path to a JSON file containing analysis results")
    return parser.parse_args()


def main():
    """Main entry point for the visualization application."""
    args = parse_arguments()

    # Create a new Tkinter root window
    root = tk.Tk()

    # Create the dashboard
    dashboard = TkinterDashboard(root)

    # If a JSON file is specified, load it
    if args.json:
        json_path = Path(args.json)
        if json_path.exists():
            print(f"Loading data from {json_path}")
            if not dashboard.load_from_json_file(str(json_path)):
                print(f"Error loading JSON file: {json_path}")
                return 1
        else:
            print(f"JSON file not found: {json_path}")
            return 1

    # Start the Tkinter main loop
    dashboard.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
