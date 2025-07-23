"""This service is used to get the integrated CFD rate for a given date range."""

import datetime
import os
from typing import Generator

import numpy as np
import pandas as pd

from ageing_analysis.services.darma_api_service import DarmaApiService


class CFDRateIntegrationService:
    """This service is used to get the integrated CFD rate for a given date range."""

    def __init__(self, dataset):
        """Initialize the CFDRateIntegrationService.

        Args:
            dataset: The dataset to use.
        """
        self.dataset = dataset
        self.darma_api_service = DarmaApiService()

    def _save_integrated_cfd_rate(
        self, integrated_cfd_rate: pd.DataFrame, filename: str | None = None
    ) -> None:
        """Save the integrated CFD rate to a parquet file with incremental updates.

        This function handles incremental updates to the parquet file.

        Args:
            integrated_cfd_rate: DataFrame with columns ["timestamp", "value",
                "element_name"]
            filename: Optional filename for the parquet file. If None, uses default
                based on dataset.
        """
        if filename is None:
            filename = f"integrated_cfd_rate_{self.dataset}.parquet"

        # Convert timestamp to date for easier querying
        df_new = integrated_cfd_rate.copy()
        df_new["date"] = pd.to_datetime(df_new["timestamp"]).dt.date
        df_new = df_new[["date", "element_name", "value"]]

        # Load existing data if file exists
        if os.path.exists(filename):
            try:
                df_existing = pd.read_parquet(filename)
                # Ensure date column is datetime.date type
                df_existing["date"] = pd.to_datetime(df_existing["date"]).dt.date

                # Combine existing and new data
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            except Exception as e:
                print(f"Warning: Could not read existing file {filename}: {e}")
                df_combined = df_new
        else:
            df_combined = df_new

        # Remove duplicates, keeping the latest value for each date-element combination
        df_combined.drop_duplicates(
            subset=["date", "element_name"], keep="last", inplace=True
        )

        # Sort by date and element_name for better querying performance
        df_combined.sort_values(["date", "element_name"], inplace=True)
        df_combined.reset_index(drop=True, inplace=True)

        # Save to parquet file
        df_combined.to_parquet(filename, index=False)

    def _get_available_data_coverage(self, filename: str | None = None) -> dict:
        """Get information about available data coverage in the parquet file.

        Args:
            filename: Optional filename for the parquet file. If None, uses default
                based on dataset.

        Returns:
            Dictionary with coverage information for each element.
        """
        if filename is None:
            filename = f"integrated_cfd_rate_{self.dataset}.parquet"

        if not os.path.exists(filename):
            return {}

        try:
            df = pd.read_parquet(filename)
            df["date"] = pd.to_datetime(df["date"]).dt.date

            coverage = {}
            for element_name in df["element_name"].unique():
                element_data = df[df["element_name"] == element_name]
                coverage[element_name] = {
                    "min_date": element_data["date"].min(),
                    "max_date": element_data["date"].max(),
                    "total_days": len(element_data),
                }

            return coverage
        except Exception as e:
            print(f"Error reading coverage from {filename}: {e}")
            return {}

    def _get_missing_date_ranges(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
        element_names: list | None = None,
        filename: str | None = None,
    ) -> dict:
        """Determine what date ranges need to be downloaded for each element.

        Args:
            start_date: Start date for the requested range
            end_date: End date for the requested range
            element_names: List of element names to check. If None, checks all elements
                from _get_datapoints()
            filename: Optional filename for the parquet file. If None, uses default
                based on dataset.

        Returns:
            Dictionary mapping element names to list of (start_date, end_date)
                tuples that need downloading.
        """
        if filename is None:
            filename = f"integrated_cfd_rate_{self.dataset}.parquet"

        if element_names is None:
            element_names = list(self._get_datapoints())

        coverage = self._get_available_data_coverage(filename)
        missing_ranges = {}

        for element_name in element_names:
            if element_name not in coverage:
                # No data exists for this element, need to download full range
                missing_ranges[element_name] = [(start_date, end_date)]
                continue

            element_coverage = coverage[element_name]
            ranges_to_download = []

            # Check if we need data before the available range
            if start_date < element_coverage["min_date"]:
                ranges_to_download.append(
                    (
                        start_date,
                        element_coverage["min_date"] - datetime.timedelta(days=1),
                    )
                )

            # Check if we need data after the available range
            if end_date > element_coverage["max_date"]:
                ranges_to_download.append(
                    (
                        element_coverage["max_date"] + datetime.timedelta(days=1),
                        end_date,
                    )
                )

            if ranges_to_download:
                missing_ranges[element_name] = ranges_to_download

        return missing_ranges

    def _query_integrated_cfd_rate(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
        element_names: list | None = None,
        filename: str | None = None,
    ) -> pd.DataFrame:
        """Query integrated CFD rate from the parquet file for a specific date range.

        Args:
            start_date: Start date for the query
            end_date: End date for the query
            element_names: List of element names to query. If None, queries all elements
                from _get_datapoints()
            filename: Optional filename for the parquet file. If None, uses default
                based on dataset.

        Returns:
            DataFrame with columns ["date", "element_name", "value"] for the
                requested range.
        """
        if filename is None:
            filename = f"integrated_cfd_rate_{self.dataset}.parquet"

        if not os.path.exists(filename):
            return pd.DataFrame(columns=["date", "element_name", "value"])

        try:
            df = pd.read_parquet(filename)
            df["date"] = pd.to_datetime(df["date"]).dt.date

            # Filter by date range
            mask = (df["date"] >= start_date) & (df["date"] <= end_date)
            df_filtered = df[mask]

            # Filter by element names if specified
            if element_names is not None:
                df_filtered = df_filtered[
                    df_filtered["element_name"].isin(element_names)
                ]

            return df_filtered.reset_index(drop=True)

        except Exception as e:
            print(f"Error querying data from {filename}: {e}")
            return pd.DataFrame(columns=["date", "element_name", "value"])

    def _get_datapoints(self) -> Generator[str, None, None]:
        """Get the datapoints for the CFD rate.

        Returns:
            A generator of datapoints.
        """
        for pm_type in ["A", "C"]:
            for pm in range(0, 10):
                if pm_type == "A" and pm == 9:
                    break
                for ch in range(1, 13):
                    if pm_type == "C" and pm == 9 and ch == 9:
                        break
                    yield f"ft0_dcs:FEE/PM{pm_type}{pm}/Ch{ch:02d}.actual.CFD_RATE"

    def _integrate_cfd_rate_trapezoidal(self, df: pd.DataFrame) -> float:
        """Integrate the CFD rate using the trapezoidal rule.

        Args:
            df: The DataFrame with 'timestamp' and 'value' columns.

        Returns:
            The integrated value.
        """
        if len(df) < 2:
            return 0.0

        # Sort by timestamp
        df_sorted = df.sort_values("timestamp")

        # Convert timestamps to seconds since epoch
        timestamps = pd.to_datetime(df_sorted["timestamp"]).astype("int64") / 1e9
        values = df_sorted["value"].to_numpy()

        # Differences between adjacent points
        dt = np.diff(timestamps)
        avg_values = (values[1:] + values[:-1]) / 2

        # Vectorized trapezoidal integration
        integrated_value: float = np.sum(avg_values * dt)

        return integrated_value

    def _integrate_cfd_rate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Integrate the CFD rate by element and day.

        Args:
            df: DataFrame with columns ["timestamp", "value", "element_name"]

        Returns:
            DataFrame with integrated values per element per 12pm–12pm day.
        """
        if df.empty:
            return pd.DataFrame(columns=["timestamp", "value", "element_name"])

        # Compute integration day anchored at 12:00
        df = df.copy()
        df["integration_day"] = (
            df["timestamp"]
            - pd.to_timedelta((df["timestamp"].dt.hour < 12).astype(int), unit="D")
        ).dt.floor("D") + pd.Timedelta(hours=12)

        # Group and integrate
        def integrate_group(group):
            integrated_value = self._integrate_cfd_rate_trapezoidal(group)
            return pd.Series(
                {
                    "timestamp": group["integration_day"].iloc[0],
                    "value": integrated_value,
                    "element_name": group["element_name"].iloc[0],
                }
            )

        result = (
            df.groupby(["element_name", "integration_day"])
            .apply(integrate_group)
            .reset_index(drop=True)
        )

        return result
