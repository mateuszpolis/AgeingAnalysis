"""Isolated tests for ageing_analysis.entities.config module.

This module focuses on path resolution.
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, mock_open, patch

import pytest

from ageing_analysis.entities.config import Config


class TestConfigPathResolution:
    """Test path resolution logic in Config without Dataset dependencies."""

    def setup_method(self):
        """Setup method run before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

    def teardown_method(self):
        """Teardown method run after each test."""
        os.chdir(self.original_cwd)
        # Clean up temp directories
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_temp_config(self, config_data):
        """Helper to create a temporary config file."""
        config_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, dir=self.temp_dir
        )
        json.dump(config_data, config_file, indent=2)
        config_file.close()
        return config_file.name

    def create_temp_directory(self, path):
        """Helper to create a temporary directory."""
        full_path = os.path.join(self.temp_dir, path)
        os.makedirs(full_path, exist_ok=True)
        return full_path

    @patch("ageing_analysis.entities.config.Dataset")
    def test_global_base_path_absolute(self, mock_dataset):
        """Test global base path with absolute path."""
        # Create test data structure
        global_data_dir = self.create_temp_directory("global_data")
        self.create_temp_directory("global_data/dataset1")

        # Setup mock dataset
        mock_dataset_instance = MagicMock()
        mock_dataset_instance.date = "2024-01-01"
        mock_dataset.return_value = mock_dataset_instance

        config_data = {
            "basePath": global_data_dir,
            "inputs": [
                {
                    "date": "2024-01-01",
                    "basePath": "dataset1",
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [0]},
                    "validateHeader": False,
                }
            ],
        }

        config_path = self.create_temp_config(config_data)
        Config(config_path)

        # Verify Dataset was called with combined path
        expected_path = os.path.join(global_data_dir, "dataset1")
        mock_dataset.assert_called_once_with(
            "2024-01-01",
            expected_path,
            {"PMA0": "test.csv"},
            {"PM": "PMA0", "CH": [0]},
            False,
        )

    @patch("ageing_analysis.entities.config.Dataset")
    def test_global_base_path_relative(self, mock_dataset):
        """Test global base path with relative path."""
        # Change to temp directory for relative path testing
        os.chdir(self.temp_dir)

        # Create test data structure
        self.create_temp_directory("relative_data")
        dataset_dir = self.create_temp_directory("relative_data/dataset1")

        # Setup mock dataset
        mock_dataset_instance = MagicMock()
        mock_dataset_instance.date = "2024-01-01"
        mock_dataset.return_value = mock_dataset_instance

        config_data = {
            "basePath": "relative_data",
            "inputs": [
                {
                    "date": "2024-01-01",
                    "basePath": "dataset1",
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [0]},
                    "validateHeader": False,
                }
            ],
        }

        config_path = self.create_temp_config(config_data)
        Config(config_path)

        # Should resolve to absolute path - normalize both paths for comparison
        expected_path = os.path.realpath(os.path.abspath(dataset_dir))
        actual_call = mock_dataset.call_args[0]
        actual_path = os.path.realpath(actual_call[1])

        assert actual_call[0] == "2024-01-01"
        assert actual_path == expected_path
        assert actual_call[2] == {"PMA0": "test.csv"}
        assert actual_call[3] == {"PM": "PMA0", "CH": [0]}
        assert actual_call[4] is False

    @patch("ageing_analysis.entities.config.Dataset")
    def test_dataset_absolute_path_overrides_global(self, mock_dataset):
        """Test that absolute dataset path overrides global base path."""
        # Create test data structure
        global_dir = self.create_temp_directory("global_data")
        absolute_dir = self.create_temp_directory("absolute_data")

        # Setup mock dataset
        mock_dataset_instance = MagicMock()
        mock_dataset_instance.date = "2024-01-01"
        mock_dataset.return_value = mock_dataset_instance

        config_data = {
            "basePath": global_dir,
            "inputs": [
                {
                    "date": "2024-01-01",
                    "basePath": absolute_dir,
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [0]},
                    "validateHeader": False,
                }
            ],
        }

        config_path = self.create_temp_config(config_data)
        Config(config_path)

        # Should use absolute path, ignoring global
        mock_dataset.assert_called_once_with(
            "2024-01-01",
            absolute_dir,
            {"PMA0": "test.csv"},
            {"PM": "PMA0", "CH": [0]},
            False,
        )

    @patch("ageing_analysis.entities.config.Dataset")
    def test_global_path_only(self, mock_dataset):
        """Test initialization with only global base path."""
        # Create test data structure
        global_dir = self.create_temp_directory("global_only")

        # Setup mock dataset
        mock_dataset_instance = MagicMock()
        mock_dataset_instance.date = "2024-01-01"
        mock_dataset.return_value = mock_dataset_instance

        config_data = {
            "basePath": global_dir,
            "inputs": [
                {
                    "date": "2024-01-01",
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [0]},
                    "validateHeader": False,
                }
            ],
        }

        config_path = self.create_temp_config(config_data)
        Config(config_path)

        # Should use global path
        mock_dataset.assert_called_once_with(
            "2024-01-01",
            global_dir,
            {"PMA0": "test.csv"},
            {"PM": "PMA0", "CH": [0]},
            False,
        )

    @patch("ageing_analysis.entities.config.Dataset")
    def test_no_paths_uses_current_directory(self, mock_dataset):
        """Test initialization with no paths uses current directory."""
        # Change to temp directory
        os.chdir(self.temp_dir)

        # Setup mock dataset
        mock_dataset_instance = MagicMock()
        mock_dataset_instance.date = "2024-01-01"
        mock_dataset.return_value = mock_dataset_instance

        config_data = {
            "inputs": [
                {
                    "date": "2024-01-01",
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [0]},
                    "validateHeader": False,
                }
            ]
        }

        config_path = self.create_temp_config(config_data)
        Config(config_path)

        # Should use current directory - normalize paths for comparison
        expected_path = os.path.realpath(self.temp_dir)
        actual_call = mock_dataset.call_args[0]
        actual_path = os.path.realpath(actual_call[1])

        assert actual_call[0] == "2024-01-01"
        assert actual_path == expected_path
        assert actual_call[2] == {"PMA0": "test.csv"}
        assert actual_call[3] == {"PM": "PMA0", "CH": [0]}
        assert actual_call[4] is False

    def test_nonexistent_path_skips_dataset(self):
        """Test that nonexistent paths cause datasets to be skipped."""
        config_data = {
            "inputs": [
                {
                    "date": "2024-01-01",
                    "basePath": "/nonexistent/path",
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [0]},
                    "validateHeader": False,
                }
            ]
        }

        config_path = self.create_temp_config(config_data)
        config = Config(config_path)

        # Should have no datasets due to nonexistent path
        assert len(config.datasets) == 0

    @patch("ageing_analysis.entities.config.Dataset")
    def test_multiple_datasets_sorted_by_date(self, mock_dataset):
        """Test that multiple datasets are sorted by date."""
        # Create test data structure
        dir1 = self.create_temp_directory("data1")
        dir2 = self.create_temp_directory("data2")
        dir3 = self.create_temp_directory("data3")

        # Setup mock datasets
        mock_dataset_instances = []
        for date in ["2024-01-01", "2024-02-01", "2024-03-01"]:
            mock_instance = MagicMock()
            mock_instance.date = date
            mock_dataset_instances.append(mock_instance)

        mock_dataset.side_effect = mock_dataset_instances

        config_data = {
            "inputs": [
                {
                    "date": "2024-03-01",
                    "basePath": dir3,
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [0]},
                    "validateHeader": False,
                },
                {
                    "date": "2024-01-01",
                    "basePath": dir1,
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [0]},
                    "validateHeader": False,
                },
                {
                    "date": "2024-02-01",
                    "basePath": dir2,
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [0]},
                    "validateHeader": False,
                },
            ]
        }

        config_path = self.create_temp_config(config_data)
        config = Config(config_path)

        # Should have 3 datasets, sorted by date
        assert len(config.datasets) == 3
        assert config.datasets[0].date == "2024-01-01"
        assert config.datasets[1].date == "2024-02-01"
        assert config.datasets[2].date == "2024-03-01"

    def test_missing_inputs_field_raises_error(self):
        """Test that missing inputs field raises ValueError."""
        config_data = {"basePath": "/some/path"}
        config_path = self.create_temp_config(config_data)

        with pytest.raises(ValueError, match="inputs field not found"):
            Config(config_path)

    @patch("ageing_analysis.entities.config.Dataset")
    def test_missing_date_field_raises_error(self, mock_dataset):
        """Test that missing date field raises ValueError."""
        data_dir = self.create_temp_directory("test_data")

        config_data = {
            "inputs": [
                {
                    "basePath": data_dir,
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0", "CH": [0]},
                    "validateHeader": False,
                }
            ]
        }

        config_path = self.create_temp_config(config_data)

        with pytest.raises(ValueError, match="date field missing"):
            Config(config_path)

    @patch("ageing_analysis.entities.config.Dataset")
    def test_invalid_refch_not_dict_raises_error(self, mock_dataset):
        """Test that invalid refCH field raises Exception."""
        data_dir = self.create_temp_directory("test_data")

        config_data = {
            "inputs": [
                {
                    "date": "2024-01-01",
                    "basePath": data_dir,
                    "files": {"PMA0": "test.csv"},
                    "refCH": "invalid",
                    "validateHeader": False,
                }
            ]
        }

        config_path = self.create_temp_config(config_data)

        with pytest.raises(Exception, match="refCH field must be a dictionary"):
            Config(config_path)

    @patch("ageing_analysis.entities.config.Dataset")
    def test_missing_refch_pm_raises_error(self, mock_dataset):
        """Test that missing refCH PM key raises Exception."""
        data_dir = self.create_temp_directory("test_data")

        config_data = {
            "inputs": [
                {
                    "date": "2024-01-01",
                    "basePath": data_dir,
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"CH": [0]},
                    "validateHeader": False,
                }
            ]
        }

        config_path = self.create_temp_config(config_data)

        with pytest.raises(Exception, match="refCH field missing PM key"):
            Config(config_path)

    @patch("ageing_analysis.entities.config.Dataset")
    def test_missing_refch_ch_raises_error(self, mock_dataset):
        """Test that missing refCH CH key raises Exception."""
        data_dir = self.create_temp_directory("test_data")

        config_data = {
            "inputs": [
                {
                    "date": "2024-01-01",
                    "basePath": data_dir,
                    "files": {"PMA0": "test.csv"},
                    "refCH": {"PM": "PMA0"},
                    "validateHeader": False,
                }
            ]
        }

        config_path = self.create_temp_config(config_data)

        with pytest.raises(Exception, match="refCH field missing CH key"):
            Config(config_path)

    def test_complex_path_resolution_scenario(self):
        """Test complex scenario with mixed absolute/relative paths."""
        # Create test structure
        os.chdir(self.temp_dir)

        global_dir = self.create_temp_directory("global")
        relative_dataset_dir = self.create_temp_directory("global/relative_dataset")
        absolute_dataset_dir = self.create_temp_directory("absolute_dataset")

        with patch("ageing_analysis.entities.config.Dataset") as mock_dataset:
            # Setup mock datasets
            mock_instances = []
            dates = ["2024-01-01", "2024-01-02", "2024-01-03"]
            for date in dates:
                mock_instance = MagicMock()
                mock_instance.date = date
                mock_instances.append(mock_instance)
            mock_dataset.side_effect = mock_instances

            config_data = {
                "basePath": "global",
                "inputs": [
                    {
                        "date": "2024-01-01",
                        "basePath": "relative_dataset",
                        "files": {"PMA0": "test.csv"},
                        "refCH": {"PM": "PMA0", "CH": [0]},
                        "validateHeader": False,
                    },
                    {
                        "date": "2024-01-02",
                        "basePath": absolute_dataset_dir,
                        "files": {"PMA0": "test.csv"},
                        "refCH": {"PM": "PMA0", "CH": [0]},
                        "validateHeader": False,
                    },
                    {
                        "date": "2024-01-03",
                        "files": {"PMA0": "test.csv"},
                        "refCH": {"PM": "PMA0", "CH": [0]},
                        "validateHeader": False,
                    },
                ],
            }

            config_path = self.create_temp_config(config_data)
            config = Config(config_path)

            # Verify all three datasets were created with correct paths
            assert len(config.datasets) == 3

            # Check the calls to Dataset constructor
            calls = mock_dataset.call_args_list

            # First dataset: global + relative - normalize paths for comparison
            expected_path1 = os.path.realpath(os.path.normpath(relative_dataset_dir))
            actual_path1 = os.path.realpath(calls[0][0][1])
            assert actual_path1 == expected_path1

            # Second dataset: absolute (ignores global) - normalize paths for comparison
            expected_path2 = os.path.realpath(absolute_dataset_dir)
            actual_path2 = os.path.realpath(calls[1][0][1])
            assert actual_path2 == expected_path2

            # Third dataset: global only - normalize paths for comparison
            expected_path3 = os.path.realpath(os.path.normpath(global_dir))
            actual_path3 = os.path.realpath(calls[2][0][1])
            assert actual_path3 == expected_path3


class TestConfigFileHandling:
    """Test file handling and configuration loading."""

    def setup_method(self):
        """Setup method run before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

    def teardown_method(self):
        """Teardown method run after each test."""
        os.chdir(self.original_cwd)
        # Clean up temp directories
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_no_config_files_raises_error(self):
        """Test that missing config files raises FileNotFoundError."""
        # Change to empty temp directory
        os.chdir(self.temp_dir)

        with pytest.raises(
            FileNotFoundError,
            match="Neither config.json nor ageing_analysis_results.json found",
        ):
            Config()

    def test_init_with_results_file(self):
        """Test initialization with existing results file."""
        # Change to temp directory
        os.chdir(self.temp_dir)

        # Create ageing_analysis_results.json
        results_data = {"datasets": [{"date": "2024-01-01", "modules": []}]}

        results_path = os.path.join(self.temp_dir, "ageing_analysis_results.json")
        with open(results_path, "w") as f:
            json.dump(results_data, f)

        config = Config()  # No path provided

        assert hasattr(config, "results_data")
        assert len(config.datasets) == 0  # Empty for results mode

    def test_to_dict_with_results_data(self):
        """Test to_dict method with loaded results data."""
        # Change to temp directory
        os.chdir(self.temp_dir)

        results_data = {"datasets": [{"date": "2024-01-01", "modules": []}]}

        results_path = os.path.join(self.temp_dir, "ageing_analysis_results.json")
        with open(results_path, "w") as f:
            json.dump(results_data, f)

        config = Config()
        result = config.to_dict()

        assert result == results_data

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_file_reading_error_handling(self, mock_json_load, mock_file_open):
        """Test error handling during file reading."""
        mock_json_load.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        with pytest.raises(json.JSONDecodeError):
            Config("invalid_config.json")

    def test_empty_inputs_list(self):
        """Test handling of empty inputs list."""
        config_data = {"inputs": []}

        # Create temp config file
        config_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, dir=self.temp_dir
        )
        json.dump(config_data, config_file, indent=2)
        config_file.close()

        config = Config(config_file.name)

        assert len(config.datasets) == 0
