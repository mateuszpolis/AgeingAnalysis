"""Channel entity for FIT detector ageing analysis."""

import logging
import math
from typing import Any, Dict, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


class Channel:
    """Represents a single channel in a dataset (combination of two columns)."""

    def __init__(
        self,
        name: str,
        signal_data: pd.Series,
        noise_data: pd.Series,
        is_reference: bool = False,
        integrated_charge: Optional[float] = None,
        total_signal_data: Optional[pd.Series] = None,
    ):
        """Initialize a Channel object.

        Args:
            name: Name of the channel in format "CHx", where x is the channel number.
            signal_data: Important Signal Data for the channel.
            noise_data: Noise Data for the channel.
            total_signal_data: Total signal data for the channel.
            is_reference: Whether the channel is a reference channel.
            integrated_charge: Optional integrated charge value for this channel.
        """
        self.name = name
        self.data = signal_data
        self.total_signal_data = (
            total_signal_data if total_signal_data is not None else None
        )
        self.noise_data = noise_data if not is_reference else None
        self.is_reference = is_reference
        self.integrated_charge: Optional[float] = integrated_charge
        self._means: Dict[str, float] = {"gaussian_mean": 0.0, "weighted_mean": 0.0}
        self._ageing_factors: Dict[str, Union[float, str]] = {
            "gaussian_ageing_factor": 0.0,
            "weighted_ageing_factor": 0.0,
            "normalized_gauss_ageing_factor": 0.0,
            "normalized_weighted_ageing_factor": 0.0,
        }

    def get_gaussian_mean(self) -> float:
        """Get the Gaussian mean for the Channel.

        Returns:
            The Gaussian mean.
        """
        return self._means["gaussian_mean"]

    def get_weighted_mean(self) -> float:
        """Get the weighted mean for the Channel.

        Returns:
            The weighted mean.
        """
        return self._means["weighted_mean"]

    def get_gauss_ageing_factor(self) -> Union[float, str]:
        """Get the Gaussian ageing factor for the Channel.

        Returns:
            The Gaussian ageing factor.
        """
        return self._ageing_factors["gaussian_ageing_factor"]

    def get_weighted_ageing_factor(self) -> Union[float, str]:
        """Get the weighted ageing factor for the Channel.

        Returns:
            The weighted ageing factor.
        """
        return self._ageing_factors["weighted_ageing_factor"]

    def set_ageing_factors(
        self, gaussian_ageing_factor: float, weighted_ageing_factor: float
    ):
        """Set the Gaussian and weighted ageing factors for the Channel.

        Args:
            gaussian_ageing_factor: Gaussian ageing factor.
            weighted_ageing_factor: Weighted ageing factor.
        """
        self._ageing_factors.update(
            {
                "gaussian_ageing_factor": gaussian_ageing_factor,
                "weighted_ageing_factor": weighted_ageing_factor,
            }
        )

    def set_normalized_ageing_factors(self, divisors: Dict[str, float]):
        """Set the normalized Gaussian and weighted ageing factors for the Channel.

        Args:
            divisors: Dictionary containing divisors for normalization.
        """
        try:
            gauss_factor = self.get_gauss_ageing_factor()
            if isinstance(gauss_factor, str):
                self._ageing_factors["normalized_gauss_ageing_factor"] = "N/A"
            else:
                self._ageing_factors["normalized_gauss_ageing_factor"] = (
                    gauss_factor / divisors["gaussian_divisor"]
                )
            weighted_factor = self.get_weighted_ageing_factor()
            if isinstance(weighted_factor, str):
                self._ageing_factors["normalized_weighted_ageing_factor"] = "N/A"
            else:
                self._ageing_factors["normalized_weighted_ageing_factor"] = (
                    weighted_factor / divisors["weighted_divisor"]
                )
        except (KeyError, ZeroDivisionError, TypeError):
            self._ageing_factors["normalized_gauss_ageing_factor"] = "N/A"
            self._ageing_factors["normalized_weighted_ageing_factor"] = "N/A"

    def set_means(self, gaussian_mean: float, weighted_mean: float):
        """Set the Gaussian and weighted means for the Channel.

        Args:
            gaussian_mean: Gaussian mean.
            weighted_mean: Weighted mean.
        """
        self._means.update(
            {"gaussian_mean": gaussian_mean, "weighted_mean": weighted_mean}
        )

    def get_integrated_charge(self) -> Optional[float]:
        """Get the integrated charge value for the channel.

        Returns:
            The integrated charge value or None if not set.
        """
        return self.integrated_charge

    def to_dict(self) -> Dict:
        """Convert the Channel to a dictionary.

        Returns:
            Dictionary representation of the channel.
        """
        if math.isnan(self._means["gaussian_mean"]) or math.isnan(
            self._means["weighted_mean"]
        ):
            return {"name": self.name, "means": "N/A", "ageing_factors": "N/A"}

        channel_dict: Dict[str, Any] = {
            "name": self.name,
            "means": self._means,
            "ageing_factors": self._ageing_factors,
        }

        if self.integrated_charge is not None:
            channel_dict["integratedCharge"] = self.integrated_charge

        return channel_dict

    def __str__(self):
        """Return string representation of the Channel."""
        channel_id = int(self.name[2:])
        first_column, second_column = channel_id * 2 - 1, channel_id * 2
        charge_info = (
            f", integrated_charge={self.integrated_charge}"
            if self.integrated_charge is not None
            else ""
        )
        return (
            f"Channel(name={self.name}, columns=({first_column}, {second_column}), "
            f"is_reference={self.is_reference}{charge_info})"
        )

    def __repr__(self):
        """Return string representation of the Channel."""
        return str(self)
