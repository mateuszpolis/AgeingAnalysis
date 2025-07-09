import warnings

import numpy as np
import pandas as pd
from scipy.optimize import OptimizeWarning, curve_fit

from configs.logger_config import logger
from fit_detector.apps.ageing.entities.dataset import Dataset


class GaussianFitService:
    """A class to fit Gaussian distributions to data and calculate weighted means."""

    def __init__(self, dataset: Dataset):
        """Initialize the service with the processed data for each processing module.

        Args:
            dataset (Dataset): The dataset object containing processed data for each module.
        """
        self.dataset = dataset

    def gaussian(self, x: np.ndarray, amplitude: float, mean: float, stddev: float) -> np.ndarray:
        """Calculate a Gaussian distribution for the given x values.

        Args:
            x (np.ndarray): The x values to calculate the Gaussian distribution for.
            amplitude (float): The amplitude of the Gaussian distribution.
            mean (float): The mean of the Gaussian distribution.
            stddev (float): The standard deviation of the Gaussian distribution.

        Returns:
            np.ndarray: The Gaussian distribution values for the given x values.
        """
        return amplitude * np.exp(-((x - mean) ** 2) / (2 * stddev**2))

    def fit_gaussian(self, data_series: pd.Series, is_reference: bool = False) -> float:
        """Fit a Gaussian distribution to the data and return the mean.

        Args:
            data_series (pd.Series): Summed signal data for a specific channel pair.
            is_reference (bool): Whether the data belongs to a reference channel.

        Returns:
            float: The mean of the Gaussian distribution fit to the data, or NaN if the fit fails.
        """
        if data_series.sum() == 0:
            logger.warning("Sum of values is zero. Cannot fit Gaussian distribution.")
            return np.nan

        x_data = np.arange(len(data_series))
        if is_reference:
            x_data += 100  # Adjust x_data for reference channels
        y_data = data_series.values

        initial_guess = [
            max(y_data),
            np.sum(x_data * y_data) / np.sum(y_data),
            np.std(x_data),
        ]

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", OptimizeWarning)
                params, _ = curve_fit(self.gaussian, x_data, y_data, p0=initial_guess)
            return params[1]  # Gaussian mean
        except (OptimizeWarning, RuntimeError):
            logger.warning("Gaussian fit failed or covariance could not be estimated.")
            return np.nan

    def calculate_weighted_mean(self, data_series: pd.Series, is_reference: bool = False) -> float:
        """Calculate the weighted mean of the data series.

        Args:
            data_series (pd.Series): Summed signal data for a specific channel pair.
            is_reference (bool): Whether the data belongs to a reference channel.

        Returns:
            float: The weighted mean of the data series, or NaN if calculation fails.
        """
        if data_series.sum() == 0:
            logger.warning("Sum of values is zero. Cannot calculate weighted mean.")
            return np.nan

        x_data = np.arange(len(data_series))
        if is_reference:
            x_data += 100  # Adjust x_data for reference channels
        values = data_series.values

        return np.sum(x_data * values) / np.sum(values)

    def process_all_modules(self):
        """Process all modules and calculate Gaussian fits and weighted means for each channel."""
        logger.debug("Applying Gaussian fit and calculating weighted means...")

        warning_count = 0
        for module in self.dataset.modules:
            module_warning_count = 0

            for channel in module.channels:
                is_reference = channel.is_reference

                # Try Gaussian fit
                gaussian_mean = self.fit_gaussian(channel.data, is_reference)
                if np.isnan(gaussian_mean) and channel.noise_data is not None:
                    logger.warning("Retrying Gaussian fit with noise data.")
                    gaussian_mean = self.fit_gaussian(channel.noise_data, is_reference)

                # Try weighted mean
                weighted_mean = self.calculate_weighted_mean(channel.data, is_reference)
                if np.isnan(weighted_mean) and channel.noise_data is not None:
                    logger.warning("Retrying weighted mean calculation with noise data.")
                    weighted_mean = self.calculate_weighted_mean(channel.noise_data, is_reference)

                channel.set_means(gaussian_mean, weighted_mean)

                if np.isnan(gaussian_mean) or np.isnan(weighted_mean):
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
                    f"Gaussian fit and weighted mean calculation completed successfully "
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
