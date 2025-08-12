"""Integrated charge service for FIT detector ageing analysis."""

import copy
import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from ageing_analysis.entities.config import Config
from ageing_analysis.services.cfd_rate_integration_service import (
    CFDRateIntegrationService,
)

from ..utils.normalization import normalize_channel_name, normalize_pm_name

logger = logging.getLogger(__name__)


class IntegratedChargeService:
    """Service for handling integrated charge operations."""

    def __init__(self):
        """Initialize the IntegratedChargeService."""
        self.cfd_rate_integration_service = CFDRateIntegrationService()

    @staticmethod
    def normalize_channel_name(channel_name: str) -> str:
        """Normalize channel name to standard format.

        This function handles various channel name formats and converts them to
        the standard format used by the application (e.g., "CH01").

        Args:
            channel_name: The channel name to normalize

        Returns:
            Normalized channel name in standard format (e.g., "CH01")
        """
        return normalize_channel_name(channel_name)

    @staticmethod
    def normalize_pm_name(pm_name: str) -> str:
        """Normalize PM name to standard format.

        Args:
            pm_name: The PM name to normalize (e.g., "PMA0", "pma0")

        Returns:
            Normalized PM name in standard format (e.g., "PMA0")
        """
        return normalize_pm_name(pm_name)

    @staticmethod
    def is_integrated_charge_available(results_data: Dict) -> bool:
        """Check if integrated charge is available for all channels in all datasets.

        Args:
            results_data: The analysis results data.

        Returns:
            True if integrated charge is available for all channels in all datasets.
        """
        if not results_data or "datasets" not in results_data:
            return False

        datasets = results_data["datasets"]
        if not datasets:
            return False

        # Check if all datasets have integrated charge for all channels
        for dataset in datasets:
            for module in dataset.get("modules", []):
                for channel in module.get("channels", []):
                    if "integratedCharge" not in channel:
                        return False

        logger.debug("Integrated charge is available for all channels in all datasets")
        return True

    @staticmethod
    def get_integrated_charge_values(
        results_data: Dict,
    ) -> List[Tuple[str, str, str, float]]:
        """Get integrated charge values for all channels in all datasets.

        Args:
            results_data: The analysis results data.

        Returns:
            List of tuples (date, module_id, channel_name, integrated_charge).
        """
        if not IntegratedChargeService.is_integrated_charge_available(results_data):
            return []

        datasets = results_data["datasets"]
        charge_values = []

        for dataset in datasets:
            date = dataset.get("date", "unknown")
            for module in dataset.get("modules", []):
                module_id = module.get("identifier", "unknown")
                for channel in module.get("channels", []):
                    channel_name = channel.get("name", "unknown")
                    integrated_charge = channel.get("integratedCharge")
                    if integrated_charge is not None:
                        charge_values.append(
                            (date, module_id, channel_name, integrated_charge)
                        )

        # Sort by integrated charge value
        charge_values.sort(key=lambda x: x[3])

        logger.debug(
            f"Found {len(charge_values)} channels with integrated charge values"
        )
        return charge_values

    @staticmethod
    def get_integrated_charge_for_channel(
        results_data: Dict, date: str, module_id: str, channel_name: str
    ) -> Optional[float]:
        """Get integrated charge value for a specific channel.

        Args:
            results_data: The analysis results data.
            date: The date to look up.
            module_id: The module identifier.
            channel_name: The channel name.

        Returns:
            The integrated charge value for the channel, or None if not found.
        """
        if not results_data or "datasets" not in results_data:
            return None

        datasets = results_data["datasets"]

        for dataset in datasets:
            if dataset.get("date") == date:
                for module in dataset.get("modules", []):
                    if module.get("identifier") == module_id:
                        for channel in module.get("channels", []):
                            if channel.get("name") == channel_name:
                                charge = channel.get("integratedCharge")
                                return float(charge) if charge is not None else None

        return None

    @staticmethod
    def get_unique_integrated_charge_values(results_data: Dict) -> List[float]:
        """Get unique integrated charge values across all channels and datasets.

        Args:
            results_data: The analysis results data.

        Returns:
            List of unique integrated charge values, sorted.
        """
        charge_values = IntegratedChargeService.get_integrated_charge_values(
            results_data
        )
        unique_values = list({value[3] for value in charge_values})
        unique_values.sort()
        return unique_values

    def integrate_charge_for_config(
        self,
        config: Config,
        progress_callback=None,
        include_range_correction: bool = True,
        use_latest_available_configuration: bool = False,
    ) -> None:
        """Integrate charge for a config.

        Args:
            config: The config to integrate charge for.
            progress_callback: Optional callback function to report progress.
            include_range_correction: Whether to apply range-correction to
                integrated charge values during computation. If True, values are
                adjusted by detector-specific range correction factors.
            use_latest_available_configuration: When range-correction data is
                missing for an integration period, attempt to fall back to the
                latest available configuration prior to the period.
        """
        current_integrated_charge = (
            self.cfd_rate_integration_service.get_empty_pm_channel_dict(
                include_pmc9=True
            )
        )
        sorted_datasets = sorted(config.datasets, key=lambda x: x.date)
        total_datasets = len(sorted_datasets)

        # For the first dataset, save a copy of the initial (empty) integrated charge
        first_dataset_charge = copy.deepcopy(current_integrated_charge)
        sorted_datasets[0].save_integrated_charge(first_dataset_charge)

        if progress_callback:
            progress_callback(
                0, f"Initialized integrated charge for {sorted_datasets[0].date}"
            )

        for i in range(1, len(sorted_datasets)):
            start_date: date = datetime.strptime(
                str(sorted_datasets[i - 1].date), "%Y-%m-%d"
            ).date()

            end_date: date = datetime.strptime(
                str(sorted_datasets[i].date), "%Y-%m-%d"
            ).date()

            if progress_callback:
                progress = (i / total_datasets) * 100
                progress_callback(
                    progress,
                    f"Getting integrated charge from {start_date} to {end_date} "
                    f"(Dataset {i+1} of {total_datasets})",
                )

            integrated_cfd_rate_fn = (
                self.cfd_rate_integration_service.get_integrated_cfd_rate
            )
            integrated_charge = integrated_cfd_rate_fn(
                start_date,
                end_date,
                multiply_by_mu=True,
                include_range_correction=include_range_correction,
                use_latest_available_configuration=use_latest_available_configuration,
            )

            # Do not log actual values to avoid leaking sensitive data

            # Add the new integrated charge to the cumulative total
            for pm, channels in integrated_charge.items():
                for channel, value in channels.items():
                    current_integrated_charge[pm][channel] += value

            # Save a copy of the current cumulative integrated charge for this dataset
            dataset_charge = copy.deepcopy(current_integrated_charge)
            sorted_datasets[i].save_integrated_charge(dataset_charge)

            if progress_callback:
                progress = ((i + 1) / total_datasets) * 100
                progress_callback(
                    progress,
                    f"Completed integrated charge for {sorted_datasets[i].date}",
                )

        if progress_callback:
            progress_callback(100, "Saving configuration...")

        config.save()

        if progress_callback:
            progress_callback(
                100, "Integrated charge calculation completed successfully!"
            )
