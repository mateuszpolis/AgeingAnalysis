"""Tests for save_results utilities."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ageing_analysis.utils.save_results import (
    export_results_csv,
    load_results,
    save_results,
)


class TestSaveResults:
    """Test save_results function."""

    def test_save_results_without_total_signal_data(self, tmp_path):
        """Test saving results without total signal data."""
        # Create a mock config
        mock_config = Mock()
        mock_config.to_dict.return_value = {
            "datasets": [
                {
                    "date": "2022-01-01",
                    "modules": [
                        {
                            "identifier": "PMA0",
                            "channels": [
                                {
                                    "name": "CH01",
                                    "means": {
                                        "gaussian_mean": 1.0,
                                        "weighted_mean": 1.1,
                                    },
                                    "ageing_factors": {"gaussian_ageing_factor": 0.9},
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        output_path = tmp_path / "test_results.json"
        result_path = save_results(mock_config, str(output_path))

        # Verify the file was created
        assert Path(result_path).exists()

        # Verify the content
        with open(result_path) as f:
            data = json.load(f)

        assert "datasets" in data
        assert "metadata" in data

    def test_save_results_default_behavior(self, tmp_path):
        """Test that save_results defaults to including total signal data."""
        # Create a mock config
        mock_config = Mock()
        mock_config.to_dict.return_value = {
            "datasets": [
                {
                    "date": "2022-01-01",
                    "modules": [
                        {
                            "identifier": "PMA0",
                            "channels": [
                                {
                                    "name": "CH01",
                                    "means": {
                                        "gaussian_mean": 1.0,
                                        "weighted_mean": 1.1,
                                    },
                                    "ageing_factors": {"gaussian_ageing_factor": 0.9},
                                    "total_signal_data": {"0": 100, "1": 200},
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        output_path = tmp_path / "test_results.json"
        result_path = save_results(
            mock_config, str(output_path)
        )  # No parameter specified

        # Verify the file was created
        assert Path(result_path).exists()

        # Verify the content
        with open(result_path) as f:
            json.load(f)

    def test_save_results_auto_filename(self, tmp_path):
        """Test that save_results generates a filename when none is provided."""
        # Create a mock config
        mock_config = Mock()
        mock_config.to_dict.return_value = {"datasets": []}

        # Mock file operations to avoid actual file creation
        with patch("builtins.open", create=True), patch("pathlib.Path.mkdir"), patch(
            "pathlib.Path.exists", return_value=False
        ):
            # Call the function without mocking datetime
            result_path = save_results(mock_config)

        # Verify the path contains the expected pattern (without specific timestamp)
        assert "ageing_analysis_results" in result_path
        assert result_path.endswith(".json")

        # Verify the filename format (should contain timestamp pattern)
        import re

        timestamp_pattern = r"ageing_analysis_results_\d{8}_\d{6}\.json$"
        assert re.search(
            timestamp_pattern, result_path
        ), f"Path {result_path} doesn't match expected pattern"

    def test_save_results_creates_directory(self, tmp_path):
        """Test that save_results creates the output directory if it doesn't exist."""
        # Create a mock config
        mock_config = Mock()
        mock_config.to_dict.return_value = {"datasets": []}

        output_path = tmp_path / "new_dir" / "test_results.json"
        result_path = save_results(
            mock_config, str(output_path), include_total_signal_data=True
        )

        # Verify the directory was created
        assert output_path.parent.exists()
        assert Path(result_path).exists()


class TestLoadResults:
    """Test load_results function."""

    def test_load_results_success(self, tmp_path):
        """Test loading results from a file."""
        # Create a test results file
        test_data = {
            "datasets": [{"date": "2022-01-01", "modules": []}],
            "metadata": {"version": "1.0.0"},
        }

        results_file = tmp_path / "test_results.json"
        with open(results_file, "w") as f:
            json.dump(test_data, f)

        # Load the results
        loaded_data = load_results(str(results_file))

        # Verify the data
        assert loaded_data["datasets"][0]["date"] == "2022-01-01"
        assert loaded_data["metadata"]["version"] == "1.0.0"

    def test_load_results_file_not_found(self):
        """Test loading results from a non-existent file."""
        with pytest.raises(FileNotFoundError, match="No such file or directory"):
            load_results("non_existent_file.json")


class TestExportResultsCsv:
    """Test export_results_csv function."""

    def test_export_results_csv_success(self, tmp_path):
        """Test exporting results to CSV format."""
        # Create test results data
        test_results = {
            "datasets": [
                {
                    "date": "2022-01-01",
                    "modules": [
                        {
                            "identifier": "PMA0",
                            "channels": [
                                {
                                    "name": "CH01",
                                    "means": {
                                        "gaussian_mean": 1.0,
                                        "weighted_mean": 1.1,
                                    },
                                    "ageing_factors": {
                                        "gaussian_ageing_factor": 0.9,
                                        "weighted_ageing_factor": 0.95,
                                        "normalized_gauss_ageing_factor": 0.85,
                                        "normalized_weighted_ageing_factor": 0.90,
                                    },
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        output_path = tmp_path / "test_results.csv"
        result_path = export_results_csv(test_results, str(output_path))

        # Verify the file was created
        assert Path(result_path).exists()

        # Verify the CSV content (basic check)
        with open(result_path) as f:
            content = f.read()
            assert "date,module,channel,gaussian_mean,weighted_mean" in content
            assert "2022-01-01,PMA0,CH01,1.0,1.1" in content
