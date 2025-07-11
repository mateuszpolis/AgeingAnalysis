"""
Unit tests for basic module functionality.
"""


import ageing_analysis


class TestModuleBasics:
    """Test basic module functionality."""

    def test_module_has_version(self):
        """Test that module has a version attribute."""
        assert hasattr(ageing_analysis, "__version__")
        assert isinstance(ageing_analysis.__version__, str)
        assert ageing_analysis.__version__ != ""

    def test_module_info_structure(self):
        """Test that module info has the correct structure."""
        info = ageing_analysis.get_module_info()

        required_keys = ["name", "version", "description", "author", "category"]
        for key in required_keys:
            assert key in info, f"Missing required key: {key}"

        assert info["name"] == "AgeingAnalysis"
        assert info["version"] == ageing_analysis.__version__
        assert isinstance(info["description"], str)
        assert isinstance(info["author"], str)
        assert info["category"] == "Scientific Analysis"

    def test_module_path(self):
        """Test that module path is correct."""
        import pathlib

        path = pathlib.Path(ageing_analysis.__file__).parent
        assert path.exists()
        assert path.is_dir()
        assert (path / "__init__.py").exists()

    def test_module_availability(self):
        """Test module availability check."""
        # Should be available in test environment
        assert ageing_analysis.is_module_available() is True


class TestModuleImports:
    """Test module imports."""

    def test_can_import_main_app(self):
        """Test that main app can be imported."""
        from ageing_analysis import AgeingAnalysisApp

        assert AgeingAnalysisApp is not None

    def test_all_exports_importable(self):
        """Test that all items in __all__ can be imported."""
        for item_name in ageing_analysis.__all__:
            assert hasattr(ageing_analysis, item_name)
            item = getattr(ageing_analysis, item_name)
            assert item is not None
