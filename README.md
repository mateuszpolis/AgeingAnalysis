# AgeingAnalysis Module

A comprehensive FIT detector data analysis tool for calculating and visualizing ageing factors.

## Problem

In FT0, each PMT (photomultiplier tube) channel's gain changes over time due to ageing effects (mainly photocathode degradation and dynode wear from accumulated charge). To keep the detector response uniform and stable, we need to determine a relative ageing factor for each channel.

That factor is then used to recalibrate gain settings and discriminator thresholds, so that differences in channel sensitivity don't bias the physics measurements (e.g., trigger efficiency, timing resolution, amplitude calibration).

## Goals

AgeingAnalysis helps to:
- Quantify detector ageing by computing per-channel relative ageing factors over time
- Compare modules and reference channels with robust normalization
- Inspect data quality and trends through interactive visualization
- Automate batch processing for large datasets and reproducible studies
- Integrate into a launcher/GUI ecosystem while also supporting a headless workflow

## Why this tool

- Automatic end-to-end calculations with a built-in analysis module
- Grid visualizations for quick spatial insights across channels/modules
- Minimal user setup: provide only
  - configuration loads (control server logs)
  - configuration files (.cfg)
  and the program performs the full analysis

## Overview

The AgeingAnalysis module provides a complete pipeline for processing FIT detector data, including:
- Data parsing and preprocessing
- Gaussian fitting and statistical analysis
- Reference channel calculations
- Ageing factor computation and normalization
- Interactive visualization and plotting

## Features

- **Data Analysis Pipeline**: Multi-stage processing of FIT detector data
- **Interactive Visualization**: Tkinter-based GUI with matplotlib plotting
- **Headless Mode**: Command-line interface for automated processing without GUI
- **Flexible Configuration**: Global and dataset-specific base paths for easy data management
- **Service Architecture**: Modular design with separate services for different analysis stages
- **Progress Tracking**: Real-time progress updates during analysis
- **Export Capabilities**: Save results in various formats

## Installation

As a submodule in the FIT Detector Toolkit:

```bash
# Clone as submodule
git submodule add <repository-url> modules/ageing-analysis

# Install dependencies
pip install -r modules/ageing-analysis/requirements.txt
```

## Usage

### As a Standalone Application

```python
from ageing_analysis import AgeingAnalysisApp

# Launch the application
app = AgeingAnalysisApp()
app.run()
```

### As a Module in the Launcher

```python
from ageing_analysis import launch_module

# Launch from the main launcher
launch_module()
```

## Documentation

- [Usage Guide](USAGE.md): GUI, headless mode, configuration format, and examples
- [Configuration Generator](USAGE.md#configuration-generator-gui): GUI-integrated tool for building configs
- [Contributing & Releases](CONTRIBUTING.md): commit style, tests, and release automation
- API and internals: browse the `ageing_analysis/` package for services, GUI, and utils
- Tests: see `tests/` for unit and integration coverage

## Module Structure

```
ageing_analysis/
├── __init__.py          # Main module interface
├── main.py              # Entry point
├── services/            # Analysis services
├── gui/                 # GUI components
├── utils/               # Utility functions
└── config/              # Configuration files
```

## Dependencies

- Python 3.8+
- numpy>=1.21.0
- matplotlib>=3.5.0
- scipy>=1.7.0
- pandas>=1.3.0
- tkinter (built-in)

## Configuration

The module uses configuration files for:
- Data source paths
- Analysis parameters
- Visualization settings
- Export options

## Contributing

This module is part of the FIT Detector Toolkit project. Please follow the project's contributing guidelines.
