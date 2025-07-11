# AgeingAnalysis Usage Guide

This guide explains how to use the FIT Detector Ageing Analysis tool both with GUI and in headless mode.

## Installation

First, install the package and its dependencies:

```bash
# Install from source
pip install -e .

# Or install dependencies only
pip install -r requirements.txt
```

## Usage Modes

### 1. GUI Mode (Default)

Run the application with a graphical user interface:

```bash
# Using the launcher script
python run_ageing_analysis.py

# Or using the installed command
ageing-analysis

# Or using the module directly
python -m ageing_analysis.main
```

### 2. Headless Mode

Run the analysis without GUI for automated processing:

```bash
# Basic headless analysis
python run_ageing_analysis.py --headless --config config.json

# With custom output path
python run_ageing_analysis.py --headless --config config.json --output my_results.json

# With verbose logging
python run_ageing_analysis.py --headless --config config.json --verbose
```

## Command Line Arguments

### Required Arguments (Headless Mode)
- `--headless`: Run without GUI
- `--config`, `-c`: Path to configuration file (JSON format)

### Optional Arguments
- `--output`, `-o`: Custom output path for results
- `--verbose`, `-v`: Enable verbose logging
- `--help`, `-h`: Show help message

## Configuration File

The configuration file should be in JSON format and specify the datasets to analyze. It supports both global and dataset-specific base paths for flexible file organization.

### Basic Configuration Structure

```json
{
  "basePath": "/path/to/data/root",
  "inputs": [
    {
      "date": "2024-01-15",
      "validateHeader": false,
      "basePath": "experiment1/run1",
      "files": {
        "PMA0": "data-PMA0.csv",
        "PMA1": "data-PMA1.csv",
        "PMA2": "data-PMA2.csv"
      },
      "refCH": {
        "PM": "PMA0",
        "CH": [0, 1, 2, 3]
      }
    }
  ]
}
```

### Global Base Path

The optional `basePath` field at the root level sets a global base path that is prepended to all dataset paths:

- **Absolute global path**: Used as-is
- **Relative global path**: Resolved relative to the config file location

### Dataset Base Paths

Each dataset can have its own `basePath` field:

- **Relative dataset path**: Combined with global base path (if specified)
- **Absolute dataset path**: Used as-is, ignoring global base path
- **No dataset path**: Uses global base path only

### Path Resolution Examples

1. **Global + Relative Dataset Path**:
   ```json
   {
     "basePath": "/data/experiments",
     "inputs": [
       {
         "date": "2024-01-15",
         "basePath": "run1/session1"
       }
     ]
   }
   ```
   Result: `/data/experiments/run1/session1`

2. **Global + Absolute Dataset Path**:
   ```json
   {
     "basePath": "/data/experiments",
     "inputs": [
       {
         "date": "2024-01-15",
         "basePath": "/special/location/data"
       }
     ]
   }
   ```
   Result: `/special/location/data` (global path ignored)

3. **Global Path Only**:
   ```json
   {
     "basePath": "/data/experiments",
     "inputs": [
       {
         "date": "2024-01-15"
       }
     ]
   }
   ```
   Result: `/data/experiments`

4. **Relative Paths from Config Location**:
   ```json
   {
     "basePath": "data",
     "inputs": [
       {
         "date": "2024-01-15",
         "basePath": "run1"
       }
     ]
   }
   ```
   Result: `<config_directory>/data/run1`

## Examples

### Example 1: GUI Mode
```bash
# Start with GUI
python run_ageing_analysis.py

# Then load configuration file through the GUI
# File -> Load Config...
```

### Example 2: Headless Analysis
```bash
# Run complete analysis in headless mode
python run_ageing_analysis.py --headless --config my_config.json

# Expected output:
# INFO - Starting headless analysis...
# INFO - Parsing data files...
# INFO - Fitting Gaussian distributions...
# INFO - Calculating reference means...
# INFO - Calculating ageing factors...
# INFO - Normalizing ageing factors...
# INFO - Saving results...
#
# ============================================================
# ANALYSIS RESULTS SUMMARY
# ============================================================
# Number of datasets processed: 2
#
# Dataset 1: 2024-01-15
#   Modules: 1
#   Total channels: 48
#   Average ageing factor: 0.9876
#
# Results saved to: /path/to/results_20240115_142030.json
# ============================================================
#
# Analysis completed successfully!
# Results saved to: /path/to/results_20240115_142030.json
```

### Example 3: Custom Output Path
```bash
# Specify custom output location
python run_ageing_analysis.py --headless --config config.json --output final_results.json
```

### Example 4: Verbose Logging
```bash
# Enable detailed logging
python run_ageing_analysis.py --headless --config config.json --verbose
```

## Output Files

The analysis generates the following output files:

1. **Results JSON**: Complete analysis results in JSON format
   - Contains all datasets, modules, channels, and calculated values
   - Default name: `results_YYYYMMDD_HHMMSS.json`

2. **Log Files**: Detailed execution logs
   - Automatic logging to console
   - Use `--verbose` for detailed information

## Error Handling

### Common Issues

1. **Missing Configuration File**
   ```bash
   Error: --config is required when running in headless mode
   ```
   **Solution**: Provide a valid configuration file with `--config`

2. **Invalid Configuration**
   ```bash
   Error: Failed to load configuration: [Errno 2] No such file or directory
   ```
   **Solution**: Check that the configuration file path is correct

3. **Missing Dependencies**
   ```bash
   Error: Could not import AgeingAnalysis module
   ```
   **Solution**: Install dependencies with `pip install -r requirements.txt`

### Troubleshooting

1. **Enable Verbose Logging**
   ```bash
   python run_ageing_analysis.py --headless --config config.json --verbose
   ```

2. **Check Configuration File**
   ```bash
   # Validate JSON format
   python -c "import json; print(json.load(open('config.json')))"
   ```

3. **Test with GUI First**
   ```bash
   # Run with GUI to verify configuration
   python run_ageing_analysis.py
   ```

## Integration with Scripts

### Bash Script Example
```bash
#!/bin/bash
# run_analysis.sh

CONFIG_FILE="config.json"
OUTPUT_DIR="results"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run analysis
python run_ageing_analysis.py \
    --headless \
    --config "$CONFIG_FILE" \
    --output "$OUTPUT_DIR/analysis_$(date +%Y%m%d_%H%M%S).json" \
    --verbose

echo "Analysis completed!"
```

### Python Script Example
```python
#!/usr/bin/env python3
# automated_analysis.py

import subprocess
import sys
from pathlib import Path

def run_analysis(config_path, output_path=None):
    """Run ageing analysis programmatically."""
    cmd = [
        sys.executable, "run_ageing_analysis.py",
        "--headless",
        "--config", str(config_path)
    ]

    if output_path:
        cmd.extend(["--output", str(output_path)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("Analysis completed successfully!")
            print(result.stdout)
        else:
            print(f"Analysis failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error running analysis: {e}")
        return False

    return True

if __name__ == "__main__":
    config_file = Path("config.json")
    output_file = Path("results.json")

    success = run_analysis(config_file, output_file)
    sys.exit(0 if success else 1)
```

## Performance Considerations

- **Memory Usage**: Large datasets may require significant memory
- **Processing Time**: Analysis time depends on dataset size and complexity
- **Disk Space**: Ensure sufficient space for output files

## Support

For issues or questions:
1. Check the verbose logs for detailed error information
2. Verify configuration file format
3. Ensure all dependencies are installed
4. Test with GUI mode first to validate setup
