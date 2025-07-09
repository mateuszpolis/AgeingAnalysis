#!/usr/bin/env python3
"""
Test script to verify the AgeingAnalysis module works correctly.
"""

import sys
import traceback
from pathlib import Path


def test_imports():
    """Test that the module can be imported correctly."""
    print("Testing imports...")
    try:
        import ageing_analysis
        print("✓ Successfully imported ageing_analysis")
        
        # Test module info
        info = ageing_analysis.get_module_info()
        print(f"✓ Module info: {info['name']} v{info['version']}")
        
        # Test availability check
        available = ageing_analysis.is_module_available()
        print(f"✓ Module available: {available}")
        
        # Test path
        path = ageing_analysis.get_module_path()
        print(f"✓ Module path: {path}")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        traceback.print_exc()
        return False


def test_app_creation():
    """Test that the main application can be created."""
    print("\nTesting application creation...")
    try:
        from ageing_analysis import AgeingAnalysisApp
        
        app = AgeingAnalysisApp()
        print("✓ Successfully created AgeingAnalysisApp instance")
        
        # Test configuration
        config = app.config
        print(f"✓ Configuration loaded: {len(config)} sections")
        
        return True
    except Exception as e:
        print(f"✗ App creation failed: {e}")
        traceback.print_exc()
        return False


def test_launcher_interface():
    """Test the launcher interface."""
    print("\nTesting launcher interface...")
    try:
        import ageing_analysis
        
        # Test launch function exists
        assert hasattr(ageing_analysis, 'launch_module')
        print("✓ launch_module function exists")
        
        # Test get_module_info
        info = ageing_analysis.get_module_info()
        required_keys = ['name', 'version', 'description', 'author', 'category']
        for key in required_keys:
            assert key in info, f"Missing required key: {key}"
        print("✓ Module info contains all required keys")
        
        return True
    except Exception as e:
        print(f"✗ Launcher interface test failed: {e}")
        traceback.print_exc()
        return False


def test_configuration():
    """Test configuration system."""
    print("\nTesting configuration system...")
    try:
        from ageing_analysis.config import load_config, save_config, DEFAULT_CONFIG
        
        # Test default config
        config = load_config()
        print(f"✓ Default configuration loaded: {len(config)} sections")
        
        # Test required sections
        required_sections = ['data_sources', 'analysis', 'visualization', 'export']
        for section in required_sections:
            assert section in config, f"Missing required section: {section}"
        print("✓ All required configuration sections present")
        
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("AgeingAnalysis Module Test Suite")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_app_creation,
        test_launcher_interface,
        test_configuration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Module is ready for use.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 