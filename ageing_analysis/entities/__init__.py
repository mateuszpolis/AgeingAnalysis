"""Entity classes for AgeingAnalysis.

This module contains the core entity classes that represent the data structures
used in the ageing analysis process.
"""

from .channel import Channel
from .config import Config
from .dataset import Dataset
from .module import Module

__all__ = [
    "Channel",
    "Module",
    "Dataset",
    "Config",
]
