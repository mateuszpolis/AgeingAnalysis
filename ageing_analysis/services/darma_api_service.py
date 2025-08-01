"""This service is used to get data from the DARMA API."""

import datetime
import logging
import tempfile
import uuid
from enum import Enum
from pathlib import Path
from typing import List, Optional

import pandas as pd

# Import DA_batch_client functions (optional - may not be available in all environments)
try:
    from ..utils.da_batch_client.DA_batch_client import (
        get_result_file,
        request_and_save_parsed_data,
        save_result_file,
        upload_file,
    )

    DA_BATCH_CLIENT_AVAILABLE = True
except ImportError:
    # DA_batch_client not available (e.g., in CI environment)
    DA_BATCH_CLIENT_AVAILABLE = False

    # Create dummy functions that raise informative errors
    def get_result_file(client_id, flask_url):
        """Raise an error if DA_batch_client is not available."""
        raise ImportError(
            "DA_batch_client not available. This module contains proprietary code."
        )

    def request_and_save_parsed_data(client_ids, parsed_data_url, output_path):
        """Raise an error if DA_batch_client is not available."""
        raise ImportError(
            "DA_batch_client not available. This module contains proprietary code."
        )

    def save_result_file(base64_content, output_path):
        """Raise an error if DA_batch_client is not available."""
        raise ImportError(
            "DA_batch_client not available. This module contains proprietary code."
        )

    def upload_file(file_path, flask_url):
        """Raise an error if DA_batch_client is not available."""
        raise ImportError(
            "DA_batch_client not available. This module contains proprietary code."
        )


logger = logging.getLogger(__name__)


class DarmaApiSchema(Enum):
    """This enum is used to specify the schema of the DARMA API."""

    FT0ARCH = "FT0ARCH"


class DarmaApiService:
    """This service is used to get data from the DARMA API.

    Attributes:
        upload_url: The URL to upload the file to the DARMA API.
        result_url: The URL to get the result from the DARMA API.
        parsed_data_url: The URL to get the parsed data from the DARMA API.
    """

    def __init__(self):
        """Initialize the DARMA API service."""
        # Flask server URLs for DA_batch_client
        self.upload_url = "http://agrana-dev.cern.ch:5050/upload_base64"
        self.result_url = "http://agrana-dev.cern.ch:5050/generate_result"
        self.parsed_data_url = "http://agrana-dev.cern.ch:5050/get_parsed_data"

    def get_data(
        self,
        time_from: datetime.datetime,
        time_to: datetime.datetime,
        schema: DarmaApiSchema,
        elements: List[str],
        aliases: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Get data from the DARMA API.

        Args:
            time_from: The start time of the data to retrieve.
            time_to: The end time of the data to retrieve.
            schema: The schema of the data to retrieve.
            elements: The elements to retrieve.
            aliases: Optional list of aliases for the elements.

        Returns:
            A pandas DataFrame with columns: timestamp, value, element_name
        """
        if not DA_BATCH_CLIENT_AVAILABLE:
            logger.warning("DA_batch_client not available. Returning empty DataFrame.")
            return pd.DataFrame(columns=["timestamp", "value", "element_name"])

        # Create an input file
        input_file = self._create_input_file(
            time_from, time_to, schema, elements, aliases
        )

        # Create a base name for output files in the temporary directory
        output_base = Path(tempfile.gettempdir()) / f"darma_output_{uuid.uuid4()}"

        # Call DA_batch_client to get data and return a list of output files
        output_files = self._call_da_batch_client(input_file, output_base)

        # Parse and merge all response files into a single DataFrame
        return self._parse_multiple_responses(output_files)

    def _call_da_batch_client(self, input_file: Path, output_base: Path) -> List[Path]:
        """Call the DA_batch_client to retrieve data from the DARMA API.

        Args:
            input_file: Path to the input file.
            output_base: Base path for output files.

        Returns:
            List of paths to the output files created.
        """
        if not DA_BATCH_CLIENT_AVAILABLE:
            logger.warning("DA_batch_client not available. Returning empty file list.")
            return []

        output_files = []

        try:
            # Step 1: Upload file and get client IDs
            client_ids = upload_file(str(input_file), self.upload_url)

            if client_ids:
                # Step 2: Request parsed data if multiple client IDs
                if len(client_ids) > 1:
                    parsed_data_file_path = (
                        Path(tempfile.gettempdir())
                        / f"datapoints_list_{uuid.uuid4()}.txt"
                    )
                    request_and_save_parsed_data(
                        client_ids, self.parsed_data_url, str(parsed_data_file_path)
                    )

                # Step 3: Handle both single and multiple client IDs
                for idx, client_id in enumerate(client_ids, start=1):
                    # Request the result file using the client ID
                    result_file_base64 = get_result_file(client_id, self.result_url)

                    if result_file_base64:
                        # Save the result file locally
                        output_path = (
                            f"{output_base}_{idx}.csv"
                            if len(client_ids) > 1
                            else f"{output_base}.csv"
                        )
                        save_result_file(result_file_base64, output_path)
                        output_files.append(Path(output_path))
            else:
                logger.error("Failed to get client IDs from DA_batch_client")

        except Exception as e:
            logger.error(f"Error calling DA_batch_client: {e}")
            # Create empty output file if DA_batch_client fails
            empty_file = f"{output_base}.csv"
            Path(empty_file).touch()
            output_files.append(Path(empty_file))

        return output_files

    def _parse_response(self, output_file: Path) -> pd.DataFrame:
        """Parse the response CSV file from the DARMA API using pandas.

        Args:
            output_file: The path to the output file.

        Returns:
            A pandas DataFrame with columns: timestamp, value, element_name
        """
        try:
            # Read CSV with expected format and existing headers
            df = pd.read_csv(
                output_file,
                sep=";",
                dtype={
                    "date": str,
                    "time": str,
                    "element_name/alias": str,
                    "value": float,
                },
            )
        except (FileNotFoundError, pd.errors.ParserError):
            # Could log here
            return pd.DataFrame(columns=["timestamp", "value", "element_name"])

        # Rename the 'element_name/alias' column
        df.rename(columns={"element_name/alias": "element_name"}, inplace=True)

        # Combine date and time into single datetime column
        datetime_strs = df["date"] + " " + df["time"]
        df["timestamp"] = pd.to_datetime(
            datetime_strs, format="%Y-%m-%d %H:%M:%S", errors="coerce"
        )

        # Drop rows where timestamp could not be parsed
        df = df.dropna(subset=["timestamp"])

        # Keep only needed columns and reorder
        result = df[["timestamp", "value", "element_name"]].copy()

        return result

    def _parse_multiple_responses(self, output_files: List[Path]) -> pd.DataFrame:
        """Parse multiple response CSV files from the DARMA API and merge them.

        Args:
            output_files: List of paths to the output files.

        Returns:
            A pandas DataFrame with columns: timestamp, value, element_name
        """
        if not output_files:
            return pd.DataFrame(columns=["timestamp", "value", "element_name"])

        # Parse each file and collect DataFrames
        dataframes = []
        for output_file in output_files:
            if output_file.exists():
                df = self._parse_response(output_file)
                if not df.empty:
                    dataframes.append(df)

        # Merge all DataFrames
        if dataframes:
            result = pd.concat(dataframes, ignore_index=True)
            # Sort by timestamp
            result = result.sort_values("timestamp").reset_index(drop=True)
            return result
        else:
            return pd.DataFrame(columns=["timestamp", "value", "element_name"])

    def _create_input_file(
        self,
        time_from: datetime.datetime,
        time_to: datetime.datetime,
        schema: DarmaApiSchema,
        elements: List[str],
        aliases: Optional[List[str]] = None,
    ) -> Path:
        """Create a CSV input file for the DARMA API.

        Args:
            time_from: The start time of the data to retrieve.
            time_to: The end time of the data to retrieve.
            schema: The schema of the data to retrieve.
            elements: The elements to retrieve.
            aliases: Optional list of aliases for the elements.

        Returns:
            Path to the input file.
        """
        # Create a temporary file with a unique name
        temp_dir = tempfile.gettempdir()
        unique_id = str(uuid.uuid4())[:8]  # Use first 8 characters of UUID
        temp_file = Path(temp_dir) / f"darma_input_{unique_id}.csv"

        # Format dates as DD.MM.YYYY
        time_from_str = time_from.strftime("%d.%m.%Y")
        time_to_str = time_to.strftime("%d.%m.%Y")

        # Format times as H:M:S.0 (matching the manual test format)
        time_from_time = time_from.strftime("%H:%M:%S.0")
        time_to_time = time_to.strftime("%H:%M:%S.0")

        # Write the file directly to match the exact format from manual test
        with open(temp_file, "w", encoding="utf-8") as f:
            # Write timefrom line
            f.write(f"timefrom;{time_from_str};{time_from_time};\n")

            # Write timeto line
            f.write(f"timeto;{time_to_str};{time_to_time};\n")

            # Write schema line
            f.write(f"schema;{schema.value};\n")

            # Write element line
            if elements:
                element_line = "element;" + ";".join(elements) + "\n"
                f.write(element_line)

            # Write alias line if provided
            if aliases:
                alias_line = "alias;" + ";".join(aliases) + "\n"
                f.write(alias_line)

        return temp_file
