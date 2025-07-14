# Configuration Generator Usage Guide

## Overview

The Configuration Generator is a graphical tool for creating configuration files for the FIT Detector Ageing Analysis. It provides an intuitive interface for selecting input folders and files, automatically optimizing base paths to avoid repetition. **The Config Generator is now easily accessible from the main GUI interface.**

## Features

### 🎯 **Core Functionality**
- **Graphical Interface**: Easy-to-use GUI for config creation
- **Main GUI Integration**: Accessible via button in the main application
- **Automatic Path Optimization**: Determines optimal base paths to minimize repetition
- **PM Identifier Detection**: Automatically extracts PM identifiers from filenames
- **Reference Channel Selection**: Smart defaults with manual override options
- **Configuration Preview**: Live preview of generated configuration
- **Import/Export**: Load and save configuration files

### 🔧 **Technical Details**
- **Service-GUI Separation**: Clean separation between business logic (`ConfigManager`) and UI (`ConfigGeneratorWidget`)
- **Path Management**: Intelligent handling of absolute/relative paths
- **Validation**: Comprehensive validation of files and paths
- **Error Handling**: User-friendly error messages and logging

## Architecture

```
ageing_analysis/
├── services/
│   └── config_manager.py      # Business logic for config generation
├── gui/
│   └── config_generator_widget.py  # GUI interface
└── main.py                    # Main GUI integration
```

## Usage

### 1. Via Main GUI Interface (Recommended)

**From the Main Application:**
1. Launch the main ageing analysis application:
   ```bash
   python -m ageing_analysis.main
   ```
2. Click the **"Config Generator"** button in the Configuration section
3. Or use the menu: **File → Config Generator...**

**Benefits:**
- Seamless integration with main workflow
- Modal window for focused configuration creation
- Automatic path detection based on project structure
- Easy return to main interface after config creation

### 2. Standalone Usage

For development or testing purposes:

```python
import tkinter as tk
from ageing_analysis.gui.config_generator_widget import ConfigGeneratorWidget

# Create main window
root = tk.Tk()
root.title("Config Generator")

# Create config generator widget
config_widget = ConfigGeneratorWidget(root, root_path="/path/to/project")

# Run the application
root.mainloop()
```

### 3. Using the Config Generator

#### Step 1: Add Input Groups
1. Click **"Add Input Group"**
2. Select a folder containing CSV files
3. Select up to 20 CSV files with PM identifiers (e.g., `PMA0`, `PMC9`)
4. Choose a reference PM when prompted (defaults to `PMC9` if available)

#### Step 2: Manage Groups
- **Remove Selected**: Remove a selected input group
- **Clear All**: Remove all input groups
- View groups in the list with format: `Date - File Count - Reference PM`

#### Step 3: Generate Configuration
- **Preview Config**: See the generated JSON configuration
- **Save Config**: Export configuration to a JSON file
- **Load Config**: Import an existing configuration

### 4. Service-Only Usage

For programmatic usage:

```python
from ageing_analysis.services.config_manager import ConfigManager

# Initialize config manager
config_manager = ConfigManager(root_path="/path/to/project")

# Add input group
success, message = config_manager.add_input_group(
    folder_path="/path/to/data/folder",
    file_paths=["/path/to/file1.csv", "/path/to/file2.csv"],
    reference_pm="PMC9"
)

# Generate configuration
config = config_manager.generate_config()

# Save configuration
success, path = config_manager.save_config("/path/to/config.json")
```

## Configuration Structure

### Generated Configuration Format

```json
{
    "basePath": "/Users/user/Documents/Data",
    "inputs": [
        {
            "date": "2022-09-19",
            "validateHeader": false,
            "basePath": "0T/2022-09-19-laser",
            "files": {
                "PMA0": "2022-09-19-0T-charge-PMA0.csv",
                "PMC9": "2022-09-19-0T-charge-PMC9.csv"
            },
            "refCH": {
                "PM": "PMC9",
                "CH": [5, 7, 8]
            }
        }
    ]
}
```

### Path Optimization Logic

1. **Global Base Path**: Common path shared by all input folders
2. **Relative Paths**: Input paths made relative to global base path
3. **Fallback**: If no common path exists, uses first input's parent directory
4. **Cross-Drive Handling**: Keeps absolute paths when on different drives
5. **Path Preservation**: When loading existing configs, original paths are preserved when adding new groups

#### Smart Path Preservation

The Config Generator includes intelligent path preservation when modifying existing configurations:

- **Scenario 1 - New input fits**: If a new input group can fit within the existing global base path structure, all paths remain relative and the structure is preserved
- **Scenario 2 - New input outside**: If a new input group is outside the existing structure, the original global base path and relative paths are preserved, while the new input uses an absolute path

This ensures that when you load an existing configuration and add new input groups, the original folder structure remains intact and functional.

## GUI Integration Details

### Main Interface Integration

The Config Generator is integrated into the main GUI interface in two ways:

1. **Configuration Section Button**: Located next to the "Load Configuration File" button
2. **File Menu**: Accessible via "File → Config Generator..."

### Modal Window Behavior

- Opens as a modal window (stays on top of main window)
- Properly centered on screen
- Maintains focus until closed
- Returns control to main application when closed

### Integration Benefits

- **Seamless Workflow**: Generate configs directly from main interface
- **Context Awareness**: Automatically uses project root path
- **Consistent UI**: Matches main application styling and behavior
- **Error Integration**: Errors are logged to main application logger

## File Requirements

### File Naming Convention
- Files must be CSV format (`.csv` extension)
- Must contain PM identifier: `PM[AC][0-9]` (e.g., `PMA0`, `PMC9`)
- Example: `2022-09-19-0T-charge-PMA0.csv`

### Folder Structure
- Date must be present in folder path: `YYYY-MM-DD` format
- Example: `/path/to/data/2022-09-19-laser/`

### Limits
- Maximum 20 files per input group
- Supports both PMA and PMC modules
- Automatic reference channel configuration

## Reference Channel Logic

1. **User Selection**: If user specifies a reference PM, it's used
2. **PMC9 Default**: If PMC9 is available, it's used as default
3. **First Available**: Otherwise, uses the first available PM
4. **Channels**: Always uses channels `[5, 7, 8]` for reference

## Error Handling

### Common Errors
- **Invalid Path**: Folder or file doesn't exist
- **Invalid Date**: Folder path doesn't contain valid date
- **Invalid PM**: File doesn't contain valid PM identifier
- **Too Many Files**: More than 20 files selected
- **Invalid File Type**: Non-CSV files selected

### Error Messages
- User-friendly messages in GUI
- Detailed logging for debugging
- Status log in the interface
- Integration with main application error handling

## Logging

The config generator includes comprehensive logging:
- **Info**: Successful operations
- **Warning**: Non-critical issues
- **Error**: Failed operations
- **Debug**: Detailed operation info
- **Integration**: Main GUI integration events

## Best Practices

### 1. File Organization
- Keep related files in dated folders
- Use consistent naming conventions
- Group files by measurement date

### 2. Path Management
- Use consistent folder structures
- Avoid special characters in paths
- Consider using relative paths for portability

### 3. Configuration Management
- Save configurations with descriptive names
- Keep backups of important configurations
- Use version control for configuration files

### 4. Validation
- Always preview configurations before saving
- Validate file paths exist before processing
- Check for missing PM identifiers

### 5. Main GUI Integration
- Use the main GUI button for normal workflow
- Generate configs before starting analysis
- Load generated configs directly in main interface

## Troubleshooting

### Common Issues

1. **"No PM identifier found"**
   - Check filename contains `PM[AC][0-9]` pattern
   - Ensure correct file naming convention

2. **"No valid date found"**
   - Folder path must contain `YYYY-MM-DD` format
   - Check folder structure and naming

3. **"Path optimization failed"**
   - Ensure all paths are accessible
   - Check for permission issues
   - Verify paths exist on same drive

4. **"Configuration not loading"**
   - Check JSON file structure
   - Verify file paths still exist
   - Ensure proper JSON formatting

5. **"Config generator won't open"**
   - Check GUI dependencies are installed
   - Verify main application is running
   - Check application logs for errors

6. **"Original paths changed after adding new group"**
   - This is resolved in the current version with smart path preservation
   - Original paths from loaded configs are now preserved automatically
   - New inputs outside existing structure use absolute paths

### Getting Help

1. Check the status log in the GUI
2. Review error messages for specific issues
3. Verify file and folder permissions
4. Ensure consistent naming conventions
5. Check main application logs for integration issues

## Future Enhancements

- **Batch Processing**: Process multiple configurations at once
- **Template Support**: Save and load configuration templates
- **Validation Rules**: Customizable validation rules
- **Export Formats**: Support for additional export formats
- **Direct Analysis**: Generate config and start analysis in one step
- **Recent Configs**: Quick access to recently used configurations

## API Reference

### Main GUI Integration

```python
# In main.py
def _open_config_generator(self):
    """Open the configuration generator in a new window."""
    # Creates modal window with ConfigGeneratorWidget
    # Handles window lifecycle and error reporting
```

### ConfigGeneratorWidget

```python
# Main widget class
class ConfigGeneratorWidget:
    def __init__(self, parent, root_path=None)
    def get_frame(self) -> ttk.Frame

    # Core functionality
    def _add_input_group(self)
    def _save_config(self)
    def _load_config(self)
    def _preview_config(self)
```

### ConfigManager Service

```python
# Service class
class ConfigManager:
    def __init__(self, root_path=None)
    def add_input_group(self, folder_path, file_paths, reference_pm=None)
    def generate_config(self) -> Dict
    def save_config(self, file_path=None) -> Tuple[bool, str]
    def load_config(self, file_path) -> Tuple[bool, str]
```
