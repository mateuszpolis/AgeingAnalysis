"""AgeingAnalysis - FIT Detector Ageing Analysis Module.

A comprehensive module for analyzing ageing effects in FIT detector data.
This module provides data processing, statistical analysis, and interactive
visualization.

Features:
- Data parsing and preprocessing from CSV files
- Gaussian fitting and statistical analysis
- Reference channel calculations
- Ageing factor computation and normalization
- Interactive GUI with plotting capabilities
- Results export in JSON and CSV formats

Usage:
    # For GUI application
    from ageing_analysis import AgeingAnalysisApp
    app = AgeingAnalysisApp()
    app.run()

    # For programmatic use
    from ageing_analysis.entities import Config
    from ageing_analysis.services import DataParser, GaussianFitService

    config = Config("config.json")
    parser = DataParser(config.datasets[0])
    parser.process_all_files()
"""

__version__ = "1.0.0"
__author__ = "FIT Detector Team"

# Core imports: entities, main app, services, and utilities
from .entities import Channel, Config, Dataset, Module
from .main import AgeingAnalysisApp
from .services import (
    AgeingCalculationService,
    DataNormalizer,
    DataParser,
    GaussianFitService,
    ReferenceChannelService,
)
from .utils import (
    export_results_csv,
    load_results,
    save_results,
    validate_csv,
    validate_file_identifier,
    validate_path_exists,
)

# GUI components (optional import)
try:
    from .gui import AgeingPlotWidget, ProgressWindow

    _GUI_AVAILABLE = True
except ImportError:
    _GUI_AVAILABLE = False
    AgeingPlotWidget = None  # type: ignore
    ProgressWindow = None  # type: ignore


def get_module_info():
    """Get module information.

    Returns:
        dict: Module information including name, version, description, etc.
    """
    return {
        "name": "AgeingAnalysis",
        "version": __version__,
        "author": __author__,
        "description": "FIT Detector Ageing Analysis Module",
        "category": "Scientific Analysis",
        "features": [
            "Data parsing and preprocessing",
            "Gaussian fitting and statistical analysis",
            "Reference channel calculations",
            "Ageing factor computation and normalization",
            "Interactive visualization and plotting",
            "Results export capabilities",
        ],
        "gui_available": _GUI_AVAILABLE,
    }


def is_module_available():
    """Check if the module is properly installed and available.

    Returns:
        bool: True if module is available and functional.
    """
    try:
        # Test basic functionality
        info = get_module_info()
        return info["name"] == "AgeingAnalysis"
    except Exception:
        return False


# Main exports
__all__ = [
    # Main application
    "AgeingAnalysisApp",
    # Entities
    "Config",
    "Dataset",
    "Module",
    "Channel",
    # Services
    "DataParser",
    "GaussianFitService",
    "ReferenceChannelService",
    "AgeingCalculationService",
    "DataNormalizer",
    # Utilities
    "save_results",
    "load_results",
    "export_results_csv",
    "validate_csv",
    "validate_file_identifier",
    "validate_path_exists",
    # GUI components (if available)
    "AgeingPlotWidget",
    "ProgressWindow",
    # Module info functions
    "get_module_info",
    "is_module_available",
    # Metadata
    "__version__",
    "__author__",
]
