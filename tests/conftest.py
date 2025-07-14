"""Pytest configuration and fixtures for AgeingAnalysis tests."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_data_file(temp_dir: Path) -> Path:
    """Create a sample data file for testing."""
    data_file = temp_dir / "sample_data.txt"
    data_file.write_text(
        """# Sample data for testing
1.0 0.5 100
2.0 0.7 150
3.0 0.9 200
4.0 1.1 250
5.0 1.3 300
"""
    )
    return data_file


@pytest.fixture
def mock_config(temp_dir: Path):
    """Provide a mock configuration for testing."""
    return {
        "data_sources": {
            "default_path": str(temp_dir / "test_data"),
            "file_patterns": ["*.txt", "*.csv"],
        },
        "analysis": {
            "default_bins": 100,
            "fit_method": "gaussian",
        },
        "visualization": {
            "dpi": 100,
            "figure_size": [8, 6],
        },
        "export": {
            "default_format": "png",
            "quality": 95,
        },
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Ensure we're in test mode
    os.environ["AGEING_ANALYSIS_TEST_MODE"] = "1"
    yield
    # Clean up
    if "AGEING_ANALYSIS_TEST_MODE" in os.environ:
        del os.environ["AGEING_ANALYSIS_TEST_MODE"]


@pytest.fixture
def gui_available():
    """Check if GUI testing is available."""
    try:
        import tkinter

        # Test if display is available
        root = tkinter.Tk()
        root.withdraw()
        root.destroy()
        return True
    except (ImportError, tkinter.TclError):
        return False
