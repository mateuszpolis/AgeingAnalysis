"""
Integration tests for the main application.
"""

import pytest

from ageing_analysis import AgeingAnalysisApp


@pytest.mark.integration
class TestAppIntegration:
    """Test application integration."""

    def test_app_creation(self, mock_config):
        """Test that app can be created successfully."""
        app = AgeingAnalysisApp()
        assert app is not None
        assert hasattr(app, "config")

    def test_app_has_required_components(self):
        """Test that app has all required components."""
        app = AgeingAnalysisApp()

        # Check that app has required attributes
        required_attrs = ["config"]
        for attr in required_attrs:
            assert hasattr(app, attr), f"App missing required attribute: {attr}"

    @pytest.mark.slow
    def test_launcher_integration(self):
        """Test the launcher integration."""
        import ageing_analysis

        # This should not crash (though GUI won't actually launch in test)
        # We'll mock the GUI creation to avoid actual window creation
        try:
            # Note: In a real scenario, we'd mock the GUI components
            # For now, just test that the function exists and is callable
            assert callable(ageing_analysis.launch_module)
        except Exception as e:
            # Expected in headless environment
            assert "DISPLAY" in str(e) or "Tcl" in str(e) or "GUI" in str(e)
