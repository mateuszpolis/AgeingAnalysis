# AgeingAnalysis Documentation

Welcome to the AgeingAnalysis module documentation! This module provides comprehensive ageing analysis capabilities for FIT detector data.

## Overview

The AgeingAnalysis module is part of the FIT Detector Toolkit and provides:

- **Data Processing**: Import and process FIT detector data
- **Statistical Analysis**: Advanced statistical analysis of ageing patterns
- **Interactive Visualization**: Modern GUI for data exploration
- **Export Capabilities**: Export results in various formats

## Quick Start

### Installation

```bash
pip install ageing-analysis
```

### Basic Usage

```python
from ageing_analysis import AgeingAnalysisApp

# Launch the GUI application
app = AgeingAnalysisApp()
app.run()
```

### Programmatic Usage

```python
import ageing_analysis

# Check if module is available
if ageing_analysis.is_module_available():
    # Launch through the launcher interface
    ageing_analysis.launch_module()
```

## Table of Contents

```{toctree}
:maxdepth: 2
:caption: Contents:

installation
user_guide/index
api/index
development/index
changelog
```

## Features

### Data Sources
- Multiple file format support
- Flexible data import options
- Batch processing capabilities

### Analysis Tools
- Gaussian fitting
- Statistical analysis
- Trend detection
- Reference channel analysis

### Visualization
- Interactive plots
- Real-time data exploration
- Customizable charts
- Export options

### GUI Features
- Modern, intuitive interface
- Cross-platform compatibility
- Keyboard shortcuts
- Comprehensive help system

## Getting Help

- **Documentation**: This documentation covers all aspects of the module
- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/your-org/AgeingAnalysis/issues)
- **Contributing**: See our [Contributing Guide](https://github.com/your-org/AgeingAnalysis/blob/main/CONTRIBUTING.md)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
