"""Reference channel service for FIT detector ageing analysis."""

import logging
import math

logger = logging.getLogger(__name__)


class ReferenceChannelService:
    """Calculate reference Gaussian and weighted means across reference channels."""

    def __init__(self, dataset):
        """Initialize the service with the reference module.

        Args:
            dataset: The dataset containing the reference module.
        """
        self.dataset = dataset
        self.reference_module = dataset.get_reference_module()

    def calculate_reference_means(self) -> None:
        """Calculate the reference means across reference channels.

        Raises:
            ValueError: If the reference channels contain insufficient data.
            ValueError: If the reference channels contain no data for calculation.
        """
        logger.debug("Calculating reference Gaussian and weighted means...")

        gaussian_means = []
        weighted_means = []

        # Extract Gaussian and weighted means from the reference channels
        logger.info(
            f"Extracting reference means from reference module: {self.reference_module}"
        )
        for channel in self.reference_module.get_reference_channels():
            logger.info(f"Extracting reference means from reference channel: {channel}")
            gaussian_mean = channel.get_gaussian_mean()
            weighted_mean = channel.get_weighted_mean()
            if (
                gaussian_mean is None
                or weighted_mean is None
                or isinstance(gaussian_mean, float)
                and math.isnan(gaussian_mean)
                or isinstance(weighted_mean, float)
                and math.isnan(weighted_mean)
            ):
                logger.warning(
                    f"Reference channel: {channel} contains None or NaN values."
                )
                continue
            gaussian_means.append(gaussian_mean)
            weighted_means.append(weighted_mean)

        # Check if there is sufficient data to calculate
        if len(gaussian_means) != len(weighted_means):
            raise ValueError(
                f"Reference channels contain insufficient data for calculation. "
                f"Gaussian means: {len(gaussian_means)}, "
                f"Weighted means: {len(weighted_means)}"
            )
        elif len(gaussian_means) == 0:
            raise ValueError("Reference channels contain no data for calculation.")

        # Calculate the arithmetic mean for Gaussian and weighted means
        reference_gaussian_mean = sum(gaussian_means) / len(gaussian_means)
        reference_weighted_mean = sum(weighted_means) / len(weighted_means)

        logger.info("Finished calculating reference Gaussian and weighted means.")
        logger.info(
            f"Reference Gaussian mean: {reference_gaussian_mean}, "
            f"Reference Weighted mean: {reference_weighted_mean}"
        )

        self.dataset.set_reference_means(
            reference_gaussian_mean, reference_weighted_mean
        )
