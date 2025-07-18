"""Unit tests for the AgeingCalculationService."""

from unittest.mock import Mock

import pytest

from ageing_analysis.services.ageing_calculator import AgeingCalculationService


class TestAgeingCalculationService:
    """Test cases for AgeingCalculationService."""

    def test_init_with_dataset(self):
        """Test initialization with a dataset."""
        # Create mock dataset
        mock_dataset = Mock()
        mock_dataset.get_reference_gaussian_mean.return_value = 100.0
        mock_dataset.get_reference_weighted_mean.return_value = 95.0

        # Create service
        service = AgeingCalculationService(mock_dataset)

        # Verify initialization
        assert service.dataset == mock_dataset
        assert service.reference_gaussian_mean == 100.0
        assert service.reference_weighted_mean == 95.0

        # Verify dataset methods were called
        mock_dataset.get_reference_gaussian_mean.assert_called_once()
        mock_dataset.get_reference_weighted_mean.assert_called_once()

    def test_calculate_ageing_factors_single_channel(self):
        """Test ageing factor calculation for a single channel."""
        # Create mock channel
        mock_channel = Mock()
        mock_channel.get_gaussian_mean.return_value = 90.0
        mock_channel.get_weighted_mean.return_value = 85.0
        mock_channel.set_ageing_factors = Mock()

        # Create mock module
        mock_module = Mock()
        mock_module.identifier = "PMA0"
        mock_module.channels = [mock_channel]

        # Create mock dataset
        mock_dataset = Mock()
        mock_dataset.get_reference_gaussian_mean.return_value = 100.0
        mock_dataset.get_reference_weighted_mean.return_value = 95.0
        mock_dataset.modules = [mock_module]
        mock_dataset.date = "2022-01-01"

        # Create service and calculate ageing factors
        service = AgeingCalculationService(mock_dataset)
        service.calculate_ageing_factors()

        # Verify ageing factors were calculated correctly
        expected_gaussian_factor = 90.0 / 100.0  # 0.9
        expected_weighted_factor = 85.0 / 95.0  # 0.8947...

        mock_channel.set_ageing_factors.assert_called_once_with(
            expected_gaussian_factor, expected_weighted_factor
        )

    def test_calculate_ageing_factors_multiple_channels(self):
        """Test ageing factor calculation for multiple channels."""
        # Create mock channels
        mock_channel1 = Mock()
        mock_channel1.get_gaussian_mean.return_value = 90.0
        mock_channel1.get_weighted_mean.return_value = 85.0
        mock_channel1.set_ageing_factors = Mock()

        mock_channel2 = Mock()
        mock_channel2.get_gaussian_mean.return_value = 110.0
        mock_channel2.get_weighted_mean.return_value = 105.0
        mock_channel2.set_ageing_factors = Mock()

        # Create mock module
        mock_module = Mock()
        mock_module.identifier = "PMA0"
        mock_module.channels = [mock_channel1, mock_channel2]

        # Create mock dataset
        mock_dataset = Mock()
        mock_dataset.get_reference_gaussian_mean.return_value = 100.0
        mock_dataset.get_reference_weighted_mean.return_value = 95.0
        mock_dataset.modules = [mock_module]
        mock_dataset.date = "2022-01-01"

        # Create service and calculate ageing factors
        service = AgeingCalculationService(mock_dataset)
        service.calculate_ageing_factors()

        # Verify ageing factors for first channel
        expected_gaussian_factor1 = 90.0 / 100.0  # 0.9
        expected_weighted_factor1 = 85.0 / 95.0  # 0.8947...
        mock_channel1.set_ageing_factors.assert_called_once_with(
            expected_gaussian_factor1, expected_weighted_factor1
        )

        # Verify ageing factors for second channel
        expected_gaussian_factor2 = 110.0 / 100.0  # 1.1
        expected_weighted_factor2 = 105.0 / 95.0  # 1.105...
        mock_channel2.set_ageing_factors.assert_called_once_with(
            expected_gaussian_factor2, expected_weighted_factor2
        )

    def test_calculate_ageing_factors_multiple_modules(self):
        """Test ageing factor calculation for multiple modules."""
        # Create mock channels for first module
        mock_channel1 = Mock()
        mock_channel1.get_gaussian_mean.return_value = 90.0
        mock_channel1.get_weighted_mean.return_value = 85.0
        mock_channel1.set_ageing_factors = Mock()

        mock_module1 = Mock()
        mock_module1.identifier = "PMA0"
        mock_module1.channels = [mock_channel1]

        # Create mock channels for second module
        mock_channel2 = Mock()
        mock_channel2.get_gaussian_mean.return_value = 110.0
        mock_channel2.get_weighted_mean.return_value = 105.0
        mock_channel2.set_ageing_factors = Mock()

        mock_module2 = Mock()
        mock_module2.identifier = "PMA1"
        mock_module2.channels = [mock_channel2]

        # Create mock dataset
        mock_dataset = Mock()
        mock_dataset.get_reference_gaussian_mean.return_value = 100.0
        mock_dataset.get_reference_weighted_mean.return_value = 95.0
        mock_dataset.modules = [mock_module1, mock_module2]
        mock_dataset.date = "2022-01-01"

        # Create service and calculate ageing factors
        service = AgeingCalculationService(mock_dataset)
        service.calculate_ageing_factors()

        # Verify ageing factors for first module
        expected_gaussian_factor1 = 90.0 / 100.0  # 0.9
        expected_weighted_factor1 = 85.0 / 95.0  # 0.8947...
        mock_channel1.set_ageing_factors.assert_called_once_with(
            expected_gaussian_factor1, expected_weighted_factor1
        )

        # Verify ageing factors for second module
        expected_gaussian_factor2 = 110.0 / 100.0  # 1.1
        expected_weighted_factor2 = 105.0 / 95.0  # 1.105...
        mock_channel2.set_ageing_factors.assert_called_once_with(
            expected_gaussian_factor2, expected_weighted_factor2
        )

    def test_calculate_ageing_factors_with_zero_reference_means(self):
        """Test ageing factor calculation with zero reference means.

        Should handle division by zero.
        """
        # Create mock channel
        mock_channel = Mock()
        mock_channel.get_gaussian_mean.return_value = 90.0
        mock_channel.get_weighted_mean.return_value = 85.0
        mock_channel.set_ageing_factors = Mock()

        # Create mock module
        mock_module = Mock()
        mock_module.identifier = "PMA0"
        mock_module.channels = [mock_channel]

        # Create mock dataset with zero reference means
        mock_dataset = Mock()
        mock_dataset.get_reference_gaussian_mean.return_value = 0.0
        mock_dataset.get_reference_weighted_mean.return_value = 0.0
        mock_dataset.modules = [mock_module]
        mock_dataset.date = "2022-01-01"

        # Create service and calculate ageing factors
        service = AgeingCalculationService(mock_dataset)

        # This should raise a ZeroDivisionError
        with pytest.raises(ZeroDivisionError):
            service.calculate_ageing_factors()

    def test_calculate_ageing_factors_with_negative_values(self):
        """Test ageing factor calculation with negative values."""
        # Create mock channel
        mock_channel = Mock()
        mock_channel.get_gaussian_mean.return_value = -90.0
        mock_channel.get_weighted_mean.return_value = -85.0
        mock_channel.set_ageing_factors = Mock()

        # Create mock module
        mock_module = Mock()
        mock_module.identifier = "PMA0"
        mock_module.channels = [mock_channel]

        # Create mock dataset
        mock_dataset = Mock()
        mock_dataset.get_reference_gaussian_mean.return_value = 100.0
        mock_dataset.get_reference_weighted_mean.return_value = 95.0
        mock_dataset.modules = [mock_module]
        mock_dataset.date = "2022-01-01"

        # Create service and calculate ageing factors
        service = AgeingCalculationService(mock_dataset)
        service.calculate_ageing_factors()

        # Verify ageing factors were calculated correctly (negative values)
        expected_gaussian_factor = -90.0 / 100.0  # -0.9
        expected_weighted_factor = -85.0 / 95.0  # -0.8947...

        mock_channel.set_ageing_factors.assert_called_once_with(
            expected_gaussian_factor, expected_weighted_factor
        )

    def test_calculate_ageing_factors_empty_modules(self):
        """Test ageing factor calculation with empty modules list."""
        # Create mock dataset with no modules
        mock_dataset = Mock()
        mock_dataset.get_reference_gaussian_mean.return_value = 100.0
        mock_dataset.get_reference_weighted_mean.return_value = 95.0
        mock_dataset.modules = []
        mock_dataset.date = "2022-01-01"

        # Create service and calculate ageing factors
        service = AgeingCalculationService(mock_dataset)
        service.calculate_ageing_factors()

        # Should complete without errors (no channels to process)

    def test_calculate_ageing_factors_empty_channels(self):
        """Test ageing factor calculation with empty channels list."""
        # Create mock module with no channels
        mock_module = Mock()
        mock_module.identifier = "PMA0"
        mock_module.channels = []

        # Create mock dataset
        mock_dataset = Mock()
        mock_dataset.get_reference_gaussian_mean.return_value = 100.0
        mock_dataset.get_reference_weighted_mean.return_value = 95.0
        mock_dataset.modules = [mock_module]
        mock_dataset.date = "2022-01-01"

        # Create service and calculate ageing factors
        service = AgeingCalculationService(mock_dataset)
        service.calculate_ageing_factors()

        # Should complete without errors (no channels to process)
