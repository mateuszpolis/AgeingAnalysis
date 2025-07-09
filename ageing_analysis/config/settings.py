"""Configuration settings for AgeingAnalysis module."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "data_sources": {
        "input_directory": "data/input",
        "output_directory": "data/output",
        "temp_directory": "data/temp",
        "supported_formats": [".dat", ".txt", ".csv"],
    },
    "analysis": {
        "gaussian_fit": {
            "method": "least_squares",
            "max_iterations": 1000,
            "tolerance": 1e-6,
        },
        "reference_channel": {
            "auto_detect": True,
            "fallback_channels": ["ref_1", "ref_2"],
        },
        "ageing_calculation": {
            "normalization_method": "linear",
            "time_window": "auto",
        },
    },
    "visualization": {
        "default_plot_size": (12, 8),
        "color_scheme": "viridis",
        "show_error_bars": True,
        "interactive_mode": True,
    },
    "export": {
        "default_format": "json",
        "include_metadata": True,
        "compress_output": False,
    },
}


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from file or return default configuration.
    
    Args:
        config_path: Path to configuration file (optional)
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = Path(__file__).parent / "config.json"
    
    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        else:
            logger.info("No configuration file found, using defaults")
            return DEFAULT_CONFIG.copy()
            
    except Exception as e:
        logger.warning(f"Error loading configuration: {e}, using defaults")
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any], config_path: Optional[Path] = None) -> bool:
    """Save configuration to file.
    
    Args:
        config: Configuration dictionary to save
        config_path: Path to save configuration file (optional)
        
    Returns:
        True if successful, False otherwise
    """
    if config_path is None:
        config_path = Path(__file__).parent / "config.json"
    
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {config_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return False 