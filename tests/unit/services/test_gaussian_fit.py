"""Tests for the GaussianFitService."""

from unittest.mock import Mock, patch

import numpy as np
import pandas as pd

from ageing_analysis.entities.dataset import Dataset
from ageing_analysis.services.gaussian_fit import GaussianFitService


class TestGaussianFitService:
    """Test cases for GaussianFitService."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock dataset
        self.mock_dataset = Mock(spec=Dataset)
        self.mock_dataset.date = "2024-01-01"

        # Create mock modules and channels
        self.mock_module = Mock()
        self.mock_module.identifier = "PMA1"

        self.mock_channel = Mock()
        self.mock_channel.name = "CH01"
        self.mock_channel.is_reference = False
        self.mock_channel.data = pd.Series([1, 2, 3, 2, 1])
        self.mock_channel.noise_data = None

        self.mock_module.channels = [self.mock_channel]
        self.mock_dataset.modules = [self.mock_module]

    def test_init_with_debug_mode_false(self):
        """Test initialization with debug_mode=False."""
        service = GaussianFitService(self.mock_dataset, debug_mode=False)
        assert service.debug_mode is False
        assert service.dataset == self.mock_dataset

    def test_init_with_debug_mode_true(self):
        """Test initialization with debug_mode=True."""
        service = GaussianFitService(self.mock_dataset, debug_mode=True)
        assert service.debug_mode is True
        assert service.dataset == self.mock_dataset

    def test_gaussian_function(self):
        """Test the gaussian function calculation."""
        service = GaussianFitService(self.mock_dataset)
        x = np.array([0, 1, 2])
        amplitude = 1.0
        mean = 1.0
        stddev = 0.5

        result = service.gaussian(x, amplitude, mean, stddev)

        assert len(result) == 3
        assert isinstance(result, np.ndarray)
        # The peak should be at x=1 (mean=1)
        assert result[1] > result[0]
        assert result[1] > result[2]

    def test_fit_gaussian_success(self):
        """Test successful Gaussian fitting."""
        service = GaussianFitService(self.mock_dataset, debug_mode=False)

        # Create test data that should fit well to a Gaussian
        x = np.linspace(0, 10, 50)
        y = 2.0 * np.exp(-((x - 5.0) ** 2) / (2 * 1.5**2)) + 0.1 * np.random.randn(50)
        data_series = pd.Series(y)

        result = service.fit_gaussian(
            data_series, is_reference=False, module_id="PMA1", channel_name="CH01"
        )

        assert isinstance(result, float)
        assert result > 0  # Should be close to 5.0

    def test_fit_gaussian_zero_data(self):
        """Test Gaussian fitting with zero data."""
        service = GaussianFitService(self.mock_dataset, debug_mode=False)

        zero_data = pd.Series([0, 0, 0, 0, 0])
        result = service.fit_gaussian(
            zero_data, is_reference=False, module_id="PMA1", channel_name="CH01"
        )

        assert result == 0

    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.close")
    @patch("os.makedirs")
    def test_debug_plot_creation(self, mock_makedirs, mock_close, mock_savefig):
        """Test that debug plots are created when debug_mode is True."""
        service = GaussianFitService(self.mock_dataset, debug_mode=True)

        # Create test data
        x = np.linspace(0, 10, 50)
        y = 2.0 * np.exp(-((x - 5.0) ** 2) / (2 * 1.5**2))
        data_series = pd.Series(y)

        # Mock parameters
        params = np.array([2.0, 5.0, 1.5])

        # Call the private method directly
        service._create_debug_plot(data_series, params, "PMA1", "CH01", False, True)

        # Verify that the directory was created
        mock_makedirs.assert_called_once()

        # Verify that the plot was saved
        mock_savefig.assert_called_once()
        # matplotlib might call close() multiple times, so just check it was called
        assert mock_close.called

    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.close")
    @patch("os.makedirs")
    def test_debug_plot_failed_fit(self, mock_makedirs, mock_close, mock_savefig):
        """Test debug plot creation for failed fits."""
        service = GaussianFitService(self.mock_dataset, debug_mode=True)

        # Create test data
        data_series = pd.Series([1, 2, 3, 2, 1])

        # Call with failed fit (params=None, fit_successful=False)
        service._create_debug_plot(data_series, None, "PMA1", "CH01", False, False)

        # Verify that the directory was created
        mock_makedirs.assert_called_once()

        # Verify that the plot was saved
        mock_savefig.assert_called_once()
        # matplotlib might call close() multiple times, so just check it was called
        assert mock_close.called

    def test_calculate_weighted_mean(self):
        """Test weighted mean calculation."""
        service = GaussianFitService(self.mock_dataset)

        # Create test data
        data_series = pd.Series([1, 2, 3, 2, 1])

        result = service.calculate_weighted_mean(data_series)

        assert isinstance(result, float)
        assert result > 0

    def test_calculate_weighted_mean_zero_data(self):
        """Test weighted mean calculation with zero data."""
        service = GaussianFitService(self.mock_dataset)

        zero_data = pd.Series([0, 0, 0, 0, 0])
        result = service.calculate_weighted_mean(zero_data)

        assert result == 0

    def test_calculate_weighted_mean_reference_channel(self):
        """Test weighted mean calculation for reference channels."""
        service = GaussianFitService(self.mock_dataset)

        data_series = pd.Series([1, 2, 3, 2, 1])

        # Test with reference channel data
        result = service.calculate_weighted_mean(data_series)

        assert isinstance(result, float)
        assert result > 0  # Should be a positive value

    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.close")
    @patch("os.makedirs")
    def test_process_all_modules_with_debug(
        self, mock_makedirs, mock_close, mock_savefig
    ):
        """Test processing all modules with debug mode enabled."""
        service = GaussianFitService(self.mock_dataset, debug_mode=True)

        # Process all modules
        service.process_all_modules()

        # Verify that debug plots were created
        mock_makedirs.assert_called()
        mock_savefig.assert_called()
        mock_close.assert_called()

    def test_process_all_modules_without_debug(self):
        """Test processing all modules without debug mode."""
        service = GaussianFitService(self.mock_dataset, debug_mode=False)

        # Process all modules
        service.process_all_modules()

        # Verify that means were set on the channel
        assert self.mock_channel.set_means.called
