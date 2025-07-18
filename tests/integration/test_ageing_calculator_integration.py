"""Integration tests for the AgeingCalculationService."""

from unittest.mock import patch

import pandas as pd

from ageing_analysis.entities import Channel, Dataset, Module
from ageing_analysis.services.ageing_calculator import AgeingCalculationService


class TestAgeingCalculationServiceIntegration:
    """Integration tests for AgeingCalculationService with real entities."""

    @patch("ageing_analysis.entities.module.os.path.exists")
    @patch("ageing_analysis.entities.module.validate_csv")
    def test_ageing_calculation_with_real_entities(
        self, mock_validate_csv, mock_exists
    ):
        """Test ageing factor calculation with real Dataset, Module, and Channel
        entities."""
        # Mock file validation
        mock_exists.return_value = True
        mock_validate_csv.return_value = True

        # Create test data
        signal_data1 = pd.Series([100, 101, 102, 103, 104])
        noise_data1 = pd.Series([1, 2, 1, 2, 1])
        total_signal_data1 = pd.Series([200, 201, 202, 203, 204])

        signal_data2 = pd.Series([110, 111, 112, 113, 114])
        noise_data2 = pd.Series([2, 1, 2, 1, 2])
        total_signal_data2 = pd.Series([220, 221, 222, 223, 224])

        # Create channels
        channel1 = Channel(
            "CH01", signal_data1, noise_data1, False, None, total_signal_data1
        )
        channel2 = Channel(
            "CH02", signal_data2, noise_data2, False, None, total_signal_data2
        )

        # Set means for channels
        channel1.set_means(100.0, 95.0)  # Current channel means
        channel2.set_means(110.0, 105.0)  # Current channel means

        # Create module
        module = Module("dummy_path", "PMA0", False, None, False, None)
        module.channels = [channel1, channel2]

        # Create dataset
        dataset = Dataset(
            date="2022-01-01",
            base_path="/dummy/path",
            files={"PMA0": "dummy_file.csv"},
            ref_ch={"PM": "PMA0", "CH": [1]},
            validate_header=False,
        )
        dataset.modules = [module]

        # Set reference means (same dataset reference)
        dataset.set_reference_means(100.0, 95.0)

        # Create service and calculate ageing factors
        service = AgeingCalculationService(dataset)
        service.calculate_ageing_factors()

        # Verify ageing factors were calculated correctly
        # Channel 1: 100.0 / 100.0 = 1.0, 95.0 / 95.0 = 1.0
        assert channel1.get_gauss_ageing_factor() == 1.0
        assert channel1.get_weighted_ageing_factor() == 1.0

        # Channel 2: 110.0 / 100.0 = 1.1, 105.0 / 95.0 = 1.105...
        assert channel2.get_gauss_ageing_factor() == 1.1
        assert abs(channel2.get_weighted_ageing_factor() - 1.105263) < 1e-6

    @patch("ageing_analysis.entities.module.os.path.exists")
    @patch("ageing_analysis.entities.module.validate_csv")
    def test_ageing_calculation_with_multiple_modules(
        self, mock_validate_csv, mock_exists
    ):
        """Test ageing factor calculation with multiple modules."""
        # Mock file validation
        mock_exists.return_value = True
        mock_validate_csv.return_value = True

        # Create test data for first module
        signal_data1 = pd.Series([90, 91, 92, 93, 94])
        noise_data1 = pd.Series([1, 1, 1, 1, 1])
        total_signal_data1 = pd.Series([180, 181, 182, 183, 184])

        # Create test data for second module
        signal_data2 = pd.Series([120, 121, 122, 123, 124])
        noise_data2 = pd.Series([2, 2, 2, 2, 2])
        total_signal_data2 = pd.Series([240, 241, 242, 243, 244])

        # Create channels
        channel1 = Channel(
            "CH01", signal_data1, noise_data1, False, None, total_signal_data1
        )
        channel2 = Channel(
            "CH01", signal_data2, noise_data2, False, None, total_signal_data2
        )

        # Set means for channels
        channel1.set_means(90.0, 85.0)  # Module 1 channel means
        channel2.set_means(120.0, 115.0)  # Module 2 channel means

        # Create modules
        module1 = Module("dummy_path1", "PMA0", False, None, False, None)
        module1.channels = [channel1]

        module2 = Module("dummy_path2", "PMA1", False, None, False, None)
        module2.channels = [channel2]

        # Create dataset
        dataset = Dataset(
            date="2022-01-01",
            base_path="/dummy/path",
            files={"PMA0": "dummy_file1.csv", "PMA1": "dummy_file2.csv"},
            ref_ch={"PM": "PMA0", "CH": [1]},
            validate_header=False,
        )
        dataset.modules = [module1, module2]

        # Set reference means (same dataset reference)
        dataset.set_reference_means(100.0, 95.0)

        # Create service and calculate ageing factors
        service = AgeingCalculationService(dataset)
        service.calculate_ageing_factors()

        # Verify ageing factors for module 1
        # Channel 1: 90.0 / 100.0 = 0.9, 85.0 / 95.0 = 0.8947...
        assert channel1.get_gauss_ageing_factor() == 0.9
        assert abs(channel1.get_weighted_ageing_factor() - 0.894737) < 1e-6

        # Verify ageing factors for module 2
        # Channel 2: 120.0 / 100.0 = 1.2, 115.0 / 95.0 = 1.2105...
        assert channel2.get_gauss_ageing_factor() == 1.2
        assert abs(channel2.get_weighted_ageing_factor() - 1.210526) < 1e-6

    @patch("ageing_analysis.entities.module.os.path.exists")
    @patch("ageing_analysis.entities.module.validate_csv")
    def test_ageing_calculation_with_reference_channel(
        self, mock_validate_csv, mock_exists
    ):
        """Test ageing factor calculation including a reference channel."""
        # Mock file validation
        mock_exists.return_value = True
        mock_validate_csv.return_value = True

        # Create test data
        signal_data1 = pd.Series([100, 101, 102, 103, 104])
        noise_data1 = pd.Series([1, 2, 1, 2, 1])
        total_signal_data1 = pd.Series([200, 201, 202, 203, 204])

        signal_data2 = pd.Series([110, 111, 112, 113, 114])
        noise_data2 = pd.Series([2, 1, 2, 1, 2])
        total_signal_data2 = pd.Series([220, 221, 222, 223, 224])

        # Create channels (first one is reference)
        channel1 = Channel(
            "CH01", signal_data1, noise_data1, True, None, total_signal_data1
        )
        channel2 = Channel(
            "CH02", signal_data2, noise_data2, False, None, total_signal_data2
        )

        # Set means for channels
        channel1.set_means(100.0, 95.0)  # Reference channel means
        channel2.set_means(110.0, 105.0)  # Regular channel means

        # Create module
        module = Module("dummy_path", "PMA0", True, [1], False, None)
        module.channels = [channel1, channel2]

        # Create dataset
        dataset = Dataset(
            date="2022-01-01",
            base_path="/dummy/path",
            files={"PMA0": "dummy_file.csv"},
            ref_ch={"PM": "PMA0", "CH": [1]},
            validate_header=False,
        )
        dataset.modules = [module]

        # Set reference means (same dataset reference)
        dataset.set_reference_means(100.0, 95.0)

        # Create service and calculate ageing factors
        service = AgeingCalculationService(dataset)
        service.calculate_ageing_factors()

        # Verify ageing factors
        # Reference channel: 100.0 / 100.0 = 1.0, 95.0 / 95.0 = 1.0
        assert channel1.get_gauss_ageing_factor() == 1.0
        assert channel1.get_weighted_ageing_factor() == 1.0

        # Regular channel: 110.0 / 100.0 = 1.1, 105.0 / 95.0 = 1.105...
        assert channel2.get_gauss_ageing_factor() == 1.1
        assert abs(channel2.get_weighted_ageing_factor() - 1.105263) < 1e-6

    @patch("ageing_analysis.entities.module.os.path.exists")
    @patch("ageing_analysis.entities.module.validate_csv")
    def test_ageing_calculation_with_integrated_charge(
        self, mock_validate_csv, mock_exists
    ):
        """Test ageing factor calculation with integrated charge data."""
        # Mock file validation
        mock_exists.return_value = True
        mock_validate_csv.return_value = True

        # Create test data
        signal_data = pd.Series([100, 101, 102, 103, 104])
        noise_data = pd.Series([1, 2, 1, 2, 1])
        total_signal_data = pd.Series([200, 201, 202, 203, 204])

        # Create channel with integrated charge
        channel = Channel(
            "CH01", signal_data, noise_data, False, 150.5, total_signal_data
        )
        channel.set_means(100.0, 95.0)

        # Create module
        module = Module("dummy_path", "PMA0", False, None, False, None)
        module.channels = [channel]

        # Create dataset
        dataset = Dataset(
            date="2022-01-01",
            base_path="/dummy/path",
            files={"PMA0": "dummy_file.csv"},
            ref_ch={"PM": "PMA0", "CH": [1]},
            validate_header=False,
        )
        dataset.modules = [module]

        # Set reference means
        dataset.set_reference_means(100.0, 95.0)

        # Create service and calculate ageing factors
        service = AgeingCalculationService(dataset)
        service.calculate_ageing_factors()

        # Verify ageing factors
        assert channel.get_gauss_ageing_factor() == 1.0
        assert channel.get_weighted_ageing_factor() == 1.0

        # Verify integrated charge is preserved
        assert channel.integrated_charge == 150.5

    @patch("ageing_analysis.entities.module.os.path.exists")
    @patch("ageing_analysis.entities.module.validate_csv")
    def test_ageing_calculation_edge_cases(self, mock_validate_csv, mock_exists):
        """Test ageing factor calculation with edge cases."""
        # Mock file validation
        mock_exists.return_value = True
        mock_validate_csv.return_value = True

        # Test with very small values
        signal_data = pd.Series([0.001, 0.002, 0.003])
        noise_data = pd.Series([0.0001, 0.0002, 0.0001])
        total_signal_data = pd.Series([0.002, 0.004, 0.006])

        channel = Channel(
            "CH01", signal_data, noise_data, False, None, total_signal_data
        )
        channel.set_means(0.002, 0.001)

        module = Module("dummy_path", "PMA0", False, None, False, None)
        module.channels = [channel]

        dataset = Dataset(
            date="2022-01-01",
            base_path="/dummy/path",
            files={"PMA0": "dummy_file.csv"},
            ref_ch={"PM": "PMA0", "CH": [1]},
            validate_header=False,
        )
        dataset.modules = [module]
        dataset.set_reference_means(0.001, 0.0005)

        service = AgeingCalculationService(dataset)
        service.calculate_ageing_factors()

        # Verify ageing factors with small values
        assert channel.get_gauss_ageing_factor() == 2.0  # 0.002 / 0.001
        assert channel.get_weighted_ageing_factor() == 2.0  # 0.001 / 0.0005

    @patch("ageing_analysis.entities.module.os.path.exists")
    @patch("ageing_analysis.entities.module.validate_csv")
    def test_ageing_calculation_verifies_same_dataset_reference(
        self, mock_validate_csv, mock_exists
    ):
        """Test that ageing factors are calculated using the same dataset's reference
        means."""
        # Mock file validation
        mock_exists.return_value = True
        mock_validate_csv.return_value = True

        # Create test data for two different datasets
        signal_data1 = pd.Series([100, 101, 102])
        noise_data1 = pd.Series([1, 1, 1])
        total_signal_data1 = pd.Series([200, 201, 202])

        signal_data2 = pd.Series([110, 111, 112])
        noise_data2 = pd.Series([2, 2, 2])
        total_signal_data2 = pd.Series([220, 221, 222])

        # Create channels for different datasets
        channel1 = Channel(
            "CH01", signal_data1, noise_data1, False, None, total_signal_data1
        )
        channel2 = Channel(
            "CH01", signal_data2, noise_data2, False, None, total_signal_data2
        )

        # Set means for channels
        channel1.set_means(100.0, 95.0)  # Dataset 1 channel
        channel2.set_means(110.0, 105.0)  # Dataset 2 channel

        # Create modules
        module1 = Module("dummy_path1", "PMA0", False, None, False, None)
        module1.channels = [channel1]

        module2 = Module("dummy_path2", "PMA0", False, None, False, None)
        module2.channels = [channel2]

        # Create two different datasets with different reference means
        dataset1 = Dataset(
            date="2022-01-01",
            base_path="/dummy/path1",
            files={"PMA0": "dummy_file1.csv"},
            ref_ch={"PM": "PMA0", "CH": [1]},
            validate_header=False,
        )
        dataset1.modules = [module1]
        dataset1.set_reference_means(100.0, 95.0)  # Dataset 1 reference

        dataset2 = Dataset(
            date="2022-06-01",
            base_path="/dummy/path2",
            files={"PMA0": "dummy_file2.csv"},
            ref_ch={"PM": "PMA0", "CH": [1]},
            validate_header=False,
        )
        dataset2.modules = [module2]
        dataset2.set_reference_means(120.0, 115.0)  # Dataset 2 reference (different!)

        # Calculate ageing factors for both datasets
        service1 = AgeingCalculationService(dataset1)
        service1.calculate_ageing_factors()

        service2 = AgeingCalculationService(dataset2)
        service2.calculate_ageing_factors()

        # Verify that each dataset uses its own reference means
        # Dataset 1: 100.0 / 100.0 = 1.0, 95.0 / 95.0 = 1.0
        assert channel1.get_gauss_ageing_factor() == 1.0
        assert channel1.get_weighted_ageing_factor() == 1.0

        # Dataset 2: 110.0 / 120.0 = 0.916..., 105.0 / 115.0 = 0.913...
        assert abs(channel2.get_gauss_ageing_factor() - 0.916667) < 1e-6
        assert abs(channel2.get_weighted_ageing_factor() - 0.913043) < 1e-6
