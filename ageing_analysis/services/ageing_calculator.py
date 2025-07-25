"""Ageing calculation service for FIT detector ageing analysis."""

import logging

from ageing_analysis.entities.dataset import Dataset

logger = logging.getLogger(__name__)


class AgeingCalculationService:
    """Service to calculate ageing factors for dataset channels."""

    def __init__(self, dataset: Dataset):
        """Initialize the ageing calculation service.

        Args:
            dataset: The dataset to process.
        """
        self.dataset = dataset
        self.reference_gaussian_mean = dataset.get_reference_gaussian_mean()
        self.reference_weighted_mean = dataset.get_reference_weighted_mean()

    def calculate_ageing_factors(self):
        """Calculate the ageing factors for all channels in the dataset."""
        logger.debug("Calculating ageing factors...")

        for module in self.dataset.modules:
            logger.debug(f"Calculating ageing factors for {module.identifier}...")
            for channel in module.channels:
                # Calculate the ageing factors
                gaussian_ageing_factor = (
                    channel.get_gaussian_mean() / self.reference_gaussian_mean
                )
                weighted_ageing_factor = (
                    channel.get_weighted_mean() / self.reference_weighted_mean
                )

                channel.set_ageing_factors(
                    gaussian_ageing_factor, weighted_ageing_factor
                )
                logger.debug(
                    f"{module.identifier} - {channel}: Gaussian Ageing Factor"
                    f" = {gaussian_ageing_factor}, "
                    f"Weighted Ageing Factor = {weighted_ageing_factor}"
                )

            logger.debug(f"Ageing factors calculated for {module.identifier}.")

        logger.info(
            f"Ageing factors calculated successfully for dataset {self.dataset.date}."
        )
