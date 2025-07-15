"""Tests for Channel entity integrated charge functionality."""


import pandas as pd

from ageing_analysis.entities.channel import Channel


class TestChannelIntegratedCharge:
    """Test cases for Channel integrated charge functionality."""

    def test_channel_constructor_with_integrated_charge(self):
        """Test Channel constructor with integrated charge."""
        signal_data = pd.Series([1, 2, 3])
        noise_data = pd.Series([0.1, 0.2, 0.3])

        channel = Channel(
            name="CH01",
            signal_data=signal_data,
            noise_data=noise_data,
            is_reference=False,
            integrated_charge=150.5,
        )

        assert channel.name == "CH01"
        assert channel.integrated_charge == 150.5

    def test_channel_constructor_without_integrated_charge(self):
        """Test Channel constructor without integrated charge."""
        signal_data = pd.Series([1, 2, 3])
        noise_data = pd.Series([0.1, 0.2, 0.3])

        channel = Channel(
            name="CH01",
            signal_data=signal_data,
            noise_data=noise_data,
            is_reference=False,
        )

        assert channel.name == "CH01"
        assert channel.integrated_charge is None

    def test_channel_to_dict_with_integrated_charge(self):
        """Test Channel to_dict method includes integrated charge when present."""
        signal_data = pd.Series([1, 2, 3])
        noise_data = pd.Series([0.1, 0.2, 0.3])

        channel = Channel(
            name="CH01",
            signal_data=signal_data,
            noise_data=noise_data,
            is_reference=False,
            integrated_charge=200.0,
        )

        # Set some means to avoid N/A return
        channel.set_means(1.5, 1.6)

        result = channel.to_dict()

        assert result["name"] == "CH01"
        assert result["integratedCharge"] == 200.0
        assert "means" in result
        assert "ageing_factors" in result

    def test_channel_to_dict_without_integrated_charge(self):
        """Test Channel to_dict method excludes integrated charge when not present."""
        signal_data = pd.Series([1, 2, 3])
        noise_data = pd.Series([0.1, 0.2, 0.3])

        channel = Channel(
            name="CH01",
            signal_data=signal_data,
            noise_data=noise_data,
            is_reference=False,
        )

        # Set some means to avoid N/A return
        channel.set_means(1.5, 1.6)

        result = channel.to_dict()

        assert result["name"] == "CH01"
        assert "integratedCharge" not in result

    def test_channel_str_with_integrated_charge(self):
        """Test Channel __str__ method includes integrated charge when present."""
        signal_data = pd.Series([1, 2, 3])
        noise_data = pd.Series([0.1, 0.2, 0.3])

        channel = Channel(
            name="CH01",
            signal_data=signal_data,
            noise_data=noise_data,
            is_reference=False,
            integrated_charge=300.0,
        )

        result = str(channel)

        assert "CH01" in result
        assert "integrated_charge=300.0" in result

    def test_channel_str_without_integrated_charge(self):
        """Test Channel __str__ method excludes integrated charge when not present."""
        signal_data = pd.Series([1, 2, 3])
        noise_data = pd.Series([0.1, 0.2, 0.3])

        channel = Channel(
            name="CH01",
            signal_data=signal_data,
            noise_data=noise_data,
            is_reference=False,
        )

        result = str(channel)

        assert "CH01" in result
        assert "integrated_charge=" not in result

    def test_channel_with_zero_integrated_charge(self):
        """Test Channel handles zero integrated charge correctly."""
        signal_data = pd.Series([1, 2, 3])
        noise_data = pd.Series([0.1, 0.2, 0.3])

        channel = Channel(
            name="CH01",
            signal_data=signal_data,
            noise_data=noise_data,
            is_reference=False,
            integrated_charge=0.0,
        )

        assert channel.integrated_charge == 0.0

        # Set some means to avoid N/A return
        channel.set_means(1.5, 1.6)

        result = channel.to_dict()
        assert result["integratedCharge"] == 0.0
