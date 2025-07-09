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