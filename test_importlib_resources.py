#!/usr/bin/env python3
"""Test script to verify importlib.resources works for grid_visualization_mappings."""

import importlib.resources
import sys


def test_importlib_resources():
    """Test accessing grid_visualization_mappings via importlib.resources."""
    try:
        # Test listing files in the package
        mappings_path = importlib.resources.files(
            "ageing_analysis.grid_visualization_mappings"
        )
        print(f"Package path: {mappings_path}")
        csv_files = list(mappings_path.glob("*.csv"))
        print(f"Found CSV files: {[f.name for f in csv_files]}")

        # Test reading a file
        if csv_files:
            test_file = csv_files[0]
            print(f"Testing reading: {test_file.name}")
            with importlib.resources.open_text(
                "ageing_analysis.grid_visualization_mappings", test_file.name
            ) as f:
                first_line = f.readline().strip()
                print(f"First line: {first_line}")

    except Exception as e:
        print(f"Error: {e}")
        return False

    return True


if __name__ == "__main__":
    print("Testing importlib.resources for grid_visualization_mappings...")
    success = test_importlib_resources()
    if success:
        print("✅ Test passed!")
    else:
        print("❌ Test failed!")
        sys.exit(1)
