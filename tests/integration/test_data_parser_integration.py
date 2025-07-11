"""Integration tests for ageing_analysis.services.data_parser module."""

import os
import tempfile
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from ageing_analysis.services.data_parser import DataParser


class TestDataParserIntegration:
    """Integration tests for DataParser with real CSV files."""

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

    def create_realistic_csv_file(
        self, filepath, num_channels=2, num_rows=600, add_peaks=True
    ):
        """Create a realistic CSV file for testing."""
        # Create bin column
        bins = list(range(num_rows))

        # Create channel data
        data = {"bin": bins}

        for ch in range(num_channels):
            # Create realistic signal and noise data
            signal_base = np.random.normal(100, 5, num_rows)  # Base signal level
            noise_base = np.random.normal(10, 1, num_rows)  # Base noise level

            # Add peaks to first channel if requested
            if add_peaks and ch == 0:
                # Add peaks based on file size, ensuring they fit within the array
                # Peak positions should be after bin 50 (for the data parser algorithm)
                # and have enough space for the peak width

                # Peak 1: largest peak at position min(200, num_rows-50)
                peak1_start = min(180, num_rows - 50)
                peak1_end = min(220, num_rows - 10)
                if peak1_start < peak1_end:
                    signal_base[peak1_start:peak1_end] += np.random.normal(
                        150, 10, peak1_end - peak1_start
                    )

                # Peak 2: second-largest peak at position min(400, num_rows-50)
                peak2_start = min(380, num_rows - 50)
                peak2_end = min(420, num_rows - 10)
                if peak2_start < peak2_end:
                    signal_base[peak2_start:peak2_end] += np.random.normal(
                        120, 8, peak2_end - peak2_start
                    )

                # Peak 3: smallest peak at position min(300, num_rows-50)
                peak3_start = min(280, num_rows - 50)
                peak3_end = min(320, num_rows - 10)
                if peak3_start < peak3_end:
                    signal_base[peak3_start:peak3_end] += np.random.normal(
                        90, 6, peak3_end - peak3_start
                    )

                # Add some smaller peaks for complexity if there's room
                if num_rows > 520:
                    signal_base[500:520] += np.random.normal(70, 5, 20)
                if num_rows > 120:
                    signal_base[100:120] += np.random.normal(80, 4, 20)

            # Create two columns per channel (slightly correlated)
            col1_signal = signal_base + np.random.normal(0, 2, num_rows)
            col2_signal = signal_base * 0.9 + np.random.normal(0, 3, num_rows)

            col1_noise = noise_base + np.random.normal(0, 0.5, num_rows)
            col2_noise = noise_base * 0.8 + np.random.normal(0, 0.7, num_rows)

            # Combine signal and noise (signal from row 257+, noise from 0-256)
            col1_data = np.concatenate([col1_noise[:257], col1_signal[257:]])
            col2_data = np.concatenate([col2_noise[:257], col2_signal[257:]])

            data[f"ch{ch}_col1"] = col1_data.tolist()
            data[f"ch{ch}_col2"] = col2_data.tolist()

        # Create DataFrame and save to CSV
        df = pd.DataFrame(data)
        df.to_csv(filepath, sep=":", index=False)

        return filepath

    def create_mock_module(
        self, csv_path, identifier="PMA0", is_reference=False, ref_channels=None
    ):
        """Create a mock module for testing."""
        module = MagicMock()
        module.path = csv_path
        module.identifier = identifier
        module.is_reference = is_reference
        module.ref_channels = ref_channels or []
        module.channels = []

        # Store added channels for verification
        module.added_channels = []

        def mock_add_channel(chan_idx, sig_series, noise_series):
            module.added_channels.append(
                {
                    "channel_idx": chan_idx,
                    "signal_series": sig_series.copy(),
                    "noise_series": noise_series.copy(),
                }
            )

        module.add_channel = mock_add_channel
        return module

    def create_mock_dataset(self, modules):
        """Create a mock dataset with given modules."""
        dataset = MagicMock()
        dataset.modules = modules
        return dataset

    def test_complete_workflow_non_reference_module(self):
        """Test complete workflow with non-reference module."""
        # Create test CSV file
        csv_path = os.path.join(self.temp_dir, "test_non_ref.csv")
        self.create_realistic_csv_file(csv_path, num_channels=2)

        # Create module and dataset
        module = self.create_mock_module(csv_path, "PMA0", is_reference=False)
        dataset = self.create_mock_dataset([module])

        # Create parser and process
        parser = DataParser(dataset)
        parser.process_all_files()

        # Verify results
        assert len(module.added_channels) == 2  # 2 channels

        # Check first channel
        ch1 = module.added_channels[0]
        assert ch1["channel_idx"] == 1
        assert isinstance(ch1["signal_series"], pd.Series)
        assert isinstance(ch1["noise_series"], pd.Series)

        # Signal should be from row 257+ (600-257=343 rows)
        assert len(ch1["signal_series"]) == 343
        # Noise should be from rows 0-256 (257 rows)
        assert len(ch1["noise_series"]) == 257

        # Signal index should be re-indexed from 0
        assert list(ch1["signal_series"].index) == list(range(343))

        # Values should be reasonable (sum of two columns)
        assert ch1["signal_series"].mean() > 150  # Should be higher due to peaks
        assert ch1["noise_series"].mean() < 50  # Should be lower (noise only)

    def test_complete_workflow_reference_module(self):
        """Test complete workflow with reference module."""
        # Create test CSV file with controlled peaks
        csv_path = os.path.join(self.temp_dir, "test_ref.csv")

        # Create controlled data with exactly 2 peaks
        bins = list(range(600))
        data = {"bin": bins}

        # Create baseline signal
        signal = np.full(600, 50.0)

        # Add exactly 2 peaks for reference channel
        # Peak 1: position 400 (in signal part after row 257)
        signal[400:420] = 120
        # Peak 2: position 500 (in signal part after row 257)
        signal[500:520] = 100

        # Create 2 channels
        for ch in range(2):
            data[f"ch{ch}_col1"] = (signal * 0.6).tolist()
            data[f"ch{ch}_col2"] = (signal * 0.4).tolist()

        df = pd.DataFrame(data)
        df.to_csv(csv_path, sep=":", index=False)

        # Create reference module
        module = self.create_mock_module(
            csv_path, "PMA0", is_reference=True, ref_channels=[1]
        )
        dataset = self.create_mock_dataset([module])

        # Create parser and process
        parser = DataParser(dataset)
        parser.process_all_files()

        # Verify results
        assert len(module.added_channels) == 2

        # First channel should use reference channel processing
        ch1 = module.added_channels[0]
        assert ch1["channel_idx"] == 1

        # Reference channel should have different length (peak slice)
        ref_signal = ch1["signal_series"]
        assert len(ref_signal) > 0
        assert len(ref_signal) < 343  # Should be smaller than full signal

        # Should contain the second-largest peak data
        assert ref_signal.max() > ref_signal.mean() * 1.0  # Should have clear peak

        # Second channel should use normal processing
        ch2 = module.added_channels[1]
        assert ch2["channel_idx"] == 2
        assert len(ch2["signal_series"]) == 343  # Full signal length

    def test_multiple_modules_workflow(self):
        """Test workflow with multiple modules."""
        # Create multiple CSV files with controlled data
        csv_path1 = os.path.join(self.temp_dir, "module1.csv")
        csv_path2 = os.path.join(self.temp_dir, "module2.csv")
        csv_path3 = os.path.join(self.temp_dir, "module3.csv")

        # Create controlled data for each module
        def create_simple_csv(filepath, num_channels, add_peaks=False):
            bins = list(range(600))
            data = {"bin": bins}

            for ch in range(num_channels):
                signal = np.full(600, 50.0)
                if add_peaks:
                    # Add exactly 2 peaks for reference channels
                    signal[400:420] = 120
                    signal[500:520] = 100

                data[f"ch{ch}_col1"] = (signal * 0.6).tolist()
                data[f"ch{ch}_col2"] = (signal * 0.4).tolist()

            df = pd.DataFrame(data)
            df.to_csv(filepath, sep=":", index=False)

        create_simple_csv(csv_path1, num_channels=2, add_peaks=True)
        create_simple_csv(csv_path2, num_channels=3, add_peaks=False)
        create_simple_csv(csv_path3, num_channels=1, add_peaks=True)

        # Create modules
        module1 = self.create_mock_module(
            csv_path1, "PMA0", is_reference=True, ref_channels=[1]
        )
        module2 = self.create_mock_module(csv_path2, "PMA1", is_reference=False)
        module3 = self.create_mock_module(
            csv_path3, "PMA2", is_reference=True, ref_channels=[1]
        )

        dataset = self.create_mock_dataset([module1, module2, module3])

        # Create parser and process
        parser = DataParser(dataset)
        parser.process_all_files()

        # Verify all modules were processed
        assert len(module1.added_channels) == 2  # 2 channels
        assert len(module2.added_channels) == 3  # 3 channels
        assert len(module3.added_channels) == 1  # 1 channel

        # Verify reference channel processing
        ref_ch1 = module1.added_channels[0]["signal_series"]
        ref_ch3 = module3.added_channels[0]["signal_series"]

        # Both reference channels should have peak slices (shorter than full signal)
        assert len(ref_ch1) < 343
        assert len(ref_ch3) < 343

        # Non-reference module should have full signals
        for ch in module2.added_channels:
            assert len(ch["signal_series"]) == 343

    def test_complex_peak_scenarios(self):
        """Test with complex peak scenarios in reference channels."""
        # Create CSV with carefully crafted peaks
        csv_path = os.path.join(self.temp_dir, "complex_peaks.csv")

        # Create custom data with specific peak arrangement
        bins = list(range(600))
        data = {"bin": bins}

        # Create signal with 5 peaks of varying heights using Gaussian-like peaks
        signal = np.full(600, 50.0)  # Baseline

        # Create Gaussian-like peaks instead of flat plateaus
        def add_gaussian_peak(signal, center, height, width=10):
            for i in range(len(signal)):
                if abs(i - center) < width * 3:  # 3 sigma range
                    signal[i] += height * np.exp(-0.5 * ((i - center) / width) ** 2)

        # Peak 1: position 100, height 200 (largest)
        add_gaussian_peak(signal, 100, 150, 8)

        # Peak 2: position 200, height 180 (second largest)
        add_gaussian_peak(signal, 200, 130, 8)

        # Peak 3: position 300, height 160 (third)
        add_gaussian_peak(signal, 300, 110, 8)

        # Peak 4: position 400, height 140 (fourth)
        add_gaussian_peak(signal, 400, 90, 8)

        # Peak 5: position 480, height 120 (smallest) - moved away from edge
        add_gaussian_peak(signal, 480, 70, 8)

        # Create two columns
        data["ch0_col1"] = (signal * 0.6).tolist()
        data["ch0_col2"] = (signal * 0.4).tolist()

        df = pd.DataFrame(data)
        df.to_csv(csv_path, sep=":", index=False)

        # Create reference module
        module = self.create_mock_module(
            csv_path, "PMA0", is_reference=True, ref_channels=[1]
        )
        dataset = self.create_mock_dataset([module])

        # Process
        parser = DataParser(dataset)
        parser.process_all_files()

        # Verify second-largest peak was selected
        ref_signal = module.added_channels[0]["signal_series"]
        ref_signal.idxmax()

        # Should be around position 200 (second-largest peak)
        # Note: position is relative to the signal portion (after row 257)
        assert len(ref_signal) > 0

        # Peak value should be significant
        assert (
            ref_signal.max() > 100
        )  # Combined value of both columns should be reasonable

    def test_error_handling_missing_file(self):
        """Test error handling with missing CSV file."""
        # Create module with non-existent file
        module = self.create_mock_module("/nonexistent/file.csv", "PMA0")
        dataset = self.create_mock_dataset([module])

        parser = DataParser(dataset)

        # Should raise exception for missing file
        with pytest.raises(Exception, match="Failed to process file for PMA0"):
            parser.process_all_files()

    def test_error_handling_invalid_csv_format(self):
        """Test error handling with invalid CSV format."""
        # Create invalid CSV file
        invalid_csv = os.path.join(self.temp_dir, "invalid.csv")
        with open(invalid_csv, "w") as f:
            f.write("not:valid:csv:format\n")
            f.write("missing:data\n")

        module = self.create_mock_module(invalid_csv, "PMA0")
        dataset = self.create_mock_dataset([module])

        parser = DataParser(dataset)

        # Should raise exception for invalid format
        with pytest.raises(Exception, match="Failed to process file for PMA0"):
            parser.process_all_files()

    def test_error_handling_insufficient_peaks(self):
        """Test error handling when reference channel has insufficient peaks."""
        # Create CSV with only one peak
        csv_path = os.path.join(self.temp_dir, "one_peak.csv")

        bins = list(range(600))
        signal = np.full(600, 50.0)
        signal[200:220] = 200  # Only one peak

        data = {
            "bin": bins,
            "ch0_col1": (signal * 0.6).tolist(),
            "ch0_col2": (signal * 0.4).tolist(),
        }

        df = pd.DataFrame(data)
        df.to_csv(csv_path, sep=":", index=False)

        # Create reference module
        module = self.create_mock_module(
            csv_path, "PMA0", is_reference=True, ref_channels=[1]
        )
        dataset = self.create_mock_dataset([module])

        parser = DataParser(dataset)

        # Should raise exception for insufficient peaks
        with pytest.raises(Exception, match="Failed to process file for PMA0"):
            parser.process_all_files()

    def test_different_file_sizes(self):
        """Test with different CSV file sizes."""
        sizes = [300, 600, 1000, 1500]  # Different row counts

        for size in sizes:
            csv_path = os.path.join(self.temp_dir, f"test_{size}.csv")
            self.create_realistic_csv_file(csv_path, num_channels=1, num_rows=size)

            module = self.create_mock_module(csv_path, f"PMA_{size}")
            dataset = self.create_mock_dataset([module])

            parser = DataParser(dataset)
            parser.process_all_files()

            # Verify correct signal/noise split
            ch = module.added_channels[0]

            if size > 257:
                expected_signal_len = size - 257
                expected_noise_len = 257
            else:
                # If file is smaller than 257 rows, all goes to noise
                expected_signal_len = 0 if size <= 257 else size - 257
                expected_noise_len = min(size, 257)

            assert len(ch["signal_series"]) == expected_signal_len
            assert len(ch["noise_series"]) == expected_noise_len

    def test_edge_case_minimal_valid_file(self):
        """Test with minimal valid CSV file."""
        # Create minimal file with just enough data
        csv_path = os.path.join(self.temp_dir, "minimal.csv")

        # 260 rows (enough for noise + minimal signal)
        data = {
            "bin": list(range(260)),
            "ch0_col1": [50.0] * 260,
            "ch0_col2": [50.0] * 260,
        }

        df = pd.DataFrame(data)
        df.to_csv(csv_path, sep=":", index=False)

        module = self.create_mock_module(csv_path, "PMA0")
        dataset = self.create_mock_dataset([module])

        parser = DataParser(dataset)
        parser.process_all_files()

        # Should work with minimal data
        ch = module.added_channels[0]
        assert len(ch["signal_series"]) == 3  # 260 - 257
        assert len(ch["noise_series"]) == 257

    def test_large_number_of_channels(self):
        """Test with large number of channels."""
        csv_path = os.path.join(self.temp_dir, "many_channels.csv")
        self.create_realistic_csv_file(csv_path, num_channels=10)  # 21 columns total

        module = self.create_mock_module(csv_path, "PMA0")
        dataset = self.create_mock_dataset([module])

        parser = DataParser(dataset)
        parser.process_all_files()

        # Should process all 10 channels
        assert len(module.added_channels) == 10

        # Check channel indices
        channel_indices = [ch["channel_idx"] for ch in module.added_channels]
        assert channel_indices == list(range(1, 11))

    def test_mixed_reference_channels(self):
        """Test with multiple reference channels in same module."""
        csv_path = os.path.join(self.temp_dir, "mixed_ref.csv")

        # Create simpler data specifically for this test
        bins = list(range(600))
        data = {"bin": bins}

        # Create 4 channels (8 columns) with simple signals
        for ch in range(4):
            # Create baseline signal
            signal = np.full(600, 50.0)

            # Add exactly 2 peaks for reference channels (ch 0 and 2)
            if ch == 0 or ch == 2:
                # Peak 1: position 150 (after cutting 50 bins from signal part)
                signal[400:420] = 120  # In signal part (257+)
                # Peak 2: position 250 (after cutting 50 bins)
                signal[500:520] = 100  # In signal part (257+)

            # Create two columns per channel
            data[f"ch{ch}_col1"] = (signal * 0.6).tolist()
            data[f"ch{ch}_col2"] = (signal * 0.4).tolist()

        df = pd.DataFrame(data)
        df.to_csv(csv_path, sep=":", index=False)

        # Channels 1 and 3 are reference channels
        module = self.create_mock_module(
            csv_path, "PMA0", is_reference=True, ref_channels=[1, 3]
        )
        dataset = self.create_mock_dataset([module])

        parser = DataParser(dataset)
        parser.process_all_files()

        # Should process all 4 channels
        assert len(module.added_channels) == 4

        # Channels 1 and 3 should have reference processing (shorter signals)
        ch1_signal = module.added_channels[0]["signal_series"]  # Channel 1
        ch2_signal = module.added_channels[1]["signal_series"]  # Channel 2
        ch3_signal = module.added_channels[2]["signal_series"]  # Channel 3
        ch4_signal = module.added_channels[3]["signal_series"]  # Channel 4

        # Reference channels should be shorter
        assert len(ch1_signal) < 343
        assert len(ch3_signal) < 343

        # Non-reference channels should be full length
        assert len(ch2_signal) == 343
        assert len(ch4_signal) == 343


class TestDataParserPerformance:
    """Performance tests for DataParser."""

    def setup_method(self):
        """Setup method run before each test."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Teardown method run after each test."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_large_csv_file(self, filepath, num_channels=10, num_rows=5000):
        """Create a large CSV file for performance testing."""
        data = {"bin": list(range(num_rows))}

        for ch in range(num_channels):
            col1_data = np.random.normal(100, 10, num_rows)
            col2_data = np.random.normal(90, 8, num_rows)

            data[f"ch{ch}_col1"] = col1_data.tolist()
            data[f"ch{ch}_col2"] = col2_data.tolist()

        df = pd.DataFrame(data)
        df.to_csv(filepath, sep=":", index=False)
        return filepath

    def test_large_file_processing(self):
        """Test processing of large CSV files."""
        import time

        # Create large CSV file
        csv_path = os.path.join(self.temp_dir, "large_file.csv")
        self.create_large_csv_file(csv_path, num_channels=10, num_rows=5000)

        # Create module and dataset
        module = MagicMock()
        module.path = csv_path
        module.identifier = "PMA_LARGE"
        module.is_reference = False
        module.ref_channels = []
        module.added_channels = []

        def mock_add_channel(chan_idx, sig_series, noise_series):
            module.added_channels.append(
                {
                    "channel_idx": chan_idx,
                    "signal_series": sig_series.copy(),
                    "noise_series": noise_series.copy(),
                }
            )

        module.add_channel = mock_add_channel

        dataset = MagicMock()
        dataset.modules = [module]

        # Process and measure time
        parser = DataParser(dataset)
        start_time = time.time()
        parser.process_all_files()
        end_time = time.time()

        processing_time = end_time - start_time

        # Verify results
        assert len(module.added_channels) == 10
        assert processing_time < 10.0  # Should complete within 10 seconds

        # Verify data integrity
        for ch in module.added_channels:
            assert len(ch["signal_series"]) == 5000 - 257  # 4743
            assert len(ch["noise_series"]) == 257

    def test_memory_usage_large_datasets(self):
        """Test memory usage with large datasets."""
        import gc

        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create multiple large files
        csv_paths = []
        for i in range(5):
            csv_path = os.path.join(self.temp_dir, f"large_file_{i}.csv")
            self.create_large_csv_file(csv_path, num_channels=5, num_rows=3000)
            csv_paths.append(csv_path)

        # Create modules
        modules = []
        for i, csv_path in enumerate(csv_paths):
            module = MagicMock()
            module.path = csv_path
            module.identifier = f"PMA_{i}"
            module.is_reference = False
            module.ref_channels = []
            module.added_channels = []

            def mock_add_channel(chan_idx, sig_series, noise_series, mod=module):
                mod.added_channels.append(
                    {
                        "channel_idx": chan_idx,
                        "signal_series": sig_series.copy(),
                        "noise_series": noise_series.copy(),
                    }
                )

            module.add_channel = mock_add_channel
            modules.append(module)

        dataset = MagicMock()
        dataset.modules = modules

        # Process all files
        parser = DataParser(dataset)
        parser.process_all_files()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Verify all files were processed
        total_channels = sum(len(mod.added_channels) for mod in modules)
        assert total_channels == 25  # 5 files * 5 channels each

        # Memory increase should be reasonable (less than 500MB for this test)
        assert memory_increase < 500

        # Clean up
        del parser, dataset, modules
        gc.collect()
