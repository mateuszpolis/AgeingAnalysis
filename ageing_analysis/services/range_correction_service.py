"""This service gets the required integration timestamps for range correction."""

import os
from datetime import datetime

import pandas as pd


class RangeCorrectionService:
    """This service gets the required integration timestamps for range correction."""

    def __init__(
        self,
        detector_name: str = "FT0",
        configuration_loads_file_path: str = (
            "storage/configuration_loads/configuration_loads.parquet"
        ),
        range_corrections_file_path: str = (
            "storage/range_correction/range_corrections.parquet"
        ),
    ):
        """Initialize the RangeCorrectionService.

        Args:
            detector_name: The name of the detector.
            configuration_loads_file_path: The path to the configuration loads file.
            range_corrections_file_path: The path to the range corrections file.

        Raises:
            FileNotFoundError: If the configuration loads file
                or the range corrections file does not exist.
        """
        self.detector_name = detector_name
        self.configuration_loads_file_path = configuration_loads_file_path
        self.range_corrections_file_path = range_corrections_file_path

    def get_required_integration_timestamps(
        self, start_timestamp: datetime, end_timestamp: datetime
    ) -> list[datetime]:
        """Get the required integration timestamps for the range correction.

        Analyses the configuration loads and
        returns the required integration timestamps.

        Args:
            start_timestamp: The start timestamp of the range correction.
            end_timestamp: The end timestamp of the range correction.

        Returns:
            A list of integration timestamps.
        """
        # Check if the parquet file exists
        if not os.path.exists(self.configuration_loads_file_path):
            raise FileNotFoundError(
                "Configuration loads file not found: "
                f"{self.configuration_loads_file_path}"
            )

        try:
            df = pd.read_parquet(self.configuration_loads_file_path)

            if "timestamp" not in df.columns:
                raise ValueError("Parquet file does not contain 'timestamp' column")

            # Check if column is datetime just to be safe (optional but fast)
            if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
                raise TypeError("'timestamp' column is not datetime64[ns]")

            # Filter timestamps between start and end
            mask = (df["timestamp"] >= start_timestamp) & (
                df["timestamp"] <= end_timestamp
            )
            filtered_timestamps = df.loc[mask, "timestamp"]
            return [ts.to_pydatetime() for ts in filtered_timestamps]

        except Exception as e:
            raise Exception(f"Error reading range corrections file: {e}")
