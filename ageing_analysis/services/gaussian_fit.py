"""Gaussian fitting service for FIT detector ageing analysis."""

import logging
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import OptimizeWarning, curve_fit

logger = logging.getLogger(__name__)


class GaussianFitService:
    """A class to fit Gaussian distributions to data and calculate weighted means."""

    def __init__(self, dataset):
        """Initialize the service with the processed data for each processing module.

        Args:
            dataset: The dataset object containing processed data for each module.
        """
        self.dataset = dataset

    def gaussian(
        self, x: np.ndarray, amplitude: float, mean: float, stddev: float
    ) -> np.ndarray:
        """Calculate a Gaussian distribution for the given x values.

        Args:
            x: The x values to calculate the Gaussian distribution for.
            amplitude: The amplitude of the Gaussian distribution.
            mean: The mean of the Gaussian distribution.
            stddev: The standard deviation of the Gaussian distribution.

        Returns:
            The Gaussian distribution values for the given x values.
        """
        return amplitude * np.exp(-((x - mean) ** 2) / (2 * stddev**2))

    def fit_gaussian(self, data_series: pd.Series, is_reference: bool = False) -> float:
        """Fit a Gaussian distribution to the data and return the mean.

        Args:
            data_series: Summed signal data for a specific channel pair.
            is_reference: Whether the data belongs to a reference channel.

        Returns:
            The mean of the Gaussian distribution fit, or NaN if the fit fails.
        """
        if data_series.sum() == 0:
            logger.warning("Sum of values is zero. Cannot fit Gaussian distribution.")
            return 0

        x_data = np.arange(len(data_series))
        y_data = data_series.values

        initial_guess = [
            max(y_data),
            np.sum(x_data * y_data) / np.sum(y_data),
            np.std(x_data),
        ]

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", OptimizeWarning)
                print(f"Initial guess: {initial_guess}")
                params, _ = curve_fit(self.gaussian, x_data, y_data, p0=initial_guess)
                print(f"Params: {params}")
            return float(params[1])  # Gaussian mean
        except (OptimizeWarning, RuntimeError):
            logger.warning("Gaussian fit failed or covariance could not be estimated.")
            return 0

    def calculate_weighted_mean(
        self, data_series: pd.Series, is_reference: bool = False
    ) -> float:
        """Calculate the weighted mean of the data series.

        Args:
            data_series: Summed signal data for a specific channel pair.
            is_reference: Whether the data belongs to a reference channel.

        Returns:
            The weighted mean of the data series, or NaN if calculation fails.
        """
        if data_series.sum() == 0:
            logger.warning("Sum of values is zero. Cannot calculate weighted mean.")
            return 0

        x_data = np.arange(len(data_series))
        if is_reference:
            x_data += 100  # Adjust x_data for reference channels
        values = data_series.values

        return float(np.sum(x_data * values) / np.sum(values))

    def process_all_modules(self):
        """Process all modules and calculate Gaussian fits and weighted means."""
        logger.debug("Applying Gaussian fit and calculating weighted means...")

        warning_count = 0
        for module in self.dataset.modules:
            module_warning_count = 0

            for channel in module.channels:
                is_reference = channel.is_reference

                # Try Gaussian fit with data
                gaussian_mean = self.fit_gaussian(channel.data, is_reference)
                if gaussian_mean == 0 and channel.noise_data is not None:
                    logger.warning("Retrying Gaussian fit with noise data.")
                    gaussian_mean = self.fit_gaussian(channel.noise_data, is_reference)

                # Try weighted mean
                weighted_mean = self.calculate_weighted_mean(channel.data, is_reference)
                if weighted_mean == 0 and channel.noise_data is not None:
                    logger.warning(
                        "Retrying weighted mean calculation with noise data."
                    )
                    weighted_mean = self.calculate_weighted_mean(
                        channel.noise_data, is_reference
                    )

                channel.set_means(gaussian_mean, weighted_mean)

                if gaussian_mean == 0 or weighted_mean == 0:
                    module_warning_count += 1

                logger.debug(
                    f"Processed {module.identifier} - channel: {channel} "
                    f"Gaussian mean = {gaussian_mean}, Weighted mean = {weighted_mean}"
                )

            if module_warning_count > 0:
                logger.warning(
                    f"Gaussian fit and weighted mean calculation completed with "
                    f"{module_warning_count} warnings for {module}."
                )
            else:
                logger.debug(
                    f"Gaussian fit and weighted mean calculation completed "
                    f"successfully "
                    f"with no warnings for {module}."
                )

            warning_count += module_warning_count

        if warning_count > 0:
            logger.warning(
                f"Gaussian fit and weighted mean calculation completed with "
                f"{warning_count} warnings."
            )
        else:
            logger.debug(
                "Gaussian fit and weighted mean calculation completed successfully "
                "with no warnings."
            )
