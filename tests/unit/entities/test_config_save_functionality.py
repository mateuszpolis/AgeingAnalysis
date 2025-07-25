"""Tests for Config entity save functionality."""

import json
import os
import tempfile
from unittest.mock import patch

from ageing_analysis.entities.config import Config


class TestConfigSaveFunctionality:
    """Test cases for Config save functionality."""

    def create_temp_config(self, config_data):
        """Create a temporary config file with the given data."""
        config_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        json.dump(config_data, config_file)
        config_file.close()
        return config_file.name

    def test_config_save_integrated_charge_direct(self):
        """Test saving integrated charge data to config
        by directly testing the save method."""
        # Create initial config without integrated charge
        config_data = {
            "inputs": [
                {
                    "date": "2022-01-01",
                    "basePath": "/path/to/data",
                    "files": {"PMA0": "file.csv", "PMA1": "file2.csv"},
                    "refCH": {"PM": "PMA0", "CH": [1, 2]},
                    "validateHeader": False,
                }
            ]
        }

        config_path = self.create_temp_config(config_data)

        try:
            # Mock the file existence check and CSV validation
            with patch("os.path.exists", return_value=True), patch(
                "ageing_analysis.entities.module.validate_csv", return_value=True
            ):
                config = Config(config_path)

                # Manually set integrated charge data in the original config
                config.original_config["inputs"][0]["integratedCharge"] = {
                    "PMA0": {"Ch01": 100.5, "Ch02": 200.7},
                    "PMA1": {"Ch01": 150.3, "Ch02": 250.9},
                }

                # Save the configuration
                config.save()

                # Verify the file was updated
                with open(config_path) as f:
                    updated_config = json.load(f)

                # Check that integrated charge data was saved
                assert "integratedCharge" in updated_config["inputs"][0]
                assert (
                    updated_config["inputs"][0]["integratedCharge"]["PMA0"]["Ch01"]
                    == 100.5
                )
                assert (
                    updated_config["inputs"][0]["integratedCharge"]["PMA0"]["Ch02"]
                    == 200.7
                )
                assert (
                    updated_config["inputs"][0]["integratedCharge"]["PMA1"]["Ch01"]
                    == 150.3
                )
                assert (
                    updated_config["inputs"][0]["integratedCharge"]["PMA1"]["Ch02"]
                    == 250.9
                )

        finally:
            # Clean up
            if os.path.exists(config_path):
                os.unlink(config_path)

    def test_config_get_integrated_charge_data_from_original_config(self):
        """Test getting integrated charge data from the original config."""
        config_data = {
            "inputs": [
                {
                    "date": "2022-01-01",
                    "integratedCharge": {
                        "PMA0": {"Ch01": 100.5, "Ch02": 200.7},
                        "PMA1": {"Ch01": 150.3, "Ch02": 250.9},
                    },
                    "basePath": "/path/to/data",
                    "files": {"PMA0": "file.csv", "PMA1": "file2.csv"},
                    "refCH": {"PM": "PMA0", "CH": [1, 2]},
                    "validateHeader": False,
                }
            ]
        }

        config_path = self.create_temp_config(config_data)

        try:
            # Mock the file existence check and CSV validation
            with patch("os.path.exists", return_value=True), patch(
                "ageing_analysis.entities.module.validate_csv", return_value=True
            ):
                config = Config(config_path)

                # Get integrated charge data directly from original config
                charge_data = config.original_config["inputs"][0]["integratedCharge"]

                # Verify the data structure
                assert "PMA0" in charge_data
                assert "PMA1" in charge_data
                assert charge_data["PMA0"]["Ch01"] == 100.5
                assert charge_data["PMA1"]["Ch02"] == 250.9

        finally:
            # Clean up
            if os.path.exists(config_path):
                os.unlink(config_path)

    def test_config_save_without_original_config(self):
        """Test that save fails when no original config is available."""
        # Create a config by loading from a file,
        # then remove the original_config attribute
        config_data = {
            "inputs": [
                {
                    "date": "2022-01-01",
                    "basePath": "/path/to/data",
                    "files": {"PMA0": "file.csv"},
                    "refCH": {"PM": "PMA0", "CH": [1, 2]},
                    "validateHeader": False,
                }
            ]
        }

        config_path = self.create_temp_config(config_data)

        try:
            # Mock the file existence check and CSV validation
            with patch("os.path.exists", return_value=True), patch(
                "ageing_analysis.entities.module.validate_csv", return_value=True
            ):
                config = Config(config_path)

                # Remove the original_config attribute to simulate the error condition
                delattr(config, "original_config")

                # Should raise ValueError when trying to save without original config
                try:
                    config.save()
                    raise AssertionError("Expected ValueError to be raised")
                except ValueError as e:
                    assert "No original config data available" in str(e)

        finally:
            # Clean up
            if os.path.exists(config_path):
                os.unlink(config_path)

    def test_config_save_without_config_path(self):
        """Test that save fails when no config path is specified."""
        # Create a config by loading from a file, then remove the config_path
        config_data = {
            "inputs": [
                {
                    "date": "2022-01-01",
                    "basePath": "/path/to/data",
                    "files": {"PMA0": "file.csv"},
                    "refCH": {"PM": "PMA0", "CH": [1, 2]},
                    "validateHeader": False,
                }
            ]
        }

        config_path = self.create_temp_config(config_data)

        try:
            # Mock the file existence check and CSV validation
            with patch("os.path.exists", return_value=True), patch(
                "ageing_analysis.entities.module.validate_csv", return_value=True
            ):
                config = Config(config_path)

                # Remove the config_path to simulate the error condition
                config.config_path = None

                # Should raise ValueError when trying to save without config path
                try:
                    config.save()
                    raise AssertionError("Expected ValueError to be raised")
                except ValueError as e:
                    assert "No config path specified" in str(e)

        finally:
            # Clean up
            if os.path.exists(config_path):
                os.unlink(config_path)
