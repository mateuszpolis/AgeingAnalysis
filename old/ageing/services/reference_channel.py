import math

from configs.logger_config import logger
from fit_detector.apps.ageing.entities.dataset import Dataset


class ReferenceChannelService:
    """A class to calculate reference Gaussian and weighted means across reference channels."""

    def __init__(self, dataset: Dataset):
        """Initialize the service with the reference module.

        Args:
            dataset (Dataset): The dataset containing the reference module.
        """
        self.dataset = dataset
        self.reference_module = dataset.get_reference_module()

    def calculate_reference_means(self):
        """Calculate the reference Gaussian and weighted means across reference channels.

        Raises:
            ValueError: If the reference channels contain insufficient data for calculation.
            ValueError: If the reference channels contain no data for calculation.
        """

        logger.debug("Calculating reference Gaussian and weighted means...")

        gaussian_means = []
        weighted_means = []

        # Extract Gaussian and weighted means from the reference channels
        for channel in self.reference_module.get_reference_channels():
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
                logger.warning(f"Reference channel: {channel} contains None or NaN values.")
                continue
            gaussian_means.append(gaussian_mean)
            weighted_means.append(weighted_mean)

        # Check if there is sufficient data to calculate
        if len(gaussian_means) != len(weighted_means):
            raise ValueError(
                f"Reference channels contain insufficient data for calculation. "
                f"Gaussian means: {len(gaussian_means)}, Weighted means: {len(weighted_means)}"
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

        self.dataset.set_reference_means(reference_gaussian_mean, reference_weighted_mean)
