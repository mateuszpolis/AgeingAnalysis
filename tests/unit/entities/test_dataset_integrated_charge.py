"""Tests for Dataset entity integrated charge functionality."""

from unittest.mock import MagicMock, patch

from ageing_analysis.entities.dataset import Dataset


class TestDatasetIntegratedCharge:
    """Test cases for Dataset integrated charge functionality."""

    def test_dataset_constructor_without_integrated_charge(self):
        """Test Dataset constructor without integrated charge."""
        with patch(
            "ageing_analysis.entities.dataset.Dataset._initialize_modules"
        ) as mock_init_modules, patch(
            "ageing_analysis.entities.dataset.Dataset._get_reference_module"
        ) as mock_get_ref_module:
            mock_init_modules.return_value = []
            mock_get_ref_module.return_value = MagicMock()

            dataset = Dataset(
                date="2022-01-01",
                base_path="/path/to/data",
                files={"PMA0": "file.csv"},
                ref_ch={"PM": "PMA0", "CH": [1, 2]},
                validate_header=False,
            )

            assert dataset.date == "2022-01-01"
            assert not hasattr(dataset, "integrated_charge")

    def test_dataset_to_dict_without_integrated_charge(self):
        """Test Dataset to_dict method excludes integrated charge."""
        with patch(
            "ageing_analysis.entities.dataset.Dataset._initialize_modules"
        ) as mock_init_modules, patch(
            "ageing_analysis.entities.dataset.Dataset._get_reference_module"
        ) as mock_get_ref_module:
            mock_init_modules.return_value = []
            mock_get_ref_module.return_value = MagicMock()

            dataset = Dataset(
                date="2022-01-01",
                base_path="/path/to/data",
                files={"PMA0": "file.csv"},
                ref_ch={"PM": "PMA0", "CH": [1, 2]},
                validate_header=False,
            )

            result = dataset.to_dict()

            assert result["date"] == "2022-01-01"
            assert "integratedCharge" not in result
            assert "reference_means" in result
            assert "modules" in result

    def test_dataset_str_without_integrated_charge(self):
        """Test Dataset __str__ method excludes integrated charge."""
        with patch(
            "ageing_analysis.entities.dataset.Dataset._initialize_modules"
        ) as mock_init_modules, patch(
            "ageing_analysis.entities.dataset.Dataset._get_reference_module"
        ) as mock_get_ref_module:
            mock_init_modules.return_value = []
            mock_get_ref_module.return_value = MagicMock()

            dataset = Dataset(
                date="2022-01-01",
                base_path="/path/to/data",
                files={"PMA0": "file.csv"},
                ref_ch={"PM": "PMA0", "CH": [1, 2]},
                validate_header=False,
            )

            result = str(dataset)

            assert "2022-01-01" in result
            assert "integrated_charge=" not in result
