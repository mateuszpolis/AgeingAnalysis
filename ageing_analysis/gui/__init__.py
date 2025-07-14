"""GUI module for AgeingAnalysis.

This module contains the graphical user interface components for the ageing analysis,
including plotting widgets, progress windows, and the main application interface.
"""

from .config_generator_widget import ConfigGeneratorWidget
from .plotting_widget import AgeingPlotWidget
from .progress_window import ProgressWindow

__all__ = [
    "AgeingPlotWidget",
    "ProgressWindow",
    "ConfigGeneratorWidget",
]
