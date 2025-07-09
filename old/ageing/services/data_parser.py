import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from configs.logger_config import logger
from fit_detector.apps.ageing.entities.dataset import Dataset
from fit_detector.apps.ageing.entities.module import Module


class DataParser:
    """A class to parse and process CSV files"""

    def __init__(self, dataset: Dataset):
        """Initialize the DataParser with a dataset.

        Args:
            dataset (Dataset): The dataset to process.
        """
        self.dataset = dataset

    def _get_reference_channel_data(
        self,
        data: pd.DataFrame,
        col1: int,
        col2: int,
        prominence: float = None
    ) -> pd.Series:
        """
        Sum two channels, find the second peak, and return a slice from its full prominence bases.

        Args:
            data (pd.DataFrame): Full signal time series with at least col1 and col2.
            col1 (int): Index of the first channel column.
            col2 (int): Index of the second channel column.
            prominence (float): Minimum peak prominence for detection. If None, a default value is used.

        Returns:
            pd.Series: Summed signal cropped from the left to right base of the second peak.

        Raises:
            ValueError: If fewer than two peaks are found.
        """
        # Sum the two channels over the entire trace
        summed = data.iloc[:, [col1, col2]].sum(axis=1)

        # Set a default prominence if None is provided to ensure left_bases and right_bases are calculated
        if prominence is None:
            prominence = 0.1  # Small default value to ensure prominence calculation

        # Detect peaks with prominence (required for left_bases and right_bases)
        peaks, props = find_peaks(summed.values, prominence=prominence)
        if len(peaks) < 2:
            raise ValueError("Could not find at least two peaks in the summed signal.")

        # Use full left/right prominence bases around the second peak
        left_base = props['left_bases'][1]
        right_base = props['right_bases'][1]

        # Return the slice from left_base to right_base
        return pd.Series(summed.iloc[left_base:right_base].values, index=summed.index[left_base:right_base])


    def _parse_and_process_file(self, module: Module):
        """
        Parse and process a single CSV file for creating Channels by summing pairs of columns.

        Args:
            module (Module): The Module object containing the file path and reference info.
        """
        # Load the CSV file
        data = pd.read_csv(module.path, delimiter=":")

        # Check for valid column count (odd number of columns)
        if data.shape[1] % 2 != 1:
            raise ValueError(
                f"File {module.path} has an invalid number of "
                "columns. Expected an odd number of columns "
                "(bin and two columns for each channel)"
            )

        # Drop the first column (bin number)
        data = data.iloc[:, 1:]

        # Split data into signal data (from row 258 onwards) and noise data (first 257 rows)
        signal_data = data.iloc[257:]
        noise_data = data.iloc[:257]

        # For each column pair, check if it should be treated as a reference channel
        for i in range(0, data.shape[1] - 1, 2):
            # Adjust to 1-based indexing by dividing i by 2 and adding 1
            channel_num = (i // 2) + 1

            if module.is_reference and channel_num in module.ref_channels:
                # Use the helper function to process the reference range for this channel
                paired_sum = self._get_reference_channel_data(signal_data, i, i + 1)
            else:
                # Sum normally for non-reference channels or non-reference modules
                paired_sum = signal_data.iloc[:, i] + signal_data.iloc[:, i + 1]

            # Sum the noise data for the current channel
            noise_paired_sum = noise_data.iloc[:, i] + noise_data.iloc[:, i + 1]

            x_data = np.arange(len(paired_sum))
            paired_sum.index = x_data

            # Add the new Channel to the Module, passing signal and noise data
            module.add_channel(channel_num, paired_sum, noise_paired_sum)

    def process_all_files(self):
        """Process all files in the config and return the processed data.

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
