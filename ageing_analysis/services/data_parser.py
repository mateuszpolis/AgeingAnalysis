"""Data parsing service for FIT detector ageing analysis."""

import logging
import os
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from ageing_analysis.entities.dataset import Dataset
from ageing_analysis.entities.module import Module

logger = logging.getLogger(__name__)


class DataParser:
    """A class to parse and process CSV files for ageing analysis."""

    def __init__(
        self,
        dataset: Dataset,
        debug_mode: bool = False,
        prominence_percent: Optional[float] = None,
        peak_merge_threshold: int = 5,
    ):
        """Initialize the DataParser with a dataset.

        Args:
            dataset: The dataset to process.
            debug_mode: Whether to plot debug plots.
            prominence_percent: The prominence percentage to use for peak detection.
            peak_merge_threshold: The threshold for merging peaks when the bases
                                are this close.
        """
        self.dataset = dataset
        self.debug_mode = debug_mode
        self.prominence_percent = prominence_percent
        self.peak_merge_threshold = peak_merge_threshold

    def _get_non_reference_channel_data(
        self,
        data: pd.DataFrame,
        col1: int,
        col2: int,
    ) -> pd.Series:
        """Get the data for a non-reference channel."""
        sig_series = data.iloc[:, [col1, col2]].sum(axis=1)
        # Replace first 25 bins with zeros to handle noise in the -25 to 25 bin range
        sig_series.iloc[:25] = 0
        return sig_series

    def _get_reference_channel_data(
        self,
        data: pd.DataFrame,
        col1: int,
        col2: int,
    ) -> pd.Series:
        """Sum two channels, detect the *second-largest* peak.

        Return the slice from its left to right full-prominence bases.
        """
        # Sum the two columns
        summed = data.iloc[:, [col1, col2]].sum(axis=1)

        # Cut the first 50 bins to skip the highest peak
        summed = summed.iloc[50:]

        # Check if the signal peak is at the edge of the data
        if summed.max() == summed.iloc[0] or summed.max() == summed.iloc[-1]:
            raise ValueError(
                "Signal peak is at the edge of the data. "
                "Please check the data for edge plateaus."
            )

        # Calculate the prominence
        if self.prominence_percent is None:
            self.prominence_percent = 15
        prominence = self.prominence_percent * summed.max() / 100

        # Detect *all* peaks above that threshold
        peaks, props = find_peaks(summed.values, prominence=prominence)

        # Log all the peaks and their properties
        logger.debug(f"Peaks: {peaks}")
        logger.debug(f"Props: {props}")

        # Merge peaks when the bases are less than 5 bins apart
        peaks_to_remove = []
        for i in range(len(peaks)):
            if i > 0:
                if (
                    abs(props["left_bases"][i] - props["left_bases"][i - 1])
                    < self.peak_merge_threshold
                    and abs(props["right_bases"][i] - props["right_bases"][i - 1])
                    < self.peak_merge_threshold
                ):
                    # Average the current peak with the previous peak
                    peaks[i] = (peaks[i] + peaks[i - 1]) / 2
                    props["left_bases"][i] = (
                        props["left_bases"][i] + props["left_bases"][i - 1]
                    ) / 2
                    props["right_bases"][i] = (
                        props["right_bases"][i] + props["right_bases"][i - 1]
                    ) / 2
                    # Mark the previous peak for removal
                    peaks_to_remove.append(i - 1)

        # Remove the merged peaks (in reverse order to maintain indices)
        for idx in reversed(peaks_to_remove):
            peaks = np.delete(peaks, idx)
            for key in props:
                props[key] = np.delete(props[key], idx)

        # Generate debugging plots for all scenarios
        if self.debug_mode:
            self._create_peak_detection_debug_plot(summed, peaks, props, col1, col2)

        # Now handle the different cases with appropriate errors
        if len(peaks) < 2:
            raise ValueError("Could not find at least two peaks in the summed signal.")
        elif len(peaks) > 2:
            raise ValueError(
                "Found more than two peaks in the summed signal. "
                "Please check the data for multiple peaks."
            )

        # Take the first peak in order of bins (since we cut the first 50 bins)
        first_peak_idx = 0  # First peak in the peaks array

        lb = props["left_bases"][first_peak_idx]
        rb = props["right_bases"][first_peak_idx]
        logger.debug(f"First peak spans bins {lb}→{rb}")

        # Get the selected region
        selected_data = summed.iloc[lb:rb].values

        # Create a full-length series with zeros, maintaining original peak positions
        # The original data had length len(data), so we create a series of that length
        full_data = np.zeros(len(data))

        # Place the selected region at the correct position
        # lb and rb are indices in the cut data (after removing first 50 bins)
        # So in the original data, they correspond to positions lb+50 and rb+50
        original_lb = lb + 50
        original_rb = rb + 50

        # Place the selected data at the correct position in the full series
        full_data[original_lb:original_rb] = selected_data

        # Create index that matches the original data positions
        original_index = np.arange(len(full_data))

        # Return the series with the peak at its original position
        return pd.Series(
            full_data,
            index=original_index,
            name=f"ref_chan_{col1}_{col2}",
        )

    def _create_peak_detection_debug_plot(
        self,
        summed: pd.Series,
        peaks: np.ndarray,
        props: dict,
        col1: int,
        col2: int,
    ):
        """Create debug plot for peak detection analysis.

        Args:
            summed: The summed signal data
            peaks: Array of detected peak indices
            props: Peak properties from find_peaks
            col1: First column index
            col2: Second column index
        """
        debug_folder = f"debug_plots/data_parser/{self.dataset.date}"
        if not os.path.exists(debug_folder):
            os.makedirs(debug_folder)

        plt.figure(figsize=(12, 8))

        # Change the index start from 50
        summed.index = list(range(50, len(summed) + 50))

        # Plot the summed signal
        plt.plot(summed.index, summed.values, "b-", linewidth=2, label="Summed Signal")

        # Determine the scenario and plot accordingly
        num_peaks = len(peaks)
        lb, rb = None, None

        if num_peaks == 0:
            # No peaks found
            plt.title(
                f"Peak Detection Debug - Channels {col1} & {col2} [NO PEAKS FOUND]"
            )
            status_text = "No peaks detected"

        elif num_peaks == 1:
            # Only one peak found
            peak_idx = peaks[0]
            prominence = props["prominences"][0]
            plt.plot(
                summed.index[peak_idx],
                summed.values[peak_idx],
                "orange",
                marker="o",
                markersize=10,
                label="Only Peak Found",
            )
            plt.annotate(
                f"Single Peak\n(prom: {prominence:.1f})",
                xy=(summed.index[peak_idx], summed.values[peak_idx]),
                xytext=(10, 10),
                textcoords="offset points",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="orange", alpha=0.7),
            )
            plt.title(
                f"Peak Detection Debug - Channels {col1} & {col2} "
                "[INSUFFICIENT PEAKS]"
            )
            status_text = "Only 1 peak found (need 2)"

        elif num_peaks == 2:
            # Exactly 2 peaks - normal case
            for i, peak_idx in enumerate(peaks):
                prominence = props["prominences"][i]
                color = "ro" if i > 0 else "go"  # Green for first, red for others
                markersize = 12 if i == 0 else 8
                plt.plot(
                    summed.index[peak_idx],
                    summed.values[peak_idx],
                    color,
                    markersize=markersize,
                )

                if i == 0:
                    plt.annotate(
                        f"SELECTED Peak\n(prom: {prominence:.1f})",
                        xy=(summed.index[peak_idx], summed.values[peak_idx]),
                        xytext=(10, 10),
                        textcoords="offset points",
                        bbox=dict(
                            boxstyle="round,pad=0.3",
                            facecolor="lightgreen",
                            alpha=0.7,
                        ),
                    )
                else:
                    plt.annotate(
                        f"Peak {i+1}\n(prom: {prominence:.1f})",
                        xy=(summed.index[peak_idx], summed.values[peak_idx]),
                        xytext=(10, 10),
                        textcoords="offset points",
                        bbox=dict(
                            boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7
                        ),
                    )

            # Set up for region selection
            lb = props["left_bases"][0]
            rb = props["right_bases"][0]

            # Draw vertical lines for left and right bases
            plt.axvline(
                x=summed.index[lb],
                color="red",
                linestyle="--",
                linewidth=2,
                label=f"Left Base (idx: {lb})",
            )
            plt.axvline(
                x=summed.index[rb],
                color="red",
                linestyle="--",
                linewidth=2,
                label=f"Right Base (idx: {rb})",
            )

            # Fill the selected region
            selected_region = summed.iloc[lb:rb]
            plt.fill_between(
                selected_region.index,
                selected_region.values,
                alpha=0.3,
                color="green",
                label="Selected Region",
            )

            plt.title(f"Peak Detection Debug - Channels {col1} & {col2} [SUCCESS]")
            status_text = f"2 peaks found, first peak selected (spans bins {lb}→{rb})"

        else:
            # More than 2 peaks
            for i, peak_idx in enumerate(peaks):
                prominence = props["prominences"][i]
                plt.plot(
                    summed.index[peak_idx],
                    summed.values[peak_idx],
                    "purple",
                    marker="x",
                    markersize=8,
                )
                plt.annotate(
                    f"Peak {i+1}\n(prom: {prominence:.1f})",
                    xy=(summed.index[peak_idx], summed.values[peak_idx]),
                    xytext=(10, 10),
                    textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="purple", alpha=0.3),
                )

            plt.title(
                f"Peak Detection Debug - Channels {col1} & {col2} [TOO MANY PEAKS]"
            )
            status_text = f"{num_peaks} peaks found (expected exactly 2)"

        # Add status text to plot
        plt.figtext(
            0.02,
            0.02,
            status_text,
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7),
        )

        plt.xlabel("Index")
        plt.ylabel("Signal Value")
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Save plot with unique filename
        existing_files = len(
            [f for f in os.listdir(debug_folder) if f.endswith(".png")]
        )
        plot_filename = (
            f"{debug_folder}/peak_debug_ch{col1}_{col2}_{existing_files}.png"
        )
        plt.savefig(plot_filename, dpi=150, bbox_inches="tight")
        plt.close()

        logger.debug(f"Debug plot saved: {plot_filename}")

    def _parse_and_process_file(self, module: Module):
        """Parse & process a single CSV file for creating Channels."""
        # Load into a DataFrame
        df = pd.read_csv(module.path, delimiter=":")

        # Sanity check
        if df.shape[1] % 2 != 1:
            raise ValueError(
                f"File {module.path} has an invalid number of "
                "columns. Expected odd (1 bin + 2 per channel)"
            )

        # Drop the bin‐column and split
        df = df.iloc[:, 1:]
        sig_df = df.iloc[257:]  # from bin 0
        # We leave the noise series longer, as in case the channel is aged
        # there might not be any more signal after bin 50
        noise_df = df.iloc[:307]  # up to bin 50

        # Process each channel‐pair
        for i in range(0, df.shape[1] - 1, 2):
            chan_idx = (i // 2) + 1
            if module.is_reference and chan_idx in module.ref_channels:
                sig_series = self._get_reference_channel_data(sig_df, i, i + 1)
            else:
                sig_series = self._get_non_reference_channel_data(sig_df, i, i + 1)

            # Create noise series with proper bin positions
            # First 256 bins are negative (-256 to -1), then bins 0 to 50
            noise_series = noise_df.iloc[:, i] + noise_df.iloc[:, i + 1]
            # Set proper indices based on actual data length
            # If we have 307 rows: -256 to 50 (307 elements)
            # If we have fewer rows, adjust accordingly
            actual_noise_length = len(noise_series)
            if actual_noise_length >= 307:
                # Full range: -256 to 50
                noise_series.index = list(range(-256, 51))
            else:
                # Partial range: start from -(actual_noise_length-51) to 50
                # This ensures we always have bins 0-50 at the end
                start_bin = -(actual_noise_length - 51)
                noise_series.index = list(range(start_bin, 51))

            total_signal_series = df.iloc[:, i] + df.iloc[:, i + 1]

            # re-index so x = 0…N−1
            sig_series.index = np.arange(len(sig_series))

            module.add_channel(chan_idx, sig_series, noise_series, total_signal_series)

    def process_all_files(self):
        """Process all files in the dataset and return the processed data.

        Raises:
            Exception: If any file fails to process
        """
        logger.debug("Processing data...")

        for module in self.dataset.modules:
            try:
                # Process each file
                logger.debug(f"Processing file for {module.identifier}: {module.path}")
                self._parse_and_process_file(module)
                logger.debug(f"Processed data for {module.identifier} successfully.")
            except Exception as e:
                raise Exception(f"Failed to process file for {module.identifier}: {e}")

        logger.info("All files processed successfully.")
