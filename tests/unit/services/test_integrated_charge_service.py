"""Tests for IntegratedChargeService."""


from ageing_analysis.services.integrated_charge_service import IntegratedChargeService


class TestIntegratedChargeService:
    """Test cases for IntegratedChargeService."""

    def test_normalize_channel_name_various_formats(self):
        """Test channel name normalization with various formats."""
        # Test different channel name formats
        test_cases = [
            ("CH01", "CH01"),  # Already correct
            ("Ch01", "CH01"),  # Mixed case
            ("ch01", "CH01"),  # Lowercase
            ("CH1", "CH01"),  # No leading zero
            ("Ch1", "CH01"),  # Mixed case, no leading zero
            ("ch1", "CH01"),  # Lowercase, no leading zero
            ("CH001", "CH01"),  # Extra leading zeros
            ("Ch001", "CH01"),  # Mixed case, extra leading zeros
            ("ch001", "CH01"),  # Lowercase, extra leading zeros
            ("CH12", "CH12"),  # Double digit
            ("Ch12", "CH12"),  # Mixed case, double digit
            ("ch12", "CH12"),  # Lowercase, double digit
        ]

        for input_name, expected in test_cases:
            result = IntegratedChargeService.normalize_channel_name(input_name)
            assert (
                result == expected
            ), f"Failed for input '{input_name}': expected '{expected}', got '{result}'"

    def test_normalize_channel_name_edge_cases(self):
        """Test channel name normalization with edge cases."""
        # Test edge cases
        assert IntegratedChargeService.normalize_channel_name("") == ""
        assert IntegratedChargeService.normalize_channel_name(None) is None
        assert IntegratedChargeService.normalize_channel_name("CH") == "CH"  # No number
        assert (
            IntegratedChargeService.normalize_channel_name("ABC123") == "CH123"
        )  # Contains CH pattern

    def test_normalize_pm_name_various_formats(self):
        """Test PM name normalization with various formats."""
        # Test different PM name formats
        test_cases = [
            ("PMA0", "PMA0"),  # Already correct
            ("pma0", "PMA0"),  # Lowercase
            ("Pma0", "PMA0"),  # Mixed case
            ("PMC9", "PMC9"),  # Already correct
            ("pmc9", "PMC9"),  # Lowercase
            ("Pmc9", "PMC9"),  # Mixed case
        ]

        for input_name, expected in test_cases:
            result = IntegratedChargeService.normalize_pm_name(input_name)
            assert (
                result == expected
            ), f"Failed for input '{input_name}': expected '{expected}', got '{result}'"

    def test_normalize_pm_name_edge_cases(self):
        """Test PM name normalization with edge cases."""
        # Test edge cases
        assert IntegratedChargeService.normalize_pm_name("") == ""
        assert IntegratedChargeService.normalize_pm_name(None) is None

    def test_is_integrated_charge_available_with_all_channels_having_charge(self):
        """Test that integrated charge is available when all channels have it."""
        results_data = {
            "datasets": [
                {
                    "date": "2022-01-01",
                    "modules": [
                        {
                            "identifier": "PMA0",
                            "channels": [
                                {"name": "CH01", "integratedCharge": 100},
                                {"name": "CH02", "integratedCharge": 150},
                            ],
                        }
                    ],
                },
                {
                    "date": "2022-02-01",
                    "modules": [
                        {
                            "identifier": "PMA0",
                            "channels": [
                                {"name": "CH01", "integratedCharge": 200},
                                {"name": "CH02", "integratedCharge": 250},
                            ],
                        }
                    ],
                },
            ]
        }

        assert (
            IntegratedChargeService.is_integrated_charge_available(results_data) is True
        )

    def test_is_integrated_charge_available_with_some_channels_missing_charge(self):
        """Test that integrated charge is not available when some channels lack it."""
        results_data = {
            "datasets": [
                {
                    "date": "2022-01-01",
                    "modules": [
                        {
                            "identifier": "PMA0",
                            "channels": [
                                {"name": "CH01", "integratedCharge": 100},
                                {"name": "CH02"},  # Missing integratedCharge
                            ],
                        }
                    ],
                }
            ]
        }

        assert (
            IntegratedChargeService.is_integrated_charge_available(results_data)
            is False
        )

    def test_is_integrated_charge_available_with_no_datasets(self):
        """Test that integrated charge is not available when there are no datasets."""
        results_data = {"datasets": []}

        assert (
            IntegratedChargeService.is_integrated_charge_available(results_data)
            is False
        )

    def test_is_integrated_charge_available_with_no_datasets_key(self):
        """Test that integrated charge is not available when datasets key is missing."""
        results_data = {"other_key": "value"}

        assert (
            IntegratedChargeService.is_integrated_charge_available(results_data)
            is False
        )

    def test_is_integrated_charge_available_with_none_data(self):
        """Test that integrated charge is not available when data is None."""
        assert IntegratedChargeService.is_integrated_charge_available(None) is False

    def test_is_integrated_charge_available_with_empty_data(self):
        """Test that integrated charge is not available when data is empty."""
        assert IntegratedChargeService.is_integrated_charge_available({}) is False

    def test_get_integrated_charge_values_with_valid_data(self):
        """Test getting integrated charge values from valid data."""
        results_data = {
            "datasets": [
                {
                    "date": "2022-01-01",
                    "modules": [
                        {
                            "identifier": "PMA0",
                            "channels": [
                                {"name": "CH01", "integratedCharge": 100},
                                {"name": "CH02", "integratedCharge": 150},
                            ],
                        }
                    ],
                },
                {
                    "date": "2022-02-01",
                    "modules": [
                        {
                            "identifier": "PMA0",
                            "channels": [
                                {"name": "CH01", "integratedCharge": 200},
                                {"name": "CH02", "integratedCharge": 250},
                            ],
                        }
                    ],
                },
            ]
        }

        charge_values = IntegratedChargeService.get_integrated_charge_values(
            results_data
        )

        expected = [
            ("2022-01-01", "PMA0", "CH01", 100),
            ("2022-01-01", "PMA0", "CH02", 150),
            ("2022-02-01", "PMA0", "CH01", 200),
            ("2022-02-01", "PMA0", "CH02", 250),
        ]
        assert charge_values == expected

    def test_get_integrated_charge_values_with_missing_charge(self):
        """Test getting integrated charge values when some channels lack charge."""
        results_data = {
            "datasets": [
                {
                    "date": "2022-01-01",
                    "modules": [
                        {
                            "identifier": "PMA0",
                            "channels": [
                                {"name": "CH01", "integratedCharge": 100},
                                {"name": "CH02"},  # Missing integratedCharge
                            ],
                        }
                    ],
                }
            ]
        }

        charge_values = IntegratedChargeService.get_integrated_charge_values(
            results_data
        )

        # Should return empty list when not all channels have charge
        assert charge_values == []

    def test_get_integrated_charge_values_sorted_by_charge(self):
        """Test that integrated charge values are sorted by charge value."""
        results_data = {
            "datasets": [
                {
                    "date": "2022-01-01",
                    "modules": [
                        {
                            "identifier": "PMA0",
                            "channels": [
                                {"name": "CH01", "integratedCharge": 300},
                                {"name": "CH02", "integratedCharge": 100},
                            ],
                        }
                    ],
                }
            ]
        }

        charge_values = IntegratedChargeService.get_integrated_charge_values(
            results_data
        )

        expected = [
            ("2022-01-01", "PMA0", "CH02", 100),
            ("2022-01-01", "PMA0", "CH01", 300),
        ]
        assert charge_values == expected

    def test_get_integrated_charge_for_channel_with_valid_channel(self):
        """Test getting integrated charge for a specific channel."""
        results_data = {
            "datasets": [
                {
                    "date": "2022-01-01",
                    "modules": [
                        {
                            "identifier": "PMA0",
                            "channels": [
                                {"name": "CH01", "integratedCharge": 100},
                                {"name": "CH02", "integratedCharge": 150},
                            ],
                        }
                    ],
                }
            ]
        }

        charge = IntegratedChargeService.get_integrated_charge_for_channel(
            results_data, "2022-01-01", "PMA0", "CH02"
        )

        assert charge == 150

    def test_get_integrated_charge_for_channel_with_invalid_channel(self):
        """Test getting integrated charge for a non-existent channel."""
        results_data = {
            "datasets": [
                {
                    "date": "2022-01-01",
                    "modules": [
                        {
                            "identifier": "PMA0",
                            "channels": [
                                {"name": "CH01", "integratedCharge": 100},
                            ],
                        }
                    ],
                }
            ]
        }

        charge = IntegratedChargeService.get_integrated_charge_for_channel(
            results_data, "2022-01-01", "PMA0", "CH03"
        )

        assert charge is None

    def test_get_integrated_charge_for_channel_with_missing_charge(self):
        """Test getting integrated charge for a channel that has no charge value."""
        results_data = {
            "datasets": [
                {
                    "date": "2022-01-01",
                    "modules": [
                        {
                            "identifier": "PMA0",
                            "channels": [
                                {"name": "CH01", "integratedCharge": 100},
                                {"name": "CH02"},  # No integratedCharge
                            ],
                        }
                    ],
                }
            ]
        }

        charge = IntegratedChargeService.get_integrated_charge_for_channel(
            results_data, "2022-01-01", "PMA0", "CH02"
        )

        assert charge is None

    def test_get_integrated_charge_for_channel_with_none_data(self):
        """Test getting integrated charge with None data."""
        charge = IntegratedChargeService.get_integrated_charge_for_channel(
            None, "2022-01-01", "PMA0", "CH01"
        )
        assert charge is None

    def test_get_integrated_charge_for_channel_with_empty_data(self):
        """Test getting integrated charge with empty data."""
        charge = IntegratedChargeService.get_integrated_charge_for_channel(
            {}, "2022-01-01", "PMA0", "CH01"
        )
        assert charge is None

    def test_get_integrated_charge_for_channel_with_no_datasets_key(self):
        """Test getting integrated charge when datasets key is missing."""
        results_data = {"other_key": "value"}

        charge = IntegratedChargeService.get_integrated_charge_for_channel(
            results_data, "2022-01-01", "PMA0", "CH01"
        )

        assert charge is None

    def test_get_unique_integrated_charge_values(self):
        """Test getting unique integrated charge values."""
        results_data = {
            "datasets": [
                {
                    "date": "2022-01-01",
                    "modules": [
                        {
                            "identifier": "PMA0",
                            "channels": [
                                {"name": "CH01", "integratedCharge": 100},
                                {"name": "CH02", "integratedCharge": 150},
                            ],
                        }
                    ],
                },
                {
                    "date": "2022-02-01",
                    "modules": [
                        {
                            "identifier": "PMA0",
                            "channels": [
                                {"name": "CH01", "integratedCharge": 200},
                                {
                                    "name": "CH02",
                                    "integratedCharge": 100,
                                },  # Duplicate value
                            ],
                        }
                    ],
                },
            ]
        }

        unique_values = IntegratedChargeService.get_unique_integrated_charge_values(
            results_data
        )

        expected = [100, 150, 200]  # Sorted unique values
        assert unique_values == expected
