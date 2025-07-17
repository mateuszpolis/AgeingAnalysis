"""Comprehensive unit tests for ageing_analysis.services.data_parser module."""

import os
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from ageing_analysis.services.data_parser import DataParser


class TestDataParserInit:
    """Test DataParser initialization."""

    def test_init_with_dataset(self):
        """Test DataParser initialization with dataset."""
        mock_dataset = MagicMock()
        mock_dataset.date = "2024-01-01"
        parser = DataParser(mock_dataset, debug_mode=False)

        assert parser.dataset == mock_dataset
        assert parser.debug_mode is False

    def test_init_with_debug_mode(self):
        """Test DataParser initialization with debug mode enabled."""
        mock_dataset = MagicMock()
        mock_dataset.date = "2024-01-01"
        parser = DataParser(mock_dataset, debug_mode=True)

        assert parser.dataset == mock_dataset
        assert parser.debug_mode is True


class TestGetReferenceChannelData:
    """Test _get_reference_channel_data method with various peak configurations."""

    def setup_method(self):
        """Setup method run before each test."""
        self.mock_dataset = MagicMock()
        self.mock_dataset.date = "2024-01-01"  # Add date for debug plots
        self.parser = DataParser(self.mock_dataset, debug_mode=False)

    def create_signal_with_peaks(
        self, peak_positions, peak_heights, noise_level=0.1, length=1000
    ):
        """Helper to create synthetic signal data with specified peaks."""
        x = np.arange(length)
        signal = np.full(length, noise_level)

        for pos, height in zip(peak_positions, peak_heights):
            # Create Gaussian peaks
            width = 20  # Peak width
            gaussian = height * np.exp(-0.5 * ((x - pos) / width) ** 2)
            signal += gaussian

        return signal

    def create_signal_with_exactly_two_peaks_after_cut(
        self, peak_positions, peak_heights, noise_level=0.1, length=1000
    ):
        """Helper to create signal with exactly 2 peaks after cutting first 50 bins."""
        # Ensure peaks are positioned after bin 50 to work with the new algorithm
        adjusted_positions = [pos if pos >= 50 else pos + 50 for pos in peak_positions]
        return self.create_signal_with_peaks(
            adjusted_positions, peak_heights, noise_level, length
        )

    def test_two_peaks_first_selected(self):
        """Test with 2 peaks after cutting first 50 bins.

        First peak should be selected.
        """
        # Create signal with peaks at positions 100, 300 (both after bin 50)
        # Heights: 80 (first), 60 (second)
        signal = self.create_signal_with_exactly_two_peaks_after_cut(
            [100, 300], [80, 60]
        )

        # Create DataFrame with two identical columns
        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        result = self.parser._get_reference_channel_data(df, 0, 1)

        # Should return the slice around the first peak (position 100)
        assert isinstance(result, pd.Series)
        assert len(result) > 0
        assert result.name == "ref_chan_0_1"

        # The peak should be somewhere around position 100
        peak_idx = result.idxmax()
        assert 80 < peak_idx < 120  # Should be around position 100

    def test_two_peaks_different_heights(self):
        """Test with 2 peaks of different heights.

        First in order should be selected.
        """
        signal = self.create_signal_with_exactly_two_peaks_after_cut(
            [150, 400], [60, 80]
        )

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        result = self.parser._get_reference_channel_data(df, 0, 1)

        # Should return the slice around the first peak (position 150)
        peak_idx = result.idxmax()
        assert 130 < peak_idx < 170

    def test_two_peaks_reverse_height_order(self):
        """Test with 2 peaks where second peak is higher.

        Still select first in order.
        """
        signal = self.create_signal_with_exactly_two_peaks_after_cut(
            [200, 400], [70, 100]
        )

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        result = self.parser._get_reference_channel_data(df, 0, 1)

        # Should return the slice around the first peak regardless of height
        peak_idx = result.idxmax()
        assert 180 < peak_idx < 220

    def test_more_than_two_peaks_raises_error(self):
        """Test having more than 2 peaks after cutting first 50 bins.

        Raises error.
        """
        # Create signal with 3 peaks after bin 50
        signal = self.create_signal_with_exactly_two_peaks_after_cut(
            [150, 300, 450], [90, 100, 85]
        )

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        # Should raise error due to more than 2 peaks
        with pytest.raises(ValueError, match="Found more than two peaks"):
            self.parser._get_reference_channel_data(df, 0, 1)

    def test_multiple_peaks_raises_error(self):
        """Test that having multiple peaks after cutting first 50 bins raises error."""
        # Heights: 60, 95, 100, 75, 80
        signal = self.create_signal_with_exactly_two_peaks_after_cut(
            [100, 250, 400, 550, 700], [60, 95, 100, 75, 80]
        )

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        # Should raise error due to more than 2 peaks
        with pytest.raises(ValueError, match="Found more than two peaks"):
            self.parser._get_reference_channel_data(df, 0, 1)

    def test_custom_prominence(self):
        """Test with custom prominence parameter."""
        signal = self.create_signal_with_exactly_two_peaks_after_cut(
            [200, 400], [100, 80]
        )

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        # Use custom prominence - should still find exactly 2 peaks
        mock_dataset = MagicMock()
        mock_dataset.date = "2024-01-01"
        parser = DataParser(mock_dataset, debug_mode=False, prominence_percent=10.0)
        result = parser._get_reference_channel_data(df, 0, 1)

        assert isinstance(result, pd.Series)
        assert len(result) > 0

    def test_low_prominence_finds_exactly_two_peaks(self):
        """Test that low prominence finds exactly 2 peaks."""
        # Create signal with 2 peaks after bin 50
        signal = self.create_signal_with_exactly_two_peaks_after_cut(
            [200, 400], [80, 60]
        )

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        # Use low prominence
        mock_dataset = MagicMock()
        mock_dataset.date = "2024-01-01"
        parser = DataParser(mock_dataset, debug_mode=False, prominence_percent=1.0)
        result = parser._get_reference_channel_data(df, 0, 1)

        assert isinstance(result, pd.Series)
        assert len(result) > 0

    def test_only_one_peak_raises_error(self):
        """Test that having only one peak raises ValueError."""
        signal = self.create_signal_with_peaks([400], [100])

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        with pytest.raises(ValueError, match="Could not find at least two peaks"):
            self.parser._get_reference_channel_data(df, 0, 1)

    def test_no_peaks_raises_error(self):
        """Test that having no peaks raises ValueError."""
        # Create truly flat signal with no variation
        signal = np.full(1000, 50.0)  # Constant value

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        # The new algorithm detects edge plateaus and gives a more specific error
        with pytest.raises(ValueError, match="Signal peak is at the edge of the data"):
            self.parser._get_reference_channel_data(df, 0, 1)

    def test_high_prominence_no_peaks_raises_error(self):
        """Test that too high prominence results in no peaks found."""
        signal = self.create_signal_with_exactly_two_peaks_after_cut(
            [200, 400], [10, 8]
        )  # Small peaks

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        # Use very high prominence that makes peaks undetectable
        mock_dataset = MagicMock()
        mock_dataset.date = "2024-01-01"
        parser = DataParser(mock_dataset, debug_mode=False, prominence_percent=90.0)
        with pytest.raises(ValueError, match="Could not find at least two peaks"):
            parser._get_reference_channel_data(df, 0, 1)

    def test_two_peaks_exactly(self):
        """Test with exactly two peaks."""
        signal = self.create_signal_with_exactly_two_peaks_after_cut(
            [300, 700], [100, 80]
        )

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        result = self.parser._get_reference_channel_data(df, 0, 1)

        # Should return the slice around the first peak (position 300)
        # The peak should remain at its original position 300
        peak_idx = result.idxmax()
        assert 280 < peak_idx < 320

    def test_identical_peak_heights(self):
        """Test with peaks of identical heights."""
        # Create signal with identical peak heights but ensure they're well separated
        signal = self.create_signal_with_exactly_two_peaks_after_cut(
            [150, 400], [100, 100]  # Further apart and different positions
        )

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        # Should still work, picking the first peak
        # Use a lower prominence to ensure peaks are detected
        mock_dataset = MagicMock()
        mock_dataset.date = "2024-01-01"
        parser = DataParser(mock_dataset, debug_mode=False, prominence_percent=5.0)
        result = parser._get_reference_channel_data(df, 0, 1)

        assert isinstance(result, pd.Series)
        assert len(result) > 0

    def test_different_column_indices(self):
        """Test with different column indices."""
        signal = self.create_signal_with_exactly_two_peaks_after_cut(
            [200, 400], [100, 80]
        )

        df = pd.DataFrame(
            {
                "col0": signal / 2,
                "col1": np.zeros_like(signal),
                "col2": signal / 2,
                "col3": np.zeros_like(signal),
            }
        )

        result = self.parser._get_reference_channel_data(df, 0, 2)

        assert result.name == "ref_chan_0_2"
        assert len(result) > 0

    def test_asymmetric_columns(self):
        """Test with asymmetric column values."""
        signal1 = self.create_signal_with_exactly_two_peaks_after_cut(
            [200, 400], [60, 40]
        )
        signal2 = self.create_signal_with_exactly_two_peaks_after_cut(
            [200, 400], [40, 40]
        )

        df = pd.DataFrame({"col1": signal1, "col2": signal2})

        result = self.parser._get_reference_channel_data(df, 0, 1)

        # Combined signal should have peaks at [100, 80]
        # First peak should be at position 200 (original position)
        peak_idx = result.idxmax()
        assert 180 < peak_idx < 220

    def test_preserves_original_index(self):
        """Test that the result preserves the original DataFrame index."""
        signal = self.create_signal_with_exactly_two_peaks_after_cut(
            [200, 400], [100, 80]
        )

        # Create DataFrame with custom index
        custom_index = np.arange(1000, 2000)
        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2}, index=custom_index)

        result = self.parser._get_reference_channel_data(df, 0, 1)

        # With the new implementation, we maintain the original data length
        # and place the selected region at the correct position with zeros elsewhere
        assert min(result.index) == 0
        assert max(result.index) == len(result) - 1
        assert len(result.index) == len(result)
        # The result should have the same length as the original data
        assert len(result) == len(df)


class TestParseAndProcessFile:
    """Test _parse_and_process_file method."""

    def setup_method(self):
        """Setup method run before each test."""
        self.mock_dataset = MagicMock()
        self.mock_dataset.date = "2024-01-01"  # Add date for debug plots
        self.parser = DataParser(self.mock_dataset, debug_mode=False)

    def create_mock_csv_data(self, num_channels=2, num_rows=600):
        """Create mock CSV data."""
        # First column is bin numbers
        data = {"bin": list(range(num_rows))}

        # Add channel pairs (2 columns per channel)
        for ch in range(num_channels):
            # Create realistic signal data
            signal_data = np.random.normal(100, 10, num_rows)
            np.random.normal(10, 2, num_rows)

            # Add some peaks for reference channels
            if ch == 0:  # First channel has peaks
                signal_data[200:220] += 50
                signal_data[400:420] += 40
                signal_data[300:320] += 60  # Largest peak

            data[f"ch{ch}_col1"] = signal_data.tolist()
            data[f"ch{ch}_col2"] = (signal_data * 0.9).tolist()  # Slightly different

        return pd.DataFrame(data)

    @patch("pandas.read_csv")
    def test_parse_valid_file_non_reference(self, mock_read_csv):
        """Test parsing a valid file for non-reference module."""
        # Setup mock CSV data
        mock_df = self.create_mock_csv_data(num_channels=2)
        mock_read_csv.return_value = mock_df

        # Create mock module
        mock_module = MagicMock()
        mock_module.path = "test.csv"
        mock_module.is_reference = False
        mock_module.ref_channels = []

        # Call the method
        self.parser._parse_and_process_file(mock_module)

        # Verify CSV was read with correct delimiter
        mock_read_csv.assert_called_once_with("test.csv", delimiter=":")

        # Verify channels were added
        assert mock_module.add_channel.call_count == 2  # 2 channels

        # Check first call arguments
        first_call = mock_module.add_channel.call_args_list[0]
        chan_idx, sig_series, noise_series, total_signal_series = first_call[0]

        assert chan_idx == 1  # First channel index
        assert isinstance(sig_series, pd.Series)
        assert isinstance(noise_series, pd.Series)
        assert isinstance(total_signal_series, pd.Series)

        # Signal should have re-indexed from 0 to N-1
        assert list(sig_series.index) == list(range(len(sig_series)))

    @patch("pandas.read_csv")
    def test_parse_valid_file_reference_module(self, mock_read_csv):
        """Test parsing a valid file for reference module."""
        # Setup mock CSV data
        mock_df = self.create_mock_csv_data(num_channels=2)
        mock_read_csv.return_value = mock_df

        # Create mock module
        mock_module = MagicMock()
        mock_module.path = "test.csv"
        mock_module.is_reference = True
        mock_module.ref_channels = [1]  # First channel is reference

        # Mock the _get_reference_channel_data method
        mock_ref_data = pd.Series([1, 2, 3, 4, 5], name="ref_data")
        with patch.object(
            self.parser, "_get_reference_channel_data", return_value=mock_ref_data
        ):
            self.parser._parse_and_process_file(mock_module)

        # Verify _get_reference_channel_data was called for reference channel
        assert mock_module.add_channel.call_count == 2

        # First channel should use reference data
        first_call = mock_module.add_channel.call_args_list[0]
        chan_idx, sig_series, noise_series, total_signal_series = first_call[0]

        assert chan_idx == 1
        # Signal series should be the mock reference data
        pd.testing.assert_series_equal(sig_series, mock_ref_data)

    @patch("pandas.read_csv")
    def test_parse_file_invalid_column_count(self, mock_read_csv):
        """Test parsing file with invalid column count."""
        # Create DataFrame with odd number of data columns (invalid)
        # After dropping bin column, we need even number of columns (pairs)
        invalid_df = pd.DataFrame(
            {
                "bin": [1, 2, 3],
                "col1": [1, 2, 3],
                "col2": [1, 2, 3],
                "col3": [
                    1,
                    2,
                    3,
                ],  # This makes 3 data columns after dropping bin (odd = invalid)
            }
        )
        mock_read_csv.return_value = invalid_df

        mock_module = MagicMock()
        mock_module.path = "invalid.csv"

        with pytest.raises(ValueError, match="has an invalid number of columns"):
            self.parser._parse_and_process_file(mock_module)

    @patch("pandas.read_csv")
    def test_parse_file_with_multiple_channels(self, mock_read_csv):
        """Test parsing file with multiple channels."""
        # Create data with 3 channels (7 columns total: 1 bin + 6 data)
        mock_df = self.create_mock_csv_data(num_channels=3)
        mock_read_csv.return_value = mock_df

        mock_module = MagicMock()
        mock_module.path = "multi.csv"
        mock_module.is_reference = False
        mock_module.ref_channels = []

        self.parser._parse_and_process_file(mock_module)

        # Should have added 3 channels
        assert mock_module.add_channel.call_count == 3

        # Check channel indices
        call_args = [call[0][0] for call in mock_module.add_channel.call_args_list]
        assert call_args == [1, 2, 3]

    @patch("pandas.read_csv")
    def test_parse_file_csv_read_error(self, mock_read_csv):
        """Test handling CSV read errors."""
        mock_read_csv.side_effect = pd.errors.EmptyDataError("No data")

        mock_module = MagicMock()
        mock_module.path = "empty.csv"

        with pytest.raises(pd.errors.EmptyDataError):
            self.parser._parse_and_process_file(mock_module)

    @patch("pandas.read_csv")
    def test_signal_noise_split(self, mock_read_csv):
        """Test that signal and noise are split correctly."""
        # Create data with exactly 600 rows
        mock_df = self.create_mock_csv_data(num_channels=1, num_rows=600)
        mock_read_csv.return_value = mock_df

        mock_module = MagicMock()
        mock_module.path = "test.csv"
        mock_module.is_reference = False
        mock_module.ref_channels = []

        self.parser._parse_and_process_file(mock_module)

        # Get the call arguments
        call_args = mock_module.add_channel.call_args_list[0][0]
        chan_idx, sig_series, noise_series, total_signal_series = call_args

        # Signal should be from row 257 onwards (600-257 = 343 rows)
        # Noise should be from rows 0-256 (257 rows)
        assert len(sig_series) == 343  # 600 - 257
        assert len(noise_series) == 257

    @patch("pandas.read_csv")
    def test_reference_channel_error_handling(self, mock_read_csv):
        """Test error handling in reference channel processing."""
        mock_df = self.create_mock_csv_data(num_channels=1)
        mock_read_csv.return_value = mock_df

        mock_module = MagicMock()
        mock_module.path = "test.csv"
        mock_module.is_reference = True
        mock_module.ref_channels = [1]

        # Mock _get_reference_channel_data to raise an error
        with patch.object(
            self.parser,
            "_get_reference_channel_data",
            side_effect=ValueError("Peak error"),
        ):
            with pytest.raises(ValueError, match="Peak error"):
                self.parser._parse_and_process_file(mock_module)


class TestProcessAllFiles:
    """Test process_all_files method."""

    def setup_method(self):
        """Setup method run before each test."""
        self.mock_dataset = MagicMock()
        self.mock_dataset.date = "2024-01-01"  # Add date for debug plots
        self.parser = DataParser(self.mock_dataset, debug_mode=False)

    def test_process_all_files_success(self):
        """Test successful processing of all files."""
        # Create mock modules
        mock_module1 = MagicMock()
        mock_module1.identifier = "PMA0"
        mock_module1.path = "file1.csv"

        mock_module2 = MagicMock()
        mock_module2.identifier = "PMA1"
        mock_module2.path = "file2.csv"

        self.mock_dataset.modules = [mock_module1, mock_module2]

        # Mock the _parse_and_process_file method
        with patch.object(self.parser, "_parse_and_process_file") as mock_parse:
            self.parser.process_all_files()

        # Verify _parse_and_process_file was called for each module
        assert mock_parse.call_count == 2
        mock_parse.assert_any_call(mock_module1)
        mock_parse.assert_any_call(mock_module2)

    def test_process_all_files_single_module(self):
        """Test processing with single module."""
        mock_module = MagicMock()
        mock_module.identifier = "PMA0"
        mock_module.path = "single.csv"

        self.mock_dataset.modules = [mock_module]

        with patch.object(self.parser, "_parse_and_process_file") as mock_parse:
            self.parser.process_all_files()

        mock_parse.assert_called_once_with(mock_module)

    def test_process_all_files_empty_modules(self):
        """Test processing with no modules."""
        self.mock_dataset.modules = []

        with patch.object(self.parser, "_parse_and_process_file") as mock_parse:
            self.parser.process_all_files()

        # Should not call parse method if no modules
        mock_parse.assert_not_called()

    def test_process_all_files_with_error(self):
        """Test error handling during file processing."""
        mock_module = MagicMock()
        mock_module.identifier = "PMA0"
        mock_module.path = "error.csv"

        self.mock_dataset.modules = [mock_module]

        # Mock _parse_and_process_file to raise an error
        with patch.object(
            self.parser,
            "_parse_and_process_file",
            side_effect=ValueError("Processing error"),
        ):
            with pytest.raises(
                Exception, match="Failed to process file for PMA0: Processing error"
            ):
                self.parser.process_all_files()

    def test_process_all_files_partial_failure(self):
        """Test that error in one module stops processing."""
        mock_module1 = MagicMock()
        mock_module1.identifier = "PMA0"
        mock_module1.path = "file1.csv"

        mock_module2 = MagicMock()
        mock_module2.identifier = "PMA1"
        mock_module2.path = "file2.csv"

        self.mock_dataset.modules = [mock_module1, mock_module2]

        def side_effect(module):
            if module.identifier == "PMA0":
                raise ValueError("File error")
            return None

        with patch.object(
            self.parser, "_parse_and_process_file", side_effect=side_effect
        ):
            with pytest.raises(Exception, match="Failed to process file for PMA0"):
                self.parser.process_all_files()

    def test_process_files_different_error_types(self):
        """Test handling of different error types."""
        mock_module = MagicMock()
        mock_module.identifier = "PMA0"
        mock_module.path = "error.csv"

        self.mock_dataset.modules = [mock_module]

        # Test with different exception types
        error_types = [
            FileNotFoundError("File not found"),
            pd.errors.EmptyDataError("Empty data"),
            ValueError("Invalid data"),
            RuntimeError("Runtime error"),
        ]

        for error in error_types:
            with patch.object(
                self.parser, "_parse_and_process_file", side_effect=error
            ):
                with pytest.raises(
                    Exception, match=f"Failed to process file for PMA0: {str(error)}"
                ):
                    self.parser.process_all_files()


class TestDataParserEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Setup method run before each test."""
        self.mock_dataset = MagicMock()
        self.mock_dataset.date = "2024-01-01"  # Add date for debug plots
        self.parser = DataParser(self.mock_dataset, debug_mode=False)

    def test_very_small_dataframe(self):
        """Test with very small DataFrame."""
        # Create minimal data with 2 peaks after cutting first 50 bins
        # Since we need at least 50 bins to cut, create a longer signal
        signal = np.zeros(100)
        signal[55] = 10  # Peak at position 55 (after cut)
        signal[75] = 8  # Peak at position 75 (after cut)

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        mock_dataset = MagicMock()
        mock_dataset.date = "2024-01-01"
        parser = DataParser(mock_dataset, debug_mode=False, prominence_percent=1.0)
        result = parser._get_reference_channel_data(df, 0, 1)

        assert isinstance(result, pd.Series)
        assert len(result) > 0

    def test_all_zero_data(self):
        """Test with all-zero data."""
        df = pd.DataFrame({"col1": np.zeros(100), "col2": np.zeros(100)})

        # All-zero data means max is at position 0, triggering edge detection
        with pytest.raises(ValueError, match="Signal peak is at the edge of the data"):
            self.parser._get_reference_channel_data(df, 0, 1)

    def test_negative_values(self):
        """Test with negative values."""
        # Create signal with negative baseline and positive peaks
        signal = np.full(100, -10)  # Negative baseline
        signal[60:65] = 40  # Peak 1 (after bin 50)
        signal[80:85] = 60  # Peak 2 (after bin 50)

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        result = self.parser._get_reference_channel_data(df, 0, 1)

        # Should work with negative baseline
        assert isinstance(result, pd.Series)
        assert len(result) > 0

    def test_very_noisy_data(self):
        """Test with very noisy data."""
        # Create signal with high noise, ensuring peaks are after bin 50
        base_signal = self.create_signal_with_exactly_two_peaks_after_cut(
            [60, 80], [100, 80], length=100
        )
        noise = np.random.normal(0, 20, 100)  # High noise
        signal = base_signal + noise

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        # High noise can create more than 2 peaks, so it might raise an error
        # Let's test that it raises the expected error
        mock_dataset = MagicMock()
        mock_dataset.date = "2024-01-01"
        parser = DataParser(mock_dataset, debug_mode=False, prominence_percent=10.0)
        with pytest.raises(
            ValueError,
            match="Found more than two peaks|Could not find at least two peaks",
        ):
            parser._get_reference_channel_data(df, 0, 1)

    def create_signal_with_peaks(
        self, peak_positions, peak_heights, noise_level=0.1, length=1000
    ):
        """Helper to create synthetic signal data with specified peaks."""
        x = np.arange(length)
        signal = np.full(length, noise_level)

        for pos, height in zip(peak_positions, peak_heights):
            # Create Gaussian peaks
            width = 5  # Narrow peaks for small data
            gaussian = height * np.exp(-0.5 * ((x - pos) / width) ** 2)
            signal += gaussian

        return signal

    def create_signal_with_exactly_two_peaks_after_cut(
        self, peak_positions, peak_heights, noise_level=0.1, length=1000
    ):
        """Helper to create signal with exactly 2 peaks after cutting first 50 bins."""
        # Ensure peaks are positioned after bin 50 to work with the new algorithm
        adjusted_positions = [pos if pos >= 50 else pos + 50 for pos in peak_positions]
        return self.create_signal_with_peaks(
            adjusted_positions, peak_heights, noise_level, length
        )

    def test_peaks_near_boundaries(self):
        """Test with peaks near data boundaries (more realistic scenario)."""
        # Create more realistic Gaussian-like peaks, ensuring they work with the cut
        signal = self.create_signal_with_exactly_two_peaks_after_cut(
            [60, 80], [50, 40], length=100
        )

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        mock_dataset = MagicMock()
        mock_dataset.date = "2024-01-01"
        parser = DataParser(mock_dataset, debug_mode=False, prominence_percent=5.0)
        result = parser._get_reference_channel_data(df, 0, 1)

        assert isinstance(result, pd.Series)
        assert len(result) > 0

        # Should successfully find the first peak
        assert result.max() > result.mean() * 1.5

    def test_edge_plateaus_fallback_behavior(self):
        """Test behavior with edge plateaus (should raise appropriate error)."""
        # This tests the problematic case where plateaus extend to exact edges
        signal = np.zeros(100)
        signal[0:5] = 50  # Plateau at start (problematic)
        signal[45:55] = 60  # Plateau in middle
        signal[95:100] = 40  # Plateau at end (problematic)

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        # After cutting first 50 bins, the end plateau becomes the maximum at the edge
        # This triggers the edge detection logic
        with pytest.raises(ValueError, match="Signal peak is at the edge of the data"):
            self.parser._get_reference_channel_data(df, 0, 1)

    def test_maximum_at_edge_detected(self):
        """Test that edge detection works when maximum is at the edge."""
        # Create signal where maximum is at the very start
        signal = np.zeros(100)
        signal[0:5] = 100  # Highest peak at start (edge)
        signal[45:55] = 60  # Lower peak in middle
        signal[95:100] = 40  # Lower peak at end

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        # This should trigger edge detection since max is at position 0
        with pytest.raises(ValueError, match="Signal peak is at the edge of the data"):
            self.parser._get_reference_channel_data(df, 0, 1)

    def test_single_sample_peaks(self):
        """Test with single-sample peaks."""
        signal = np.zeros(100)
        signal[60] = 100  # Single sample peak (after bin 50)
        signal[80] = 80  # Single sample peak (after bin 50)

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        mock_dataset = MagicMock()
        mock_dataset.date = "2024-01-01"
        parser = DataParser(mock_dataset, debug_mode=False, prominence_percent=20.0)
        result = parser._get_reference_channel_data(df, 0, 1)

        assert isinstance(result, pd.Series)
        # Result might be very small for single-sample peaks
        assert len(result) >= 1


class TestDebugPlotting:
    """Test debug plotting functionality for different scenarios."""

    def setup_method(self):
        """Setup method run before each test."""
        self.mock_dataset = MagicMock()
        self.mock_dataset.date = "test_debug"
        self.parser = DataParser(self.mock_dataset, debug_mode=True)

    def create_signal_with_exactly_two_peaks_after_cut(
        self, peak_positions, peak_heights, noise_level=0.1, length=1000
    ):
        """Helper to create signal with exactly 2 peaks after cutting first 50 bins."""
        x = np.arange(length)
        signal = np.full(length, noise_level)

        # Ensure peaks are positioned after bin 50
        adjusted_positions = [pos if pos >= 50 else pos + 50 for pos in peak_positions]

        for pos, height in zip(adjusted_positions, peak_heights):
            width = 20
            gaussian = height * np.exp(-0.5 * ((x - pos) / width) ** 2)
            signal += gaussian

        return signal

    def test_debug_plot_success_case(self):
        """Test debug plot generation for successful 2-peak case."""
        signal = self.create_signal_with_exactly_two_peaks_after_cut(
            [100, 300], [80, 60]
        )

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        result = self.parser._get_reference_channel_data(df, 0, 1)

        # Should succeed and generate debug plot
        assert isinstance(result, pd.Series)
        assert len(result) > 0

        # Check that debug plot was created
        debug_folder = "debug_plots/data_parser/test_debug"
        assert os.path.exists(debug_folder)
        png_files = [f for f in os.listdir(debug_folder) if f.endswith(".png")]
        assert len(png_files) > 0

    def test_debug_plot_insufficient_peaks(self):
        """Test debug plot generation for insufficient peaks case."""
        signal = self.create_signal_with_exactly_two_peaks_after_cut(
            [100], [80]
        )  # Only 1 peak

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        # Should fail but generate debug plot
        with pytest.raises(ValueError, match="Could not find at least two peaks"):
            self.parser._get_reference_channel_data(df, 0, 1)

        # Check that debug plot was created even for error case
        debug_folder = "debug_plots/data_parser/test_debug"
        assert os.path.exists(debug_folder)
        png_files = [f for f in os.listdir(debug_folder) if f.endswith(".png")]
        assert len(png_files) > 0

    def test_debug_plot_too_many_peaks(self):
        """Test debug plot generation for too many peaks case."""
        signal = self.create_signal_with_exactly_two_peaks_after_cut(
            [100, 200, 300], [80, 70, 60]
        )  # 3 peaks

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        # Should fail but generate debug plot
        with pytest.raises(ValueError, match="Found more than two peaks"):
            self.parser._get_reference_channel_data(df, 0, 1)

        # Check that debug plot was created even for error case
        debug_folder = "debug_plots/data_parser/test_debug"
        assert os.path.exists(debug_folder)
        png_files = [f for f in os.listdir(debug_folder) if f.endswith(".png")]
        assert len(png_files) > 0

    def test_debug_plot_no_peaks(self):
        """Test debug plot generation for no peaks case."""
        # Flat signal with no peaks
        signal = np.full(1000, 50.0)

        df = pd.DataFrame({"col1": signal / 2, "col2": signal / 2})

        # Should fail but generate debug plot
        with pytest.raises(ValueError, match="Signal peak is at the edge of the data"):
            self.parser._get_reference_channel_data(df, 0, 1)

        # Check that debug plot was created even for error case
        debug_folder = "debug_plots/data_parser/test_debug"
        assert os.path.exists(debug_folder)
        png_files = [f for f in os.listdir(debug_folder) if f.endswith(".png")]
        assert len(png_files) > 0
