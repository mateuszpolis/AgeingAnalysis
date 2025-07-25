"""This service is used to get the integrated CFD rate for a given date range."""

import datetime
import logging
import os
from typing import Dict, Generator, List, Tuple

import numpy as np
import pandas as pd

from ageing_analysis.services.darma_api_service import DarmaApiSchema, DarmaApiService

logger = logging.getLogger(__name__)


class CFDRateIntegrationService:
    """This service is used to get the integrated CFD rate for a given date range."""

    def __init__(self):
        """Initialize the CFDRateIntegrationService.

        Args:
            dataset: The dataset to use.
        """
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
            filename = "integrated_cfd_rate.parquet"

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
                logger.warning(f"Could not read existing file {filename}: {e}")
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
            Dictionary mapping element names to sets of available dates.
        """
        if filename is None:
            filename = "integrated_cfd_rate.parquet"

        if not os.path.exists(filename):
            return {}

        try:
            df = pd.read_parquet(filename)
            df["date"] = pd.to_datetime(df["date"]).dt.date

            coverage = {}
            for element_name in df["element_name"].unique():
                element_data = df[df["element_name"] == element_name]
                coverage[element_name] = set(element_data["date"].unique())

            return coverage
        except Exception as e:
            logger.error(f"Error reading coverage from {filename}: {e}")
            return {}

    def _get_missing_date_ranges(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
        element_names: list | None = None,
        filename: str | None = None,
    ) -> Dict[Tuple[datetime.date, datetime.date], List[str]]:
        """Determine what date ranges are missing for each element.

        Args:
            start_date: Start date for the requested range
            end_date: End date for the requested range
            element_names: List of element names to check. If None, checks all elements
            filename: Optional filename for the parquet file.
                If None, uses default based on dataset.

        Returns:
            Dictionary mapping (start_date, end_date) tuples to list of element names.
        """
        if filename is None:
            filename = "integrated_cfd_rate.parquet"

        if element_names is None:
            element_names = list(self._get_datapoints())

        coverage = self._get_available_data_coverage(
            filename
        )  # must return set of dates per element
        missing_ranges = {}

        # Required record timestamps: start_date+1 to end_date
        required_records = [
            start_date + datetime.timedelta(days=i)
            for i in range(1, (end_date - start_date).days + 1)
        ]

        for element_name in element_names:
            available_records = coverage.get(element_name)

            if not available_records:
                # No data exists for this element — entire range is missing
                missing_ranges[element_name] = [(start_date, end_date)]
                continue

            missing_records = sorted(
                d for d in required_records if d not in available_records
            )

            # Group missing_records into contiguous ranges
            ranges = []
            if missing_records:
                range_start = missing_records[0] - datetime.timedelta(days=1)
                range_end = missing_records[0]
                for d in missing_records[1:]:
                    if d == range_end + datetime.timedelta(days=1):
                        range_end = d
                    else:
                        # Add range for this contiguous block of missing records
                        ranges.append((range_start, range_end))
                        range_start = d - datetime.timedelta(days=1)
                        range_end = d

                # Append final range
                ranges.append((range_start, range_end))

            missing_ranges[element_name] = ranges

        # Convert the missing ranges to a dict where range is
        #  the key and the value is a list of element names
        missing_ranges_dict: Dict[Tuple[datetime.date, datetime.date], List[str]] = {}
        for element_name, ranges in missing_ranges.items():
            for r in ranges:
                if r not in missing_ranges_dict:
                    missing_ranges_dict[r] = []
                missing_ranges_dict[r].append(element_name)

        return missing_ranges_dict

    def _query_integrated_cfd_rate(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
        element_names: list | None = None,
        filename: str | None = None,
    ) -> pd.DataFrame:
        """Query integrated CFD rate from the parquet file for a specific date range.

        The date range represents integration periods:
        - start_date to end_date means integrations from
            start_date 12pm to end_date 12pm
        - Results are returned with the end_date of each integration period

        Args:
            start_date: Start date for the integration period
            end_date: End date for the integration period
            element_names: List of element names to query.
                If None, queries all elements from _get_datapoints()
            filename: Optional filename for the parquet file. If None, uses default
                based on dataset.

        Returns:
            DataFrame with columns ["date", "element_name", "value"] for the
                requested range.
        """
        if filename is None:
            filename = "integrated_cfd_rate.parquet"

        if not os.path.exists(filename):
            return pd.DataFrame(columns=["date", "element_name", "value"])

        try:
            df = pd.read_parquet(filename)
            df["date"] = pd.to_datetime(df["date"]).dt.date

            # For a range start_date to end_date, we want integrations that end on dates
            # from start_date+1 to end_date+1 (since integration periods are
            # start_date 12pm to end_date 12pm)
            query_start = start_date + datetime.timedelta(days=1)
            query_end = end_date + datetime.timedelta(days=1)

            # Filter by date range
            mask = (df["date"] >= query_start) & (df["date"] <= query_end)
            df_filtered = df[mask]

            # Filter by element names if specified
            if element_names is not None:
                df_filtered = df_filtered[
                    df_filtered["element_name"].isin(element_names)
                ]

            return df_filtered.reset_index(drop=True)

        except Exception as e:
            logger.error(f"Error querying data from {filename}: {e}")
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
        # Data from 12pm on day N to 12pm on day N+1 gets assigned to day N+1
        df = df.copy()

        # Shift timestamps by 12 hours so that 12pm becomes 00:00
        # This makes it easier to group into 24-hour periods
        shifted_timestamps = df["timestamp"] - pd.Timedelta(hours=12)

        # Group by day (floor to day boundary)
        df["integration_day"] = (
            shifted_timestamps.dt.floor("D")
            + pd.Timedelta(hours=12)
            + pd.Timedelta(days=1)
        )

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

    def get_integrated_cfd_rate(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
        chunk_size_days: int = 1,
        filename: str | None = None,
        multiply_by_mu: bool = False,
        include_pmc9: bool = True,
    ) -> Dict[str, Dict[str, float]]:
        """Get integrated CFD rate data for the specified date range.

        Args:
            start_date: Start date for the requested range
            end_date: End date for the requested range
            chunk_size_days: Number of days to process in each chunk (default: 1)
            filename: Optional filename for the parquet file.
                If None, uses default based on dataset.
            multiply_by_mu: If True, multiply the integrated CFD rate by the mu
                value.

        Returns:
            Dictionary with PM as keys and dictionaries with Channels as keys
            and values as integrated CFD rates for the requested range.
        """
        if filename is None:
            filename = "integrated_cfd_rate.parquet"

        # Get all datapoints that need to be processed
        all_datapoints = list(self._get_datapoints())
        logger.info(
            f"Processing {len(all_datapoints)} datapoints for date range "
            f"{start_date} to {end_date}"
        )

        # Check what data is already available
        missing_ranges = self._get_missing_date_ranges(
            start_date, end_date, all_datapoints, filename
        )

        if missing_ranges:
            # Process missing ranges in chunks
            total_integrated_data: pd.DataFrame = pd.DataFrame(
                columns=["timestamp", "value", "element_name"]
            )

            # Process missing ranges in chunks
            for range_start, range_end in missing_ranges.keys():
                logger.info(f"Processing missing range: {range_start} to {range_end}")
                chunk_integrated_data = self._process_date_range_in_chunks(
                    range_start,
                    range_end,
                    missing_ranges[(range_start, range_end)],
                    chunk_size_days,
                )
                if not chunk_integrated_data.empty:
                    total_integrated_data = pd.concat(
                        [total_integrated_data, chunk_integrated_data],
                        ignore_index=True,
                    )

            # Combine all integrated data
            if not total_integrated_data.empty:
                # Save the integrated data to the parquet file
                logger.info(
                    f"Saving {len(total_integrated_data)} integrated records to "
                    f"{filename}"
                )
                self._save_integrated_cfd_rate(total_integrated_data, filename)
            else:
                logger.info("No new data was downloaded and integrated")

        # Return the complete dataset for the requested range
        return self._sum_integrated_cfd_rate(
            self._query_integrated_cfd_rate(start_date, end_date, filename=filename),
            multiply_by_mu,
            include_pmc9,
        )

    def _get_pm_and_channel_from_element_name(
        self, element_name: str
    ) -> Tuple[str, str]:
        """Get the PM and Channel from the element name.

        Args:
            element_name: The element name

        Returns:
            Tuple with PM and Channel
        """
        pm = element_name.split("/")[1].split(".")[0]
        channel = element_name.split("/")[2].split(".")[0]
        return pm, channel

    def _sum_integrated_cfd_rate(
        self,
        integrated_data: pd.DataFrame,
        multiply_by_mu: bool = False,
        include_pmc9: bool = True,
    ) -> Dict[str, Dict[str, float]]:
        """Sum the integrated CFD rate by PM and Channel.

        Args:
            integrated_data: DataFrame with columns
            ["timestamp", "value", "element_name"]
            multiply_by_mu: If True, multiply the integrated CFD rate by the mu
                value.
            include_pmc9: If True, include PMC9 channels 9, 10, 11, 12 in the result.

        Returns:
            Dictionary with PM as keys and dictionaries with Channels as keys
            and values as integrated CFD rates for the requested range.
        """
        if integrated_data.empty:
            return {}

        # Map element_name to PM and Channel
        pm_channel_df = integrated_data["element_name"].apply(
            self._get_pm_and_channel_from_element_name
        )
        pm_channel_df = pd.DataFrame(pm_channel_df.tolist(), columns=["pm", "channel"])

        # Concatenate with original data
        df = pd.concat([integrated_data, pm_channel_df], axis=1)

        mu = 43 * 10**-15

        # Apply mu multiplication to individual values before grouping if requested
        if multiply_by_mu:
            df["value"] = df["value"] * mu

        # Group by PM and Channel and sum values
        grouped = df.groupby(["pm", "channel"])["value"].sum().reset_index()

        # Convert to nested dictionary {pm: {channel: value}}
        result: Dict[str, Dict[str, float]] = {}
        for _, row in grouped.iterrows():
            pm, channel, value = row["pm"], row["channel"], row["value"]
            result.setdefault(pm, {})[channel] = value

        # For PMC9 channels 9, 10, 11, 12, set the value to 0
        if include_pmc9:
            for channel in ["Ch09", "Ch10", "Ch11", "Ch12"]:
                result["PMC9"][channel] = 0.0

        return result

    def _process_date_range_in_chunks(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
        element_names: list[str],
        chunk_size_days: int,
    ) -> pd.DataFrame:
        """Process a date range in daily chunks, downloading and integrating data.

        Args:
            start_date: Start date of the *requested* range
            end_date: End date of the *requested* range
            element_names: List of element names to process
            chunk_size_days: Number of record days to process in each chunk

        Returns:
            DataFrame with integrated data for the entire range.
        """
        logger.info(f"Processing date range in chunks: {start_date} to {end_date}")
        logger.info(f"Chunk size: {chunk_size_days} days")

        all_integrated_data = []
        # First record we need is for start_date+1
        current_record_date = start_date

        while current_record_date <= end_date:
            # Determine the end of this chunk of record dates
            chunk_record_end_date = min(
                current_record_date + datetime.timedelta(days=chunk_size_days), end_date
            )

            logger.info(
                f"Processing chunk of records: {current_record_date} to "
                f"{chunk_record_end_date}"
            )

            # Download and integrate for this chunk
            chunk_data = self._download_and_integrate_chunk(
                current_record_date, chunk_record_end_date, element_names
            )

            if not chunk_data.empty:
                all_integrated_data.append(chunk_data)

            # Move to next chunk of record dates
            current_record_date = chunk_record_end_date + datetime.timedelta(days=1)

        if all_integrated_data:
            return pd.concat(all_integrated_data, ignore_index=True)
        else:
            return pd.DataFrame(columns=["timestamp", "value", "element_name"])

    def _download_and_integrate_chunk(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
        element_names: list[str],
    ) -> pd.DataFrame:
        """Download and integrate data for a specific chunk.

        Args:
            start_date: Start date for the chunk
            end_date: End date for the chunk
            element_names: List of element names to process

        Returns:
            DataFrame with integrated data for the chunk.
        """
        # Convert dates to datetime for DARMA API
        start_datetime = datetime.datetime.combine(start_date, datetime.time(12, 0, 0))
        end_datetime = datetime.datetime.combine(
            end_date, datetime.time(11, 59, 59, 999999)
        )

        logger.info(
            f"Downloading data from DARMA API for {len(element_names)} elements"
        )

        try:
            # Download data from DARMA API
            raw_data = self.darma_api_service.get_data(
                time_from=start_datetime,
                time_to=end_datetime,
                schema=DarmaApiSchema.FT0ARCH,
                elements=element_names,
            )

            if raw_data.empty:
                logger.warning(
                    f"No data received from DARMA API for chunk {start_date} to "
                    f"{end_date}"
                )
            else:
                logger.info(f"Downloaded {len(raw_data)} raw data points")

            if not raw_data.empty:
                # Integrate the raw data
                integrated_data = self._integrate_cfd_rate(raw_data)
            else:
                integrated_data = pd.DataFrame(
                    columns=["timestamp", "value", "element_name"]
                )

            logger.info(f"Integrated into {len(integrated_data)} daily records")

            # Ensure all requested elements have records, even if no data was returned
            integrated_data = self._ensure_all_elements_have_records(
                integrated_data, element_names, end_date
            )

            return integrated_data

        except Exception as e:
            logger.error(
                f"Error downloading/integrating chunk {start_date} to {end_date}: {e}"
            )
            return pd.DataFrame(columns=["timestamp", "value", "element_name"])

    def get_empty_pm_channel_dict(
        self, include_pmc9: bool = False
    ) -> Dict[str, Dict[str, float]]:
        """Get an empty dictionary with PM and Channel as keys.

        Returns:
            Dictionary with PM and Channel as keys.
        """
        datapoints = list(self._get_datapoints())
        pms_channels = [
            self._get_pm_and_channel_from_element_name(dp) for dp in datapoints
        ]

        # Create the nested dictionary structure
        result: Dict[str, Dict[str, float]] = {}

        for pm, channel in pms_channels:
            if pm not in result:
                result[pm] = {}
            result[pm][channel] = 0.0

        if include_pmc9:
            for channel in ["Ch09", "Ch10", "Ch11", "Ch12"]:
                result["PMC9"][channel] = 0.0

        return result

    def _ensure_all_elements_have_records(
        self,
        integrated_data: pd.DataFrame,
        requested_elements: list[str],
        end_date: datetime.date,
    ) -> pd.DataFrame:
        """Ensure all requested elements have a record at end_date 12:00.

        If an element has no data, create a record with 0 value for end_date 12:00.

        Args:
            integrated_data: DataFrame with integrated data
            requested_elements: List of elements that were requested
            end_date: End date of the chunk

        Returns:
            DataFrame with all requested elements having records at end_date 12:00.
        """
        target_timestamp = pd.Timestamp(end_date) + pd.Timedelta(hours=12)

        # Find elements already present in integrated_data
        if integrated_data.empty:
            elements_with_data = set()
        else:
            elements_with_data = set(integrated_data["element_name"].unique())

        missing_elements = set(requested_elements) - elements_with_data

        if not missing_elements:
            return integrated_data

        missing_records = [
            {
                "timestamp": target_timestamp,
                "value": 0.0,
                "element_name": element_name,
            }
            for element_name in missing_elements
        ]

        missing_df = pd.DataFrame(missing_records)

        combined_data = pd.concat([integrated_data, missing_df], ignore_index=True)

        combined_data = combined_data.sort_values(
            ["timestamp", "element_name"]
        ).reset_index(drop=True)

        logger.info(
            f"Added {len(missing_records)} zero-value records for "
            f"{len(missing_elements)} missing elements"
        )

        return combined_data
