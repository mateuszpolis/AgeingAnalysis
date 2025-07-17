"""Gaussian fitting service for FIT detector ageing analysis."""

import logging
import os
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import OptimizeWarning, curve_fit

logger = logging.getLogger(__name__)


class GaussianFitService:
    """A class to fit Gaussian distributions to data and calculate weighted means."""

    def __init__(self, dataset, debug_mode: bool = False):
        """Initialize the service with the processed data for each processing module.

        Args:
            dataset: The dataset object containing processed data for each module.
            debug_mode: Whether to create debug plots (default: False).
        """
        self.dataset = dataset
        self.debug_mode = debug_mode

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

    def _create_debug_plot(
        self,
        data_series: pd.Series,
        params: np.ndarray,
        module_id: str,
        channel_name: str,
        is_reference: bool = False,
        fit_successful: bool = True,
    ):
        """Create a debug plot showing the signal data and Gaussian fit.

        Args:
            data_series: The signal data series.
            params: The fitted Gaussian parameters [amplitude, mean, stddev].
            module_id: The module identifier.
            channel_name: The channel name.
            is_reference: Whether this is a reference channel.
            fit_successful: Whether the Gaussian fit was successful.
        """
        if not self.debug_mode:
            return

        # Create debug folder: debug_plots/gaussian_fit/{dataset_date}/{module_id}/
        debug_folder = f"debug_plots/gaussian_fit/{self.dataset.date}/{module_id}"
        os.makedirs(debug_folder, exist_ok=True)

        plt.figure(figsize=(12, 8))

        x_data = np.arange(len(data_series))
        y_data = data_series.values

        # --- ZOOM LOGIC ---
        # Find region of interest (ROI) where signal is significant
        threshold = max(np.max(y_data) * 0.01, 1e-6)  # 1% of max or tiny value
        nonzero_indices = np.where(y_data > threshold)[0]
        if len(nonzero_indices) > 0:
            left = max(nonzero_indices[0] - 5, 0)
            right = min(nonzero_indices[-1] + 5, len(y_data) - 1)
        else:
            left, right = 0, len(y_data) - 1

        # Plot the original signal data (zoomed)
        plt.plot(
            x_data[left : right + 1],
            y_data[left : right + 1],
            "b-",
            linewidth=2,
            label="Signal Data",
            alpha=0.7,
        )

        if fit_successful and params is not None:
            # Generate smooth curve for the Gaussian fit (zoomed)
            x_smooth = np.linspace(left, right, 1000)
            y_fit = self.gaussian(x_smooth, params[0], params[1], params[2])
            plt.plot(
                x_smooth, y_fit, "r-", linewidth=2, label="Gaussian Fit", alpha=0.8
            )
            plt.axvline(
                x=params[1],
                color="red",
                linestyle="--",
                linewidth=2,
                label=f"Fitted Mean: {params[1]:.2f}",
            )
            fit_info = (
                f"Gaussian Fit Parameters:\n"
                f"Amplitude: {params[0]:.2f}\n"
                f"Mean: {params[1]:.2f}\n"
                f"Std Dev: {params[2]:.2f}"
            )
            plt.text(
                0.02,
                0.98,
                fit_info,
                transform=plt.gca().transAxes,
                verticalalignment="top",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
            )
        else:
            plt.text(
                0.02,
                0.98,
                "Gaussian fit failed",
                transform=plt.gca().transAxes,
                verticalalignment="top",
                bbox=dict(boxstyle="round", facecolor="red", alpha=0.8),
            )

        # Calculate and display statistics
        signal_max = np.max(y_data)
        signal_sum = np.sum(y_data)
        signal_mean = np.mean(y_data)
        stats_info = (
            f"Signal Statistics:\n"
            f"Max Value: {signal_max:.2f}\n"
            f"Sum: {signal_sum:.2f}\n"
            f"Mean: {signal_mean:.2f}\n"
            f"Data Points: {len(y_data)}"
        )
        plt.text(
            0.02,
            0.7,
            stats_info,
            transform=plt.gca().transAxes,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.8),
        )

        # Set plot properties (zoomed)
        plt.xlabel("Bin Index")
        plt.ylabel("Signal Value")
        plt.title(
            f"Gaussian Fit Debug - {module_id} - {channel_name} "
            f"{'Reference' if is_reference else ''}"
        )
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xlim(left, right)
        # y-limits: focus on signal, with a margin
        y_min = min(0, np.min(y_data[left : right + 1]))
        y_max = np.max(y_data[left : right + 1])
        plt.ylim(y_min, y_max * 1.15 + 1e-6)
        status = "SUCCESS" if fit_successful else "FAILED"
        plt.figtext(
            0.02,
            0.02,
            f"Fit Status: {status}",
            fontsize=12,
            bbox=dict(
                boxstyle="round,pad=0.3",
                facecolor="lightgreen" if fit_successful else "lightcoral",
                alpha=0.7,
            ),
        )

        plot_filename = f"{debug_folder}/{channel_name}_gaussian_fit.png"
        plt.savefig(plot_filename, dpi=150, bbox_inches="tight")
        plt.close()

        logger.debug(f"Debug plot saved: {plot_filename}")

    def fit_gaussian(
        self,
        data_series: pd.Series,
        is_reference: bool = False,
        module_id: str = "",
        channel_name: str = "",
    ) -> float:
        """Fit a Gaussian distribution to the data and return the mean.

        Args:
            data_series: Summed signal data for a specific channel pair.
            is_reference: Whether the data belongs to a reference channel.
            module_id: The module identifier for debug plots.
            channel_name: The channel name for debug plots.

        Returns:
            The mean of the Gaussian distribution fit, or 0 if the fit fails.
        """
        if data_series.sum() == 0:
            logger.warning("Sum of values is zero. Cannot fit Gaussian distribution.")
            if self.debug_mode:
                self._create_debug_plot(
                    data_series, None, module_id, channel_name, is_reference, False
                )
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
                params, _ = curve_fit(self.gaussian, x_data, y_data, p0=initial_guess)
                logger.debug(f"Initial guess: {initial_guess}")
                logger.debug(f"Params: {params}")

            # Create debug plot if enabled
            if self.debug_mode:
                self._create_debug_plot(
                    data_series, params, module_id, channel_name, is_reference, True
                )

            return float(params[1])  # Gaussian mean
        except (OptimizeWarning, RuntimeError):
            logger.warning("Gaussian fit failed or covariance could not be estimated.")
            if self.debug_mode:
                self._create_debug_plot(
                    data_series, None, module_id, channel_name, is_reference, False
                )
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
                gaussian_mean = self.fit_gaussian(
                    channel.data, is_reference, module.identifier, channel.name
                )
                if gaussian_mean == 0 and channel.noise_data is not None:
                    logger.warning("Retrying Gaussian fit with noise data.")
                    gaussian_mean = self.fit_gaussian(
                        channel.noise_data,
                        is_reference,
                        module.identifier,
                        channel.name,
                    )

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
