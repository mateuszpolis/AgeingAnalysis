# Migration Guide: Old Code to New Module Structure

This guide explains how to migrate the existing code from the `/old` directory to the new `ageing_analysis` module structure.

## Overview

The old code has been analyzed and a new module structure has been created. This guide provides a roadmap for migrating the functionality.

## Code Analysis Summary

### Old Structure:
```
old/
├── ageing_analysis.py          # Main analysis entry point
├── ageing_plot.py              # Plotting functionality
├── ageing_visualization.py     # Basic visualization
├── ageing_visualization_tkinter.py  # Tkinter visualization
└── ageing/                     # Core module
    ├── __init__.py            # Module launcher
    ├── entities/              # Data entities
    ├── services/              # Analysis services
    └── gui/                   # GUI components
```

### New Structure:
```
ageing_analysis/
├── __init__.py                # Module interface
├── main.py                    # Entry point
├── config/                    # Configuration
├── services/                  # Analysis services
├── gui/                       # GUI components
└── utils/                     # Utility functions
```

## Migration Steps

### 1. Services Migration

**Files to migrate:**
- `old/ageing/services/data_parser.py` → `ageing_analysis/services/data_parser.py`
- `old/ageing/services/gaussian_fit.py` → `ageing_analysis/services/gaussian_fit.py`
- `old/ageing/services/reference_channel.py` → `ageing_analysis/services/reference_channel.py`
- `old/ageing/services/ageing_calculator.py` → `ageing_analysis/services/ageing_calculator.py`
- `old/ageing/services/data_normalizer.py` → `ageing_analysis/services/data_normalizer.py`

**Required changes:**
- Update import statements to use new module structure
- Adjust logging configuration
- Update configuration access

### 2. GUI Components Migration

**Files to migrate:**
- Components referenced in `old/ageing_analysis.py` (FITAgeingAnalysisApp, ProgressWindow)
- Plotting functionality from `old/ageing_plot.py`
- Visualization from `old/ageing_visualization_tkinter.py`

**Target location:** `ageing_analysis/gui/`

**Required changes:**
- Integrate with new main application class
- Update imports and dependencies
- Ensure compatibility with launcher interface

### 3. Configuration Migration

**Files to migrate:**
- Configuration logic from `old/ageing/entities/config.py`
- Logger configuration from referenced `configs/logger_config.py`

**Target location:** `ageing_analysis/config/`

**Required changes:**
- Use new configuration system
- Update file paths and structure

### 4. Utility Functions Migration

**Files to migrate:**
- Save results functionality from `utils/save_results.py`
- Any other utility functions

**Target location:** `ageing_analysis/utils/`

### 5. Main Application Integration

**Files to migrate:**
- Core logic from `old/ageing_analysis.py`
- Entry point logic from `old/ageing/__init__.py`

**Target location:** `ageing_analysis/main.py`

**Required changes:**
- Integrate with new AgeingAnalysisApp class
- Update launcher compatibility
- Ensure proper error handling

## Implementation Priority

1. **High Priority:**
   - Services migration (core analysis functionality)
   - Configuration system
   - Basic GUI integration

2. **Medium Priority:**
   - Advanced plotting features
   - Progress tracking
   - Export functionality

3. **Low Priority:**
   - Advanced visualization features
   - Optimization and performance improvements

## Testing Strategy

1. **Unit Tests:** Create tests for each migrated service
2. **Integration Tests:** Test the complete analysis pipeline
3. **GUI Tests:** Verify GUI functionality and launcher integration
4. **Compatibility Tests:** Ensure the module works as a submodule

## Notes

- The module structure is designed to be launcher-compatible
- All dependencies are documented in `requirements.txt`
- Configuration is centralized in the `config/` directory
- The module provides both standalone and integrated operation modes

## Migration Checklist

- [ ] Migrate data parser service
- [ ] Migrate Gaussian fit service
- [ ] Migrate reference channel service
- [ ] Migrate ageing calculator service
- [ ] Migrate data normalizer service
- [ ] Create GUI components
- [ ] Implement plotting functionality
- [ ] Add configuration system
- [ ] Create utility functions
- [ ] Update main application
- [ ] Test standalone operation
- [ ] Test launcher integration
- [ ] Write unit tests
- [ ] Update documentation
