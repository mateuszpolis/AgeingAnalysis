# AgeingAnalysis Module

A comprehensive FIT detector data analysis tool for calculating and visualizing ageing factors.

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

## Goals

AgeingAnalysis helps detector experts and analysts to:
- Quantify detector ageing by computing per-channel ageing factors over time
- Compare modules and reference channels with robust normalization
- Inspect data quality and trends through interactive visualization
- Automate batch processing for large datasets and reproducible studies
- Integrate into a launcher/GUI ecosystem and support a headless workflow

## Installation

As a submodule in the FIT Detector Toolkit:

```bash
# Clone as submodule
git submodule add <repository-url> modules/ageing-analysis

# Install dependencies
pip install -r modules/ageing-analysis/requirements.txt
```

## DA_batch_client Requirement

**Important**: The AgeingAnalysis module includes integration with the DA_batch_client for retrieving data from the DARMA API. However, the DA_batch_client is a private component that cannot be shared publicly due to licensing restrictions.

### To use the DARMA API functionality:

1. **Request Access**: Contact the development team to request access to the DA_batch_client component
2. **Installation**: Once you have access, the DA_batch_client will be provided separately
3. **Placement**: Place the DA_batch_client files in the `ageing_analysis/utils/da_batch_client/` directory
4. **Dependencies**: Ensure you have the `requests` library installed (`pip install requests>=2.28.0`)

### Without DA_batch_client:

The module will still function for local data analysis, but the DARMA API integration features will not be available. All other functionality (data parsing, analysis, visualization) remains fully operational.

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
- Extended docs (Sphinx, if used): see `docs/`

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

If any of the goals or documentation structure above need adjustments, tell us what you're aiming to achieve and we will refine the docs accordingly.
