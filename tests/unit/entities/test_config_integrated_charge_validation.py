"""Tests for integrated charge validation in Config entity."""

import json

from ageing_analysis.entities.config import Config


class TestConfigIntegratedChargeValidation:
    """Test integrated charge validation in Config entity."""

    def test_config_with_valid_integrated_charge(self, tmp_path):
        """Test config loading with valid integrated charge data."""
        config_data = {
            "inputs": [
                {
                    "date": "2022-01-01",
                    "basePath": str(tmp_path),
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [1, 2]},
                    "integratedCharge": {
                        "PMA0": {
                            "Ch01": 1.0,
                            "Ch02": 2.0,
                            "Ch03": 3.0,
                            "Ch04": 4.0,
                            "Ch05": 5.0,
                            "Ch06": 6.0,
                            "Ch07": 7.0,
                            "Ch08": 8.0,
                            "Ch09": 9.0,
                            "Ch10": 10.0,
                            "Ch11": 11.0,
                            "Ch12": 12.0,
                        }
                    },
                }
            ]
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create a dummy CSV file
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("header1,header2\nvalue1,value2")

        config = Config(str(config_file))
        assert len(config.datasets) == 1
        assert len(config.datasets[0].modules) == 1
        # Check that the module has integrated charge data
        module = config.datasets[0].modules[0]
        assert hasattr(module, "integrated_charge_data")
        assert module.integrated_charge_data is not None
        assert "PMA0" in module.integrated_charge_data

    def test_config_with_invalid_integrated_charge_not_dict(self, tmp_path):
        """Test config loading with invalid integrated charge data (not dict)."""
        config_data = {
            "inputs": [
                {
                    "date": "2022-01-01",
                    "basePath": str(tmp_path),
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [1, 2]},
                    "integratedCharge": "invalid_data",
                }
            ]
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create a dummy CSV file
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("header1,header2\nvalue1,value2")

        config = Config(str(config_file))
        assert len(config.datasets) == 1
        assert len(config.datasets[0].modules) == 1
        # Check that the module has no integrated charge data
        module = config.datasets[0].modules[0]
        assert hasattr(module, "integrated_charge_data")
        assert module.integrated_charge_data is None

    def test_config_with_invalid_pm_name(self, tmp_path):
        """Test config loading with invalid PM name in integrated charge data."""
        config_data = {
            "inputs": [
                {
                    "date": "2022-01-01",
                    "basePath": str(tmp_path),
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [1, 2]},
                    "integratedCharge": {
                        "INVALID_PM": {
                            "Ch01": 1.0,
                            "Ch02": 2.0,
                        }
                    },
                }
            ]
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create a dummy CSV file
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("header1,header2\nvalue1,value2")

        config = Config(str(config_file))
        assert len(config.datasets) == 1
        assert len(config.datasets[0].modules) == 1
        # Check that the module has no integrated charge data
        module = config.datasets[0].modules[0]
        assert hasattr(module, "integrated_charge_data")
        assert module.integrated_charge_data is None

    def test_config_with_invalid_channel_name(self, tmp_path):
        """Test config loading with invalid channel name in integrated charge data."""
        config_data = {
            "inputs": [
                {
                    "date": "2022-01-01",
                    "basePath": str(tmp_path),
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [1, 2]},
                    "integratedCharge": {
                        "PMA0": {
                            "Ch00": 1.0,  # Invalid: should be Ch01-Ch12
                            "Ch13": 2.0,  # Invalid: should be Ch01-Ch12
                        }
                    },
                }
            ]
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create a dummy CSV file
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("header1,header2\nvalue1,value2")

        config = Config(str(config_file))
        assert len(config.datasets) == 1
        assert len(config.datasets[0].modules) == 1
        # Check that the module has no integrated charge data
        module = config.datasets[0].modules[0]
        assert hasattr(module, "integrated_charge_data")
        assert module.integrated_charge_data is None

    def test_config_with_invalid_charge_value_type(self, tmp_path):
        """Test config loading with invalid charge value type."""
        config_data = {
            "inputs": [
                {
                    "date": "2022-01-01",
                    "basePath": str(tmp_path),
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [1, 2]},
                    "integratedCharge": {
                        "PMA0": {
                            "Ch01": "not_a_number",
                            "Ch02": None,
                        }
                    },
                }
            ]
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create a dummy CSV file
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("header1,header2\nvalue1,value2")

        config = Config(str(config_file))
        assert len(config.datasets) == 1
        assert len(config.datasets[0].modules) == 1
        # Check that the module has no integrated charge data
        module = config.datasets[0].modules[0]
        assert hasattr(module, "integrated_charge_data")
        assert module.integrated_charge_data is None

    def test_config_with_negative_charge_value(self, tmp_path):
        """Test config loading with negative charge value."""
        config_data = {
            "inputs": [
                {
                    "date": "2022-01-01",
                    "basePath": str(tmp_path),
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [1, 2]},
                    "integratedCharge": {
                        "PMA0": {
                            "Ch01": -1.0,
                            "Ch02": 2.0,
                        }
                    },
                }
            ]
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create a dummy CSV file
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("header1,header2\nvalue1,value2")

        config = Config(str(config_file))
        assert len(config.datasets) == 1
        assert len(config.datasets[0].modules) == 1
        # Check that the module has no integrated charge data
        module = config.datasets[0].modules[0]
        assert hasattr(module, "integrated_charge_data")
        assert module.integrated_charge_data is None

    def test_config_with_missing_integrated_charge(self, tmp_path):
        """Test config loading without integrated charge data."""
        config_data = {
            "inputs": [
                {
                    "date": "2022-01-01",
                    "basePath": str(tmp_path),
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [1, 2]},
                }
            ]
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create a dummy CSV file
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("header1,header2\nvalue1,value2")

        config = Config(str(config_file))
        assert len(config.datasets) == 1
        assert len(config.datasets[0].modules) == 1
        # Check that the module has no integrated charge data
        module = config.datasets[0].modules[0]
        assert hasattr(module, "integrated_charge_data")
        assert module.integrated_charge_data is None

    def test_config_with_none_integrated_charge(self, tmp_path):
        """Test config loading with explicit None integrated charge data."""
        config_data = {
            "inputs": [
                {
                    "date": "2022-01-01",
                    "basePath": str(tmp_path),
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [1, 2]},
                    "integratedCharge": None,
                }
            ]
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create a dummy CSV file
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("header1,header2\nvalue1,value2")

        config = Config(str(config_file))
        assert len(config.datasets) == 1
        assert len(config.datasets[0].modules) == 1
        # Check that the module has no integrated charge data
        module = config.datasets[0].modules[0]
        assert hasattr(module, "integrated_charge_data")
        assert module.integrated_charge_data is None
