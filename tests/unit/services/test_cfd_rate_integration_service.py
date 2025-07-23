"""Tests for the CFDRateIntegrationService."""

import datetime
import os
from unittest.mock import Mock

import pandas as pd

from ageing_analysis.services.cfd_rate_integration_service import (
    CFDRateIntegrationService,
)


class TestCFDRateIntegrationService:
    """Test cases for CFDRateIntegrationService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.dataset = Mock()
        self.service = CFDRateIntegrationService(self.dataset)

    def test_get_datapoints_generates_correct_datapoints(self):
        """Test that _get_datapoints generates the correct datapoints."""
        # Act
        datapoints = list(self.service._get_datapoints())

        # Assert
        assert len(datapoints) > 0

        # Check PMA datapoints (0-8, channels 1-12)
        pma_datapoints = [dp for dp in datapoints if "PMA" in dp]
        assert len(pma_datapoints) == 9 * 12  # 9 PMs (0-8) * 12 channels

        # Check PMC datapoints (0-8: 12 channels each, PM9: 8 channels)
        pmc_datapoints = [dp for dp in datapoints if "PMC" in dp]
        assert (
            len(pmc_datapoints) == 9 * 12 + 1 * 8
        )  # 9 PMs (0-8) * 12 channels + 1 PM (9) * 8 channels

        # Check total datapoints
        assert len(datapoints) == 224  # 9*12 + 9*12 + 1*8 = 108 + 108 + 8 = 224

        # Check specific examples
        assert "ft0_dcs:FEE/PMA0/Ch01.actual.CFD_RATE" in datapoints
        assert "ft0_dcs:FEE/PMA8/Ch12.actual.CFD_RATE" in datapoints
        assert "ft0_dcs:FEE/PMC0/Ch01.actual.CFD_RATE" in datapoints
        assert "ft0_dcs:FEE/PMC9/Ch08.actual.CFD_RATE" in datapoints

        # Check that PMA9 doesn't exist (should break at PMA9)
        pma9_datapoints = [dp for dp in datapoints if "PMA9" in dp]
        assert len(pma9_datapoints) == 0

        # Check that PMC9 channels 9-12 don't exist (should break at Ch09)
        pmc9_ch9_plus = [
            dp
            for dp in datapoints
            if "PMC9" in dp and any(f"Ch{ch:02d}" in dp for ch in range(9, 13))
        ]
        assert len(pmc9_ch9_plus) == 0

    def test_get_datapoints_format(self):
        """Test that datapoints have the correct format."""
        # Act
        datapoints = list(self.service._get_datapoints())

        # Assert
        for datapoint in datapoints:
            assert datapoint.startswith("ft0_dcs:FEE/")
            assert datapoint.endswith(".actual.CFD_RATE")
            assert "PM" in datapoint
            assert "Ch" in datapoint

    def test_integrate_cfd_rate_trapezoidal_empty_dataframe(self):
        """Test trapezoidal integration with empty DataFrame."""
        # Arrange
        df = pd.DataFrame(columns=["timestamp", "value"])

        # Act
        result = self.service._integrate_cfd_rate_trapezoidal(df)

        # Assert
        assert result == 0.0

    def test_integrate_cfd_rate_trapezoidal_single_point(self):
        """Test trapezoidal integration with single data point."""
        # Arrange
        df = pd.DataFrame({"timestamp": ["2025-01-01 12:00:00"], "value": [10.0]})

        # Act
        result = self.service._integrate_cfd_rate_trapezoidal(df)

        # Assert
        assert result == 0.0

    def test_integrate_cfd_rate_trapezoidal_two_points(self):
        """Test trapezoidal integration with two data points."""
        # Arrange
        df = pd.DataFrame(
            {
                "timestamp": ["2025-01-01 12:00:00", "2025-01-01 13:00:00"],
                "value": [10.0, 20.0],
            }
        )

        # Act
        result = self.service._integrate_cfd_rate_trapezoidal(df)

        # Assert
        # Expected: (10 + 20) / 2 * 3600 seconds = 15 * 3600 = 54000
        expected = 15.0 * 3600  # Average value * time difference in seconds
        assert abs(result - expected) < 1e-10

    def test_integrate_cfd_rate_trapezoidal_constant_value(self):
        """Test trapezoidal integration with constant value."""
        # Arrange
        df = pd.DataFrame(
            {
                "timestamp": [
                    "2025-01-01 12:00:00",
                    "2025-01-01 13:00:00",
                    "2025-01-01 14:00:00",
                    "2025-01-01 15:00:00",
                ],
                "value": [5.0, 5.0, 5.0, 5.0],
            }
        )

        # Act
        result = self.service._integrate_cfd_rate_trapezoidal(df)

        # Assert
        # Expected: 5.0 * (3 * 3600) = 54000
        expected = 5.0 * (3 * 3600)  # Value * total time in seconds
        assert abs(result - expected) < 1e-10

    def test_integrate_cfd_rate_trapezoidal_linear_increase(self):
        """Test trapezoidal integration with linear increase."""
        # Arrange
        df = pd.DataFrame(
            {
                "timestamp": [
                    "2025-01-01 12:00:00",
                    "2025-01-01 13:00:00",
                    "2025-01-01 14:00:00",
                ],
                "value": [0.0, 10.0, 20.0],
            }
        )

        # Act
        result = self.service._integrate_cfd_rate_trapezoidal(df)

        # Assert
        # Expected: (0+10)/2 * 3600 + (10+20)/2 * 3600 = 5*3600 + 15*3600 = 72000
        expected = (5.0 + 15.0) * 3600
        assert abs(result - expected) < 1e-10

    def test_integrate_cfd_rate_trapezoidal_unsorted_timestamps(self):
        """Test trapezoidal integration with unsorted timestamps."""
        # Arrange
        df = pd.DataFrame(
            {
                "timestamp": [
                    "2025-01-01 14:00:00",
                    "2025-01-01 12:00:00",
                    "2025-01-01 13:00:00",
                ],
                "value": [20.0, 0.0, 10.0],
            }
        )

        # Act
        result = self.service._integrate_cfd_rate_trapezoidal(df)

        # Assert
        # Should be the same as sorted version
        expected = (5.0 + 15.0) * 3600
        assert abs(result - expected) < 1e-10

    def test_integrate_cfd_rate_empty_dataframe(self):
        """Test integration with empty DataFrame."""
        # Arrange
        df = pd.DataFrame(columns=["timestamp", "value", "element_name"])

        # Act
        result = self.service._integrate_cfd_rate(df)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert list(result.columns) == ["timestamp", "value", "element_name"]

    def test_integrate_cfd_rate_single_element_single_day(self):
        """Test integration with single element and single day."""
        # Arrange
        df = pd.DataFrame(
            {
                "timestamp": [
                    "2025-01-01 12:00:00",
                    "2025-01-01 13:00:00",
                    "2025-01-01 14:00:00",
                ],
                "value": [10.0, 20.0, 30.0],
                "element_name": ["test_element"] * 3,
            }
        )
        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Act
        result = self.service._integrate_cfd_rate(df)

        # Assert
        assert len(result) == 1
        assert result.iloc[0]["element_name"] == "test_element"
        assert result.iloc[0]["timestamp"] == pd.Timestamp("2025-01-01 12:00:00")
        # Expected: (10+20)/2 * 3600 + (20+30)/2 * 3600 = 15*3600 + 25*3600 = 144000
        expected = (15.0 + 25.0) * 3600
        assert abs(result.iloc[0]["value"] - expected) < 1e-10

    def test_integrate_cfd_rate_multiple_elements(self):
        """Test integration with multiple elements."""
        # Arrange
        df = pd.DataFrame(
            {
                "timestamp": [
                    "2025-01-01 12:00:00",
                    "2025-01-01 13:00:00",
                    "2025-01-01 12:00:00",
                    "2025-01-01 13:00:00",
                ],
                "value": [10.0, 20.0, 5.0, 15.0],
                "element_name": ["element1", "element1", "element2", "element2"],
            }
        )
        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Act
        result = self.service._integrate_cfd_rate(df)

        # Assert
        assert len(result) == 2
        result_sorted = result.sort_values("element_name").reset_index(drop=True)

        # element1: (10+20)/2 * 3600 = 15*3600 = 54000
        assert result_sorted.iloc[0]["element_name"] == "element1"
        assert abs(result_sorted.iloc[0]["value"] - 15.0 * 3600) < 1e-10

        # element2: (5+15)/2 * 3600 = 10*3600 = 36000
        assert result_sorted.iloc[1]["element_name"] == "element2"
        assert abs(result_sorted.iloc[1]["value"] - 10.0 * 3600) < 1e-10

    def test_integrate_cfd_rate_multiple_days(self):
        """Test integration with multiple days."""
        # Arrange
        df = pd.DataFrame(
            {
                "timestamp": [
                    "2025-01-01 12:00:00",
                    "2025-01-01 13:00:00",
                    "2025-01-02 12:00:00",
                    "2025-01-02 13:00:00",
                ],
                "value": [10.0, 20.0, 30.0, 40.0],
                "element_name": ["test_element"] * 4,
            }
        )
        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Act
        result = self.service._integrate_cfd_rate(df)

        # Assert
        assert len(result) == 2
        result_sorted = result.sort_values("timestamp").reset_index(drop=True)

        # Day 1: (10+20)/2 * 3600 = 15*3600 = 54000
        assert result_sorted.iloc[0]["timestamp"] == pd.Timestamp("2025-01-01 12:00:00")
        assert abs(result_sorted.iloc[0]["value"] - 15.0 * 3600) < 1e-10

        # Day 2: (30+40)/2 * 3600 = 35*3600 = 126000
        assert result_sorted.iloc[1]["timestamp"] == pd.Timestamp("2025-01-02 12:00:00")
        assert abs(result_sorted.iloc[1]["value"] - 35.0 * 3600) < 1e-10

    def test_integrate_cfd_rate_day_boundary_12pm(self):
        """Test integration with data around 12pm day boundary."""
        # Arrange
        df = pd.DataFrame(
            {
                "timestamp": [
                    "2025-01-01 11:59:00",  # Before 12pm - should be excluded
                    "2025-01-01 12:00:00",  # At 12pm - should be included
                    "2025-01-01 13:00:00",  # After 12pm - should be included
                    "2025-01-02 11:59:00",  # Before next 12pm - should be included
                    "2025-01-02 12:00:00",  # At next 12pm - should be excluded
                ],
                "value": [1.0, 10.0, 20.0, 30.0, 40.0],
                "element_name": ["test_element"] * 5,
            }
        )
        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Act
        result = self.service._integrate_cfd_rate(df)

        # Assert
        # The integration logic creates days based on 12pm boundaries
        # Data before 12pm goes to previous day, data after 12pm goes to current day
        assert len(result) == 3  # 2024-12-31, 2025-01-01, 2025-01-02
        result_sorted = result.sort_values("timestamp").reset_index(drop=True)

        # Check that we have the expected timestamps
        expected_timestamps = [
            pd.Timestamp("2024-12-31 12:00:00"),
            pd.Timestamp("2025-01-01 12:00:00"),
            pd.Timestamp("2025-01-02 12:00:00"),
        ]
        for i, expected_ts in enumerate(expected_timestamps):
            assert result_sorted.iloc[i]["timestamp"] == expected_ts

    def test_integrate_cfd_rate_no_data_in_12pm_period(self):
        """Test integration when no data exists in the 12pm-12pm period."""
        # Arrange
        df = pd.DataFrame(
            {
                "timestamp": [
                    "2025-01-01 11:00:00",  # Before 12pm
                    "2025-01-01 11:30:00",  # Before 12pm
                ],
                "value": [10.0, 20.0],
                "element_name": ["test_element"] * 2,
            }
        )
        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Act
        result = self.service._integrate_cfd_rate(df)

        # Assert
        # Data before 12pm gets assigned to the previous day (2024-12-31)
        assert len(result) == 1
        assert result.iloc[0]["timestamp"] == pd.Timestamp("2024-12-31 12:00:00")
        # The integration should be (10+20)/2 * 1800 = 15 * 1800 = 27000
        expected = 15.0 * 1800  # 30 minutes = 1800 seconds
        assert abs(result.iloc[0]["value"] - expected) < 1e-10

    def test_integrate_cfd_rate_complex_scenario(self):
        """Test integration with complex scenario: multiple elements, multiple days."""
        # Arrange
        df = pd.DataFrame(
            {
                "timestamp": [
                    # Day 1
                    "2025-01-01 12:00:00",
                    "2025-01-01 13:00:00",
                    "2025-01-01 14:00:00",
                    "2025-01-01 12:00:00",
                    "2025-01-01 13:00:00",
                    "2025-01-01 14:00:00",
                    # Day 2
                    "2025-01-02 12:00:00",
                    "2025-01-02 13:00:00",
                    "2025-01-02 14:00:00",
                    "2025-01-02 12:00:00",
                    "2025-01-02 13:00:00",
                    "2025-01-02 14:00:00",
                ],
                "value": [
                    # Day 1 - element1
                    10.0,
                    20.0,
                    30.0,
                    # Day 1 - element2
                    5.0,
                    15.0,
                    25.0,
                    # Day 2 - element1
                    40.0,
                    50.0,
                    60.0,
                    # Day 2 - element2
                    35.0,
                    45.0,
                    55.0,
                ],
                "element_name": [
                    "element1",
                    "element1",
                    "element1",
                    "element2",
                    "element2",
                    "element2",
                    "element1",
                    "element1",
                    "element1",
                    "element2",
                    "element2",
                    "element2",
                ],
            }
        )
        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Act
        result = self.service._integrate_cfd_rate(df)

        # Assert
        assert len(result) == 4  # 2 elements * 2 days

        # Sort by element_name, then by timestamp
        result_sorted = result.sort_values(["element_name", "timestamp"]).reset_index(
            drop=True
        )

        # element1, day1: (10+20)/2*3600 + (20+30)/2*3600 = 15*3600 + 25*3600 = 144000
        assert result_sorted.iloc[0]["element_name"] == "element1"
        assert result_sorted.iloc[0]["timestamp"] == pd.Timestamp("2025-01-01 12:00:00")
        assert abs(result_sorted.iloc[0]["value"] - (15.0 + 25.0) * 3600) < 1e-10

        # element1, day2: (40+50)/2*3600 + (50+60)/2*3600 = 45*3600 + 55*3600 = 360000
        assert result_sorted.iloc[1]["element_name"] == "element1"
        assert result_sorted.iloc[1]["timestamp"] == pd.Timestamp("2025-01-02 12:00:00")
        assert abs(result_sorted.iloc[1]["value"] - (45.0 + 55.0) * 3600) < 1e-10

        # element2, day1: (5+15)/2*3600 + (15+25)/2*3600 = 10*3600 + 20*3600 = 108000
        assert result_sorted.iloc[2]["element_name"] == "element2"
        assert result_sorted.iloc[2]["timestamp"] == pd.Timestamp("2025-01-01 12:00:00")
        assert abs(result_sorted.iloc[2]["value"] - (10.0 + 20.0) * 3600) < 1e-10

        # element2, day2: (35+45)/2*3600 + (45+55)/2*3600 = 40*3600 + 50*3600 = 324000
        assert result_sorted.iloc[3]["element_name"] == "element2"
        assert result_sorted.iloc[3]["timestamp"] == pd.Timestamp("2025-01-02 12:00:00")
        assert abs(result_sorted.iloc[3]["value"] - (40.0 + 50.0) * 3600) < 1e-10

    def test_integrate_cfd_rate_timestamp_format_handling(self):
        """Test that integration handles different timestamp formats correctly."""
        # Arrange
        df = pd.DataFrame(
            {
                "timestamp": [
                    pd.Timestamp("2025-01-01 12:00:00"),
                    pd.Timestamp("2025-01-01 13:00:00"),
                ],
                "value": [10.0, 20.0],
                "element_name": ["test_element"] * 2,
            }
        )

        # Act
        result = self.service._integrate_cfd_rate(df)

        # Assert
        assert len(result) == 1
        assert result.iloc[0]["timestamp"] == pd.Timestamp("2025-01-01 12:00:00")
        expected = 15.0 * 3600  # (10+20)/2 * 3600
        assert abs(result.iloc[0]["value"] - expected) < 1e-10

    def test_save_integrated_cfd_rate_creates_new_file(self):
        """Test that _save_integrated_cfd_rate creates a new parquet
        file when none exists.
        """
        # Arrange
        test_filename = "test_integrated_cfd_rate.parquet"
        test_data = pd.DataFrame(
            {
                "timestamp": [
                    pd.Timestamp("2025-01-01 12:00:00"),
                    pd.Timestamp("2025-01-02 12:00:00"),
                ],
                "value": [100.0, 200.0],
                "element_name": ["test_element", "test_element"],
            }
        )

        # Clean up any existing test file
        if os.path.exists(test_filename):
            os.remove(test_filename)

        # Act
        self.service._save_integrated_cfd_rate(test_data, test_filename)

        # Assert
        assert os.path.exists(test_filename)

        # Verify file contents
        df_saved = pd.read_parquet(test_filename)
        assert len(df_saved) == 2
        assert list(df_saved.columns) == ["date", "element_name", "value"]
        assert df_saved.iloc[0]["date"] == datetime.date(2025, 1, 1)
        assert df_saved.iloc[0]["element_name"] == "test_element"
        assert df_saved.iloc[0]["value"] == 100.0

        # Clean up
        os.remove(test_filename)

    def test_save_integrated_cfd_rate_incremental_update(self):
        """Test that _save_integrated_cfd_rate handles incremental updates correctly."""
        # Arrange
        test_filename = "test_integrated_cfd_rate.parquet"

        # Initial data
        initial_data = pd.DataFrame(
            {
                "timestamp": [pd.Timestamp("2025-01-01 12:00:00")],
                "value": [100.0],
                "element_name": ["test_element"],
            }
        )

        # New data
        new_data = pd.DataFrame(
            {
                "timestamp": [pd.Timestamp("2025-01-02 12:00:00")],
                "value": [200.0],
                "element_name": ["test_element"],
            }
        )

        # Clean up any existing test file
        if os.path.exists(test_filename):
            os.remove(test_filename)

        # Act
        self.service._save_integrated_cfd_rate(initial_data, test_filename)
        self.service._save_integrated_cfd_rate(new_data, test_filename)

        # Assert
        df_saved = pd.read_parquet(test_filename)
        assert len(df_saved) == 2
        assert df_saved.iloc[0]["date"] == datetime.date(2025, 1, 1)
        assert df_saved.iloc[0]["value"] == 100.0
        assert df_saved.iloc[1]["date"] == datetime.date(2025, 1, 2)
        assert df_saved.iloc[1]["value"] == 200.0

        # Clean up
        os.remove(test_filename)

    def test_save_integrated_cfd_rate_duplicate_handling(self):
        """Test that _save_integrated_cfd_rate handles duplicates correctly."""
        # Arrange
        test_filename = "test_integrated_cfd_rate.parquet"

        # Initial data
        initial_data = pd.DataFrame(
            {
                "timestamp": [pd.Timestamp("2025-01-01 12:00:00")],
                "value": [100.0],
                "element_name": ["test_element"],
            }
        )

        # Duplicate data with different value
        duplicate_data = pd.DataFrame(
            {
                "timestamp": [pd.Timestamp("2025-01-01 12:00:00")],
                "value": [150.0],  # Different value
                "element_name": ["test_element"],
            }
        )

        # Clean up any existing test file
        if os.path.exists(test_filename):
            os.remove(test_filename)

        # Act
        self.service._save_integrated_cfd_rate(initial_data, test_filename)
        self.service._save_integrated_cfd_rate(duplicate_data, test_filename)

        # Assert
        df_saved = pd.read_parquet(test_filename)
        assert len(df_saved) == 1  # Should have only one record
        assert df_saved.iloc[0]["value"] == 150.0  # Should keep the latest value

        # Clean up
        os.remove(test_filename)

    def test_save_integrated_cfd_rate_multiple_elements(self):
        """Test that _save_integrated_cfd_rate handles multiple elements correctly."""
        # Arrange
        test_filename = "test_integrated_cfd_rate.parquet"

        test_data = pd.DataFrame(
            {
                "timestamp": [
                    pd.Timestamp("2025-01-01 12:00:00"),
                    pd.Timestamp("2025-01-01 12:00:00"),
                    pd.Timestamp("2025-01-02 12:00:00"),
                    pd.Timestamp("2025-01-02 12:00:00"),
                ],
                "value": [100.0, 200.0, 150.0, 250.0],
                "element_name": ["element1", "element2", "element1", "element2"],
            }
        )

        # Clean up any existing test file
        if os.path.exists(test_filename):
            os.remove(test_filename)

        # Act
        self.service._save_integrated_cfd_rate(test_data, test_filename)

        # Assert
        df_saved = pd.read_parquet(test_filename)
        assert len(df_saved) == 4

        # Check sorting
        assert df_saved.iloc[0]["date"] == datetime.date(2025, 1, 1)
        assert df_saved.iloc[0]["element_name"] == "element1"
        assert df_saved.iloc[1]["date"] == datetime.date(2025, 1, 1)
        assert df_saved.iloc[1]["element_name"] == "element2"

        # Clean up
        os.remove(test_filename)

    def test_get_available_data_coverage_empty_file(self):
        """Test _get_available_data_coverage when file doesn't exist."""
        # Arrange
        test_filename = "nonexistent_file.parquet"

        # Act
        coverage = self.service._get_available_data_coverage(test_filename)

        # Assert
        assert coverage == {}

    def test_get_available_data_coverage_single_element(self):
        """Test _get_available_data_coverage with single element data."""
        # Arrange
        test_filename = "test_coverage.parquet"
        test_data = pd.DataFrame(
            {
                "date": [
                    datetime.date(2025, 1, 1),
                    datetime.date(2025, 1, 2),
                    datetime.date(2025, 1, 3),
                ],
                "element_name": ["test_element"] * 3,
                "value": [100.0, 200.0, 300.0],
            }
        )

        # Clean up any existing test file
        if os.path.exists(test_filename):
            os.remove(test_filename)

        test_data.to_parquet(test_filename, index=False)

        # Act
        coverage = self.service._get_available_data_coverage(test_filename)

        # Assert
        assert "test_element" in coverage
        assert coverage["test_element"]["min_date"] == datetime.date(2025, 1, 1)
        assert coverage["test_element"]["max_date"] == datetime.date(2025, 1, 3)
        assert coverage["test_element"]["total_days"] == 3

        # Clean up
        os.remove(test_filename)

    def test_get_available_data_coverage_multiple_elements(self):
        """Test _get_available_data_coverage with multiple elements."""
        # Arrange
        test_filename = "test_coverage.parquet"
        test_data = pd.DataFrame(
            {
                "date": [
                    datetime.date(2025, 1, 1),
                    datetime.date(2025, 1, 1),
                    datetime.date(2025, 1, 2),
                    datetime.date(2025, 1, 2),
                    datetime.date(2025, 1, 3),
                    datetime.date(2025, 1, 3),
                ],
                "element_name": [
                    "element1",
                    "element2",
                    "element1",
                    "element2",
                    "element1",
                    "element2",
                ],
                "value": [100.0, 200.0, 150.0, 250.0, 300.0, 350.0],
            }
        )

        # Clean up any existing test file
        if os.path.exists(test_filename):
            os.remove(test_filename)

        test_data.to_parquet(test_filename, index=False)

        # Act
        coverage = self.service._get_available_data_coverage(test_filename)

        # Assert
        assert len(coverage) == 2
        assert "element1" in coverage
        assert "element2" in coverage

        assert coverage["element1"]["min_date"] == datetime.date(2025, 1, 1)
        assert coverage["element1"]["max_date"] == datetime.date(2025, 1, 3)
        assert coverage["element1"]["total_days"] == 3

        assert coverage["element2"]["min_date"] == datetime.date(2025, 1, 1)
        assert coverage["element2"]["max_date"] == datetime.date(2025, 1, 3)
        assert coverage["element2"]["total_days"] == 3

        # Clean up
        os.remove(test_filename)

    def test_get_missing_date_ranges_no_existing_data(self):
        """Test _get_missing_date_ranges when no data exists."""
        # Arrange
        test_filename = "test_missing_ranges.parquet"
        start_date = datetime.date(2025, 1, 1)
        end_date = datetime.date(2025, 1, 5)
        element_names = ["test_element"]

        # Clean up any existing test file
        if os.path.exists(test_filename):
            os.remove(test_filename)

        # Act
        missing_ranges = self.service._get_missing_date_ranges(
            start_date, end_date, element_names, test_filename
        )

        # Assert
        assert "test_element" in missing_ranges
        assert missing_ranges["test_element"] == [(start_date, end_date)]

    def test_get_missing_date_ranges_partial_coverage(self):
        """Test _get_missing_date_ranges with partial data coverage."""
        # Arrange
        test_filename = "test_missing_ranges.parquet"

        # Create test data with coverage from 2025-01-02 to 2025-01-04
        test_data = pd.DataFrame(
            {
                "date": [
                    datetime.date(2025, 1, 2),
                    datetime.date(2025, 1, 3),
                    datetime.date(2025, 1, 4),
                ],
                "element_name": ["test_element"] * 3,
                "value": [100.0, 200.0, 300.0],
            }
        )

        # Clean up any existing test file
        if os.path.exists(test_filename):
            os.remove(test_filename)

        test_data.to_parquet(test_filename, index=False)

        start_date = datetime.date(2025, 1, 1)
        end_date = datetime.date(2025, 1, 5)
        element_names = ["test_element"]

        # Act
        missing_ranges = self.service._get_missing_date_ranges(
            start_date, end_date, element_names, test_filename
        )

        # Assert
        assert "test_element" in missing_ranges
        ranges = missing_ranges["test_element"]
        assert len(ranges) == 2

        # Should need data before existing range
        assert ranges[0] == (datetime.date(2025, 1, 1), datetime.date(2025, 1, 1))

        # Should need data after existing range
        assert ranges[1] == (datetime.date(2025, 1, 5), datetime.date(2025, 1, 5))

        # Clean up
        os.remove(test_filename)

    def test_get_missing_date_ranges_full_coverage(self):
        """Test _get_missing_date_ranges when full coverage exists."""
        # Arrange
        test_filename = "test_missing_ranges.parquet"

        # Create test data with full coverage
        test_data = pd.DataFrame(
            {
                "date": [
                    datetime.date(2025, 1, 1),
                    datetime.date(2025, 1, 2),
                    datetime.date(2025, 1, 3),
                ],
                "element_name": ["test_element"] * 3,
                "value": [100.0, 200.0, 300.0],
            }
        )

        # Clean up any existing test file
        if os.path.exists(test_filename):
            os.remove(test_filename)

        test_data.to_parquet(test_filename, index=False)

        start_date = datetime.date(2025, 1, 1)
        end_date = datetime.date(2025, 1, 3)
        element_names = ["test_element"]

        # Act
        missing_ranges = self.service._get_missing_date_ranges(
            start_date, end_date, element_names, test_filename
        )

        # Assert
        assert "test_element" not in missing_ranges  # No missing ranges

        # Clean up
        os.remove(test_filename)

    def test_query_integrated_cfd_rate_empty_file(self):
        """Test _query_integrated_cfd_rate when file doesn't exist."""
        # Arrange
        test_filename = "nonexistent_file.parquet"
        start_date = datetime.date(2025, 1, 1)
        end_date = datetime.date(2025, 1, 5)

        # Act
        result = self.service._query_integrated_cfd_rate(
            start_date, end_date, filename=test_filename
        )

        # Assert
        assert len(result) == 0
        assert list(result.columns) == ["date", "element_name", "value"]

    def test_query_integrated_cfd_rate_date_range_filtering(self):
        """Test _query_integrated_cfd_rate with date range filtering."""
        # Arrange
        test_filename = "test_query.parquet"

        test_data = pd.DataFrame(
            {
                "date": [
                    datetime.date(2025, 1, 1),
                    datetime.date(2025, 1, 2),
                    datetime.date(2025, 1, 3),
                    datetime.date(2025, 1, 4),
                    datetime.date(2025, 1, 5),
                ],
                "element_name": ["test_element"] * 5,
                "value": [100.0, 200.0, 300.0, 400.0, 500.0],
            }
        )

        # Clean up any existing test file
        if os.path.exists(test_filename):
            os.remove(test_filename)

        test_data.to_parquet(test_filename, index=False)

        start_date = datetime.date(2025, 1, 2)
        end_date = datetime.date(2025, 1, 4)

        # Act
        result = self.service._query_integrated_cfd_rate(
            start_date, end_date, filename=test_filename
        )

        # Assert
        assert len(result) == 3
        assert result.iloc[0]["date"] == datetime.date(2025, 1, 2)
        assert result.iloc[1]["date"] == datetime.date(2025, 1, 3)
        assert result.iloc[2]["date"] == datetime.date(2025, 1, 4)

        # Clean up
        os.remove(test_filename)

    def test_query_integrated_cfd_rate_element_filtering(self):
        """Test _query_integrated_cfd_rate with element filtering."""
        # Arrange
        test_filename = "test_query.parquet"

        test_data = pd.DataFrame(
            {
                "date": [
                    datetime.date(2025, 1, 1),
                    datetime.date(2025, 1, 1),
                    datetime.date(2025, 1, 2),
                    datetime.date(2025, 1, 2),
                ],
                "element_name": ["element1", "element2", "element1", "element2"],
                "value": [100.0, 200.0, 300.0, 400.0],
            }
        )

        # Clean up any existing test file
        if os.path.exists(test_filename):
            os.remove(test_filename)

        test_data.to_parquet(test_filename, index=False)

        start_date = datetime.date(2025, 1, 1)
        end_date = datetime.date(2025, 1, 2)
        element_names = ["element1"]

        # Act
        result = self.service._query_integrated_cfd_rate(
            start_date, end_date, element_names, test_filename
        )

        # Assert
        assert len(result) == 2
        assert all(result["element_name"] == "element1")
        assert result.iloc[0]["value"] == 100.0
        assert result.iloc[1]["value"] == 300.0

        # Clean up
        os.remove(test_filename)

    def test_query_integrated_cfd_rate_no_matches(self):
        """Test _query_integrated_cfd_rate when no data matches the criteria."""
        # Arrange
        test_filename = "test_query.parquet"

        test_data = pd.DataFrame(
            {
                "date": [datetime.date(2025, 1, 1)],
                "element_name": ["test_element"],
                "value": [100.0],
            }
        )

        # Clean up any existing test file
        if os.path.exists(test_filename):
            os.remove(test_filename)

        test_data.to_parquet(test_filename, index=False)

        start_date = datetime.date(2025, 1, 5)  # Date not in data
        end_date = datetime.date(2025, 1, 10)

        # Act
        result = self.service._query_integrated_cfd_rate(
            start_date, end_date, filename=test_filename
        )

        # Assert
        assert len(result) == 0

        # Clean up
        os.remove(test_filename)
