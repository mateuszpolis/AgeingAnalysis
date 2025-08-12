"""This service gets the required integration timestamps for range correction."""

import os
from datetime import datetime, timedelta

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

    def get_range_correction_factors(self, timestamps: pd.Series) -> pd.DataFrame:
        """Get the range correction factors for the given timestamps.

        Args:
            timestamps: The timestamps to get the range correction factors for.

        Returns:
            A DataFrame with the range correction factors.
            [start_timestamp, end_timestamp, pm, channel, range_correction_factor]
        """
        # Validate inputs
        if timestamps is None or len(timestamps) == 0:
            return pd.DataFrame(
                columns=[
                    "start_timestamp",
                    "end_timestamp",
                    "pm",
                    "channel",
                    "range_correction_factor",
                ]
            )

        # Check required files exist
        if not os.path.exists(self.configuration_loads_file_path):
            raise FileNotFoundError(
                "Configuration loads file not found: "
                f"{self.configuration_loads_file_path}"
            )
        if not os.path.exists(self.range_corrections_file_path):
            raise FileNotFoundError(
                "Range corrections file not found: "
                f"{self.range_corrections_file_path}"
            )

        # Normalize and sort timestamps (ends of integration periods)
        ts_series = pd.to_datetime(pd.Series(timestamps).astype("datetime64[ns]"))
        ts_series = ts_series.sort_values().reset_index(drop=True)

        # Build periods: (prev, current]
        end_ts = ts_series
        start_ts = ts_series.shift(1)
        # For the first timestamp, assume 24 hours back
        if not start_ts.empty:
            start_ts.iloc[0] = end_ts.iloc[0] - timedelta(days=1)

        periods_df = pd.DataFrame(
            {"start_timestamp": start_ts, "end_timestamp": end_ts}
        )

        # Load configuration loads and ensure schema
        cfg_df = pd.read_parquet(self.configuration_loads_file_path)
        if (
            "timestamp" not in cfg_df.columns
            or "configuration_name" not in cfg_df.columns
        ):
            raise ValueError(
                "Configuration loads parquet must contain "
                "'timestamp' and 'configuration_name' columns"
            )
        cfg_df = cfg_df.copy()
        cfg_df["timestamp"] = pd.to_datetime(
            cfg_df["timestamp"].astype("datetime64[ns]")
        )
        cfg_df = cfg_df.sort_values("timestamp")

        # For each period, determine the configuration active during the period.
        # Rule: use the latest load at or before the period start
        # (configuration in effect during the period).
        periods_df = pd.merge_asof(
            periods_df.sort_values("start_timestamp"),
            cfg_df[["timestamp", "configuration_name"]].sort_values("timestamp"),
            left_on="start_timestamp",
            right_on="timestamp",
            direction="backward",
        )

        # Note: Some periods may not have a configuration loaded (missing rows).
        # We do not raise here, since callers may still handle such periods
        # depending on whether any integrated value exists for them.

        # Load range corrections and ensure schema
        rc_df = pd.read_parquet(self.range_corrections_file_path)
        required_cols = {"detector_name", "configuration", "pm", "channel", "value"}
        if not required_cols.issubset(set(rc_df.columns)):
            raise ValueError(
                "Range corrections parquet must contain columns: "
                "'detector_name', 'configuration', 'pm', 'channel', 'value'"
            )

        # Filter to the detector of interest
        rc_df = rc_df[rc_df["detector_name"] == self.detector_name].copy()

        # Join per-period configuration with range corrections
        # to expand to pm/channel rows
        periods_cfg_df = periods_df[
            [
                "start_timestamp",
                "end_timestamp",
                "configuration_name",
            ]
        ].rename(columns={"configuration_name": "configuration"})

        result = periods_cfg_df.merge(
            rc_df[["configuration", "pm", "channel", "value"]],
            on="configuration",
            how="left",
        )

        # Allow missing values to propagate so the caller can decide
        # how to handle (e.g., default when integrated value is zero).

        # Finalize columns and naming
        result = (
            result.rename(columns={"value": "range_correction_factor"})[
                [
                    "start_timestamp",
                    "end_timestamp",
                    "pm",
                    "channel",
                    "range_correction_factor",
                ]
            ]
            .sort_values(["end_timestamp", "pm", "channel"])
            .reset_index(drop=True)
        )

        return result
