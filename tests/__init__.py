"""
Tests package for AgeingAnalysis module.

This package contains unit tests, integration tests, and GUI tests
for all components of the AgeingAnalysis module.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path so we can import ageing_analysis
test_dir = Path(__file__).parent
project_root = test_dir.parent
sys.path.insert(0, str(project_root)) 