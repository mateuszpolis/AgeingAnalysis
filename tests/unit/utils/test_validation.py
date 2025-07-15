"""Tests for validation utilities."""

import pytest

from ageing_analysis.utils.validation import (
    validate_csv,
    validate_file_identifier,
    validate_integrated_charge_format,
    validate_path_exists,
)


class TestValidateCsv:
    """Test CSV validation function."""

    def test_validate_csv_nonexistent_file(self, tmp_path):
        """Test validation of non-existent file."""
        file_path = tmp_path / "nonexistent.csv"
        assert not validate_csv(str(file_path))

    def test_validate_csv_empty_file(self, tmp_path):
        """Test validation of empty file."""
        file_path = tmp_path / "empty.csv"
        file_path.write_text("")
        assert not validate_csv(str(file_path))

    def test_validate_csv_valid_file(self, tmp_path):
        """Test validation of valid CSV file."""
        file_path = tmp_path / "valid.csv"
        file_path.write_text("header1,header2\nvalue1,value2")
        assert validate_csv(str(file_path))


class TestValidateFileIdentifier:
    """Test file identifier validation function."""

    @pytest.mark.parametrize(
        "identifier,expected",
        [
            ("PMA0", True),
            ("PMA9", True),
            ("PMC0", True),
            ("PMC9", True),
            ("PMA10", False),
            ("PMC10", False),
            ("PMB0", False),
            ("PM0", False),
            ("PMA", False),
            ("", False),
        ],
    )
    def test_validate_file_identifier(self, identifier, expected):
        """Test file identifier validation with various inputs."""
        assert validate_file_identifier(identifier) == expected


class TestValidatePathExists:
    """Test path existence validation function."""

    def test_validate_path_exists_nonexistent(self, tmp_path):
        """Test validation of non-existent path."""
        path = tmp_path / "nonexistent"
        assert not validate_path_exists(str(path))

    def test_validate_path_exists_file(self, tmp_path):
        """Test validation of file path (should fail for directories)."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")
        assert not validate_path_exists(str(file_path))

    def test_validate_path_exists_directory(self, tmp_path):
        """Test validation of existing directory."""
        dir_path = tmp_path / "testdir"
        dir_path.mkdir()
        assert validate_path_exists(str(dir_path))


class TestValidateIntegratedChargeFormat:
    """Test integrated charge format validation function."""

    def test_validate_integrated_charge_format_none(self):
        """Test validation with None (should be valid)."""
        assert validate_integrated_charge_format(None, "2022-01-01")

    def test_validate_integrated_charge_format_not_dict(self):
        """Test validation with non-dict data."""
        assert not validate_integrated_charge_format("invalid", "2022-01-01")
        assert not validate_integrated_charge_format(123, "2022-01-01")
        assert not validate_integrated_charge_format([], "2022-01-01")

    def test_validate_integrated_charge_format_invalid_pm_name(self):
        """Test validation with invalid PM names."""
        invalid_data = {
            "INVALID": {"Ch01": 1.0},
            "PMA10": {"Ch01": 1.0},
            "PMB0": {"Ch01": 1.0},
        }
        for pm_name, data in invalid_data.items():
            assert not validate_integrated_charge_format({pm_name: data}, "2022-01-01")

    def test_validate_integrated_charge_format_pm_data_not_dict(self):
        """Test validation when PM data is not a dictionary."""
        invalid_data = {
            "PMA0": "not_a_dict",
            "PMC1": 123,
            "PMA2": [],
        }
        for pm_name, data in invalid_data.items():
            assert not validate_integrated_charge_format({pm_name: data}, "2022-01-01")

    def test_validate_integrated_charge_format_invalid_channel_name(self):
        """Test validation with invalid channel names."""
        invalid_data = {
            "PMA0": {
                "Ch00": 1.0,  # Invalid: should be Ch01-Ch12
                "Ch13": 1.0,  # Invalid: should be Ch01-Ch12
                "CH01": 1.0,  # Invalid: wrong case
                "ch01": 1.0,  # Invalid: wrong case
                "Channel1": 1.0,  # Invalid: wrong format
            }
        }
        for pm_name, data in invalid_data.items():
            assert not validate_integrated_charge_format({pm_name: data}, "2022-01-01")

    def test_validate_integrated_charge_format_invalid_charge_value_type(self):
        """Test validation with invalid charge value types."""
        invalid_data = {
            "PMA0": {
                "Ch01": "not_a_number",
                "Ch02": None,
                "Ch03": [],
                "Ch04": {},
            }
        }
        for pm_name, data in invalid_data.items():
            assert not validate_integrated_charge_format({pm_name: data}, "2022-01-01")

    def test_validate_integrated_charge_format_negative_charge(self):
        """Test validation with negative charge values."""
        invalid_data = {
            "PMA0": {
                "Ch01": -1.0,
                "Ch02": -0.5,
            }
        }
        for pm_name, data in invalid_data.items():
            assert not validate_integrated_charge_format({pm_name: data}, "2022-01-01")

    def test_validate_integrated_charge_format_valid(self):
        """Test validation with valid integrated charge data."""
        valid_data = {
            "PMA0": {
                "Ch01": 0.0,
                "Ch02": 1.5,
                "Ch03": 10,
                "Ch04": 0.001,
                "Ch05": 100.0,
                "Ch06": 0,
                "Ch07": 2.5,
                "Ch08": 15.7,
                "Ch09": 3,
                "Ch10": 45.123,
                "Ch11": 7.0,
                "Ch12": 99.999,
            },
            "PMC1": {
                "Ch01": 0.0,
                "Ch02": 2.0,
                "Ch03": 5.5,
                "Ch04": 0.5,
                "Ch05": 20.0,
                "Ch06": 1,
                "Ch07": 3.14,
                "Ch08": 12.5,
                "Ch09": 4,
                "Ch10": 30.0,
                "Ch11": 8.5,
                "Ch12": 50.0,
            },
        }
        assert validate_integrated_charge_format(valid_data, "2022-01-01")

    def test_validate_integrated_charge_format_mixed_valid_invalid(self):
        """Test validation with mixed valid and invalid data."""
        mixed_data = {
            "PMA0": {
                "Ch01": 1.0,  # Valid
                "Ch02": -1.0,  # Invalid: negative
            },
            "INVALID": {  # Invalid PM name
                "Ch01": 1.0,
            },
        }
        assert not validate_integrated_charge_format(mixed_data, "2022-01-01")
