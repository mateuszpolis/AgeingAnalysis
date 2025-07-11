"""Data normalization service for FIT detector ageing analysis."""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class DataNormalizer:
    """Normalizes ageing calculation results."""

    def __init__(self, config):
        """Initialize the data normalizer.

        Args:
            config: Configuration object containing datasets.
        """
        self.config = config

    def _get_divisors(self, dataset) -> Dict[str, Dict[str, Dict[str, float]]]:
        """Get the divisors (first ageing factors) for the dataset.

        Args:
            dataset: Dataset to get the divisors from.

        Returns:
            Dictionary with stored divisors accessed by module identifier, channel name,
            and 'gaussian_divisor' or 'weighted_divisor'.
        """
        divisors: Dict[str, Dict[str, Dict[str, float]]] = {}
        for module in dataset.modules:
            divisors[module.identifier] = {}
            for channel in module.channels:
                divisors[module.identifier][channel.name] = {}
                gauss_factor = channel.get_gauss_ageing_factor()
                if isinstance(gauss_factor, str):
                    divisors[module.identifier][channel.name]["gaussian_divisor"] = 0.0
                else:
                    divisors[module.identifier][channel.name][
                        "gaussian_divisor"
                    ] = gauss_factor
                weighted_factor = channel.get_weighted_ageing_factor()
                if isinstance(weighted_factor, str):
                    divisors[module.identifier][channel.name]["weighted_divisor"] = 0.0
                else:
                    divisors[module.identifier][channel.name][
                        "weighted_divisor"
                    ] = weighted_factor
                logger.debug(f"Calculated divisors for: {channel}")
            logger.debug(f"Calculated divisors for module: {module}")

        logger.info("Successfully calculated divisors")
        return divisors

    def normalize_data(self):
        """Normalize the ageing calculation results."""
        divisors = self._get_divisors(self.config.datasets[0])

        for dataset in self.config.datasets:
            for module in dataset.modules:
                for channel in module.channels:
                    channel.set_normalized_ageing_factors(
                        divisors[module.identifier][channel.name]
                    )
                    logger.debug(f"Normalized data for channel: {channel}")
                logger.debug(f"Normalized data for module: {module}")
            logger.debug(f"Normalized data for dataset: {dataset}")

        logger.info("Normalized all data")
