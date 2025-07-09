"""
AgeingAnalysis Module for FIT Detector Toolkit

This module provides comprehensive ageing analysis capabilities for FIT detector data,
including data processing, statistical analysis, and interactive visualization.
"""

import logging
import os
import sys
from pathlib import Path

# Module metadata
__version__ = "1.0.0"
__author__ = "FIT Detector Team"
__description__ = "FIT Detector Ageing Analysis Module"

# Set up module logger
logger = logging.getLogger(__name__)

# Module information for the launcher
MODULE_INFO = {
    "name": "AgeingAnalysis",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "category": "Analysis",
    "requires_data": True,
    "supports_batch": True,
    "gui_available": True,
}


def get_module_info():
    """Return module information for the launcher."""
    return MODULE_INFO


def launch_module():
    """Launch the AgeingAnalysis module.
    
    This is the main entry point that will be called by the launcher.
    
    Returns:
        bool: True if launched successfully, False otherwise.
    """
    try:
        logger.info("Launching AgeingAnalysis module...")
        
        # Import the main application
        from .main import AgeingAnalysisApp
        
        # Create and run the application
        app = AgeingAnalysisApp()
        app.run()
        
        logger.info("AgeingAnalysis module launched successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to launch AgeingAnalysis module: {e}")
        return False


def get_module_path():
    """Get the path to this module."""
    return Path(__file__).parent


def is_module_available():
    """Check if the module is available and all dependencies are met."""
    try:
        # Check for required dependencies
        import numpy
        import matplotlib
        import scipy
        import pandas
        
        # Check if old data exists for migration
        old_path = get_module_path().parent / "old"
        if old_path.exists():
            logger.info("Old data directory found - migration available")
        
        return True
        
    except ImportError as e:
        logger.warning(f"AgeingAnalysis module dependencies not met: {e}")
        return False


# Make key classes available at module level
try:
    from .main import AgeingAnalysisApp
    
    __all__ = [
        "AgeingAnalysisApp",
        "launch_module",
        "get_module_info",
        "get_module_path",
        "is_module_available",
        "MODULE_INFO",
    ]
    
except ImportError:
    # If main components aren't available, provide minimal interface
    __all__ = [
        "launch_module",
        "get_module_info", 
        "get_module_path",
        "is_module_available",
        "MODULE_INFO",
    ] 