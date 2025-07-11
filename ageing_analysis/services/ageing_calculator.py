"""Ageing calculation service for FIT detector ageing analysis."""

import logging

logger = logging.getLogger(__name__)


class AgeingCalculationService:
    """Service to calculate ageing factors for dataset channels."""

    def __init__(
        self,
        dataset,
        reference_gaussian_mean: float,
        reference_weighted_mean: float,
    ):
        """Initialize the ageing calculation service.

        Args:
            dataset: The dataset to process.
            reference_gaussian_mean: Reference Gaussian mean for normalization.
            reference_weighted_mean: Reference weighted mean for normalization.
        """
        self.dataset = dataset
        self.reference_gaussian_mean = reference_gaussian_mean
        self.reference_weighted_mean = reference_weighted_mean

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
