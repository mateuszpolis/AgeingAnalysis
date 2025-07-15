"""Module entity for FIT detector ageing analysis."""

import logging
import os
from typing import Dict, List, Optional

import pandas as pd

from ..utils.normalization import normalize_channel_name
from ..utils.validation import validate_csv
from .channel import Channel

logger = logging.getLogger(__name__)


class Module:
    """Represents an individual PM module."""

    def __init__(
        self,
        path: str,
        identifier: str,
        is_reference: bool = False,
        ref_channels: Optional[List[int]] = None,
        validate_header: bool = False,
        integrated_charge_data: Optional[Dict[str, Dict[str, float]]] = None,
    ):
        """Initialize a module and validate its file.

        Args:
            path: Path to the PM file.
            identifier: Identifier for the module.
            is_reference: Whether the module is a reference.
            ref_channels: List of reference channels.
            validate_header: Whether to validate the header in the file.
            integrated_charge_data: Optional integrated charge data for channels.

        Raises:
            Exception: If the file does not exist or is not a valid CSV.
        """
        self.path: str = path
        self.identifier: str = identifier
        self.is_reference: bool = is_reference
        self.ref_channels: List[int] = ref_channels or []
        self.channels: List[Channel] = []
        self._ref_channel_pointers: List[Channel] = []
        self.integrated_charge_data: Optional[
            Dict[str, Dict[str, float]]
        ] = integrated_charge_data

        # Validate file existence and format
        if not os.path.exists(path):
            raise FileNotFoundError(f"File {path} for {identifier} does not exist")

        if not validate_csv(path, validate_header):
            raise Exception(f"File {path} for {identifier} is not valid")

        logger.debug(f"Module {identifier} loaded successfully from {path}")

    def add_channel(
        self,
        channel_number: int,
        signal_data: pd.Series,
        noise_data: pd.Series,
        total_signal_data: pd.Series,
    ):
        """Add a channel to the module.

        Args:
            channel_number: Channel number.
            signal_data: Signal data for the channel.
            noise_data: Noise data for the channel.
            total_signal_data: Total signal data for the channel.
        """
        channel_name = f"CH{channel_number:02d}"  # Format as CH01, CH02, etc.
        is_ref_channel = self.is_reference and channel_number in self.ref_channels

        # Get integrated charge for this channel if available
        integrated_charge = None
        if (
            self.integrated_charge_data
            and self.identifier in self.integrated_charge_data
        ):
            pm_charge_data = self.integrated_charge_data[self.identifier]

            # Try to find the channel with normalized names
            normalized_channel_name = normalize_channel_name(channel_name)

            # Look for the channel in the charge data using normalized names
            for config_channel_name, charge_value in pm_charge_data.items():
                normalized_config_name = normalize_channel_name(config_channel_name)
                if normalized_config_name == normalized_channel_name:
                    integrated_charge = charge_value
                    logger.debug(
                        f"Found integrated charge {charge_value} for channel "
                        f"{channel_name} (config: {config_channel_name})"
                    )
                    break

        channel = Channel(
            channel_name,
            signal_data,
            noise_data,
            is_ref_channel,
            integrated_charge,
            total_signal_data,
        )

        # Add channel to the main list
        self.channels.append(channel)

        # If this is a reference channel, add it to the reference pointers list
        if is_ref_channel:
            self._ref_channel_pointers.append(channel)

    def get_reference_channels(self) -> List[Channel]:
        """Retrieve all reference channels for quick access.

        Returns:
            List of reference channels in this module.
        """
        return self._ref_channel_pointers

    def to_dict(
        self, include_signal_data: bool = False, include_total_signal_data: bool = True
    ) -> Dict:
        """Convert the module to a dictionary.

        Args:
            include_signal_data: Whether to include signal data in the output.
            include_total_signal_data: Whether to include total signal in the output.

        Returns:
            Dictionary representation of the module.
        """
        return {
            "identifier": self.identifier,
            "channels": [
                channel.to_dict(include_signal_data, include_total_signal_data)
                for channel in self.channels
            ],
        }

    def __str__(self):
        """Return string representation of the Module."""
        return (
            f"Module(identifier={self.identifier}, path={self.path}, "
            f"is_reference={self.is_reference})"
        )

    def __repr__(self):
        """Return string representation of the Module."""
        return str(self)
