"""This module contains the ControlServerLogsService class.

This class is used to parse the control server logs and save the configuration loads
to a parquet file. It supports processing both individual
files and directories of files, including handling compressed archives.
"""


import os
import re
import tarfile
import tempfile
import traceback
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from ageing_analysis.utils.file_utils import safe_extract_tar, safe_extract_zip


class ControlServerLogsError(Exception):
    """Base exception for control server logs errors."""


class ControlServerLogsParsingError(ControlServerLogsError):
    """Raised when a configuration load line cannot be parsed properly.

    Occurs when a line matches the configuration load pattern but the timestamp
    cannot be extracted or parsed.
    """


class ControlServerLogsService:
    """A class to parse control server logs and save the configuration loads.

    This class handles parsing control server logs and saving the configuration loads
    to a parquet file format. It supports processing both individual
    files and directories of files, including handling compressed archives.
    """

    CONFIG_LOAD_PATTERN = re.compile(
        r"Settings loaded (?:and applied )?from file .*?configuration/([^/\s]+\.cfg)"
    )

    def __init__(
        self,
        detector_name: str = "FT0",
        output_file_path: str = (
            "storage/configuration_loads/configuration_loads.parquet"
        ),
        error_file_path: str = (
            "storage/configuration_loads/configuration_loads_errors.log"
        ),
    ):
        """Initialize the ControlServerLogsService.

        Args:
          detector_name: The name of the detector. Defaults to "FT0".
          output_file_path: The path to the output parquet file. Defaults to
            "storage/configuration_loads/configuration_loads.parquet".
          error_file_path: The path to the error log file. Defaults to
            "storage/configuration_loads/configuration_loads_errors.log".
        """
        self.detector_name = detector_name
        self.output_file_path = output_file_path
        self.error_file_path = error_file_path

    def save_configuration_loads_from_path(self, path: str) -> None:
        """Save the configuration loads from a path to a parquet file.

        The function will save the configuration loads for all logs in the
        path. The function works for paths to a single file or a directory. The function
        checks the files recursively. If the directory contains zip or tar files, the
        function will extract the files and save the configuration loads for each file.

        Args:
          path: The path to the directory containing the control server logs.

        Raises:
          Exception: If an unexpected error occurs.
        """
        root = Path(path)
        # Ensure output and error directories exist
        try:
            Path(self.output_file_path).parent.mkdir(parents=True, exist_ok=True)
            Path(self.error_file_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            raise Exception(
                f"Error creating output and error directories: {self.output_file_path} "
                f"and {self.error_file_path}"
            )

        # Aggregation state
        total_log_files = 0
        processed_ok = 0
        processed_failed = 0
        counts_by_type: Dict[str, int] = defaultdict(int)
        error_details: List[str] = []

        def _record_error(
            kind: str, file_path: Path, exc: Exception | None = None
        ) -> None:
            nonlocal processed_failed
            processed_failed += 1
            counts_by_type[kind] += 1
            if exc is None:
                msg = f"[{kind}] {file_path}"
            else:
                msg = f"[{kind}] {file_path} :: {exc}"
            # Keep a short stack for debugging without being too noisy
            if exc is not None:
                tb = "".join(traceback.format_exception_only(type(exc), exc)).strip()
                msg = f"{msg}\n  -> {tb}"
            error_details.append(msg)

        # Determine if a path looks like an archive we should try to open
        def _is_zip(p: Path) -> bool:
            try:
                return p.is_file() and zipfile.is_zipfile(p)
            except Exception:
                return False

        def _is_tar(p: Path) -> bool:
            try:
                return p.is_file() and tarfile.is_tarfile(p)
            except Exception:
                return False

        # Process a single log file by calling the provided helper.
        def _process_log(p: Path) -> None:
            nonlocal total_log_files, processed_ok
            total_log_files += 1
            try:
                self._save_configuration_loads_from_file(file_path=str(p))
                processed_ok += 1
            except Exception as e:
                # Count and record, but do not propagate.
                _record_error(type(e).__name__, p, e)

        # Extract an archive into temp_dir/dest_name and return the extraction path
        def _extract_archive(p: Path, temp_dir: Path) -> Path | None:
            dest = temp_dir / f"extracted_{p.stem}_{abs(hash(p))}"
            dest.mkdir(parents=True, exist_ok=True)
            try:
                if _is_zip(p):
                    with zipfile.ZipFile(p) as zf:
                        safe_extract_zip(zf, dest)
                    return dest
                if _is_tar(p):
                    # Allow any compression handled by tarfile
                    with tarfile.open(p) as tf:
                        safe_extract_tar(tf, dest)
                    return dest
                return None
            except Exception as e:
                _record_error("ArchiveExtractionError", p, e)
                return None

        # Walk logic: we handle files and directories, extracting archives
        # and scanning recursively.
        visited_dirs: set[Path] = set()
        processed_files: set[Path] = set()

        def _walk_and_process(start: Path, temp_dir: Path) -> None:
            # Normalize to absolute to reduce duplicates
            stack = [start.resolve()]
            while stack:
                current = stack.pop()
                try:
                    if current.is_dir():
                        # Avoid cycles
                        if current in visited_dirs:
                            continue
                        visited_dirs.add(current)
                        for child in current.iterdir():
                            stack.append(child.resolve())
                    elif current.is_file():
                        if current in processed_files:
                            continue
                        processed_files.add(current)

                        # If log file -> process (check for common log extensions)
                        if (
                            current.suffix.lower() in [".log", ".txt"]
                            or "log" in current.name.lower()
                            or current.name.endswith(".log")
                            or current.name.endswith(".txt")
                        ):
                            _process_log(current)
                            continue

                        # If archive -> extract then scan extracted directory
                        if _is_zip(current) or _is_tar(current):
                            extracted = _extract_archive(current, temp_dir)
                            if extracted and extracted.exists():
                                stack.append(extracted.resolve())
                            continue

                        # Otherwise ignore non-log regular file
                    else:
                        # Symlink or special file: ignore silently
                        continue
                except Exception as e:
                    # Unexpected filesystem error while traversing
                    _record_error("TraversalError", current, e)

        # Validate root existence; if missing, log and write an error file (no raise).
        if not root.exists():
            _record_error("PathNotFound", root)

        with tempfile.TemporaryDirectory(prefix="config_loads_") as td:
            temp_dir = Path(td)
            _walk_and_process(root, temp_dir)

        # Write error summary file
        try:
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            lines = []
            lines.append("# Configuration Loads Import Summary")
            lines.append(f"Timestamp: {now}")
            lines.append(f"Input path: {root}")
            lines.append(f"Detector: {self.detector_name}")
            lines.append(f"Output parquet: {self.output_file_path}")
            lines.append("")
            lines.append(f"Total log files discovered: {total_log_files}")
            lines.append(f"Succeeded: {processed_ok}")
            lines.append(f"Failed: {processed_failed}")
            if counts_by_type:
                lines.append("")
                lines.append("Failure counts by type:")
                for k in sorted(counts_by_type.keys()):
                    lines.append(f"- {k}: {counts_by_type[k]}")
            else:
                lines.append("")
                lines.append("No errors encountered.")

            if error_details:
                lines.append("")
                lines.append("Error details:")
                for msg in error_details:
                    lines.append(f"- {msg}")

            content = "\n".join(lines) + "\n"
            with open(self.error_file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"Error writing error file {self.error_file_path}: {e}")

        # Function completes without raising, per requirements.
        return None

    def _save_configuration_loads_from_file(self, file_path: str) -> None:
        """Save the configuration loads from a file to a parquet file.

        The dataframe format is:
        - timestamp: The timestamp of the configuration load.
        - configuration_name: The name of the configuration loaded.

        Args:
          file_path: The path to the file containing the control server logs.

        Raises:
          ControlServerLogsParsingError: If the configuration load line cannot be parsed
            properly.
          ControlServerLogsError: If there are file system errors or other issues.
        """
        # Read existing data if parquet file exists
        if os.path.exists(self.output_file_path):
            try:
                existing_df = pd.read_parquet(self.output_file_path)
            except Exception:
                existing_df = pd.DataFrame(columns=["timestamp", "configuration_name"])
        else:
            existing_df = pd.DataFrame(columns=["timestamp", "configuration_name"])

        # Parse the file and collect new configuration loads
        new_config_loads: list[tuple[datetime, str]] = []

        try:
            with open(file_path, encoding="utf-8") as file:
                for line_num, line in enumerate(file, 1):
                    try:
                        result = self._parse_line(line.strip())
                        if result is not None:
                            config_name, timestamp = result
                            new_config_loads.append((timestamp, config_name))
                    except ControlServerLogsParsingError as e:
                        raise ControlServerLogsParsingError(
                            f"Line {line_num}: {e}"
                        ) from e

            new_df = pd.DataFrame(
                new_config_loads, columns=["timestamp", "configuration_name"]
            )
        except FileNotFoundError:
            raise ControlServerLogsError(f"File not found: {file_path}")
        except PermissionError:
            raise ControlServerLogsError(f"Permission denied reading file: {file_path}")
        except Exception as e:
            raise ControlServerLogsError(f"Error reading file {file_path}: {e}")

        # Combine and drop duplicates
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df.drop_duplicates(
            subset=["timestamp", "configuration_name"], inplace=True
        )
        combined_df.sort_values("timestamp", inplace=True)

        # Ensure output directory exists
        output_dir = Path(self.output_file_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Filter out consecutive duplicates of the same configuration
        combined_df = self._filter_consecutive_configuration_duplicates(combined_df)

        # Save to parquet file
        combined_df.to_parquet(self.output_file_path, index=False)

    def _parse_line(self, line: str) -> Tuple[str, datetime] | None:
        """Parse a line of log and return the configuration name and timestamp.

        If the line is not a configuration load, return None.

        Args:
          line: The raw line of control server log.

        Returns:
          A tuple of the configuration name and the timestamp or None if the line is not
          a configuration load.
        """
        # Check if the line matches the configuration load pattern
        match = self.CONFIG_LOAD_PATTERN.search(line)
        if not match:
            return None

        # Extract the configuration filename
        config_filename = match.group(1)

        # Remove the .cfg extension to get the configuration name
        config_name = config_filename.replace(".cfg", "")

        # Extract timestamp from the beginning of the line
        # Format: YYYY-MM-DD HH:MM:SS.mmm
        timestamp_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})"
        timestamp_match = re.search(timestamp_pattern, line)

        if not timestamp_match:
            raise ControlServerLogsParsingError(
                "Configuration load pattern found but timestamp could not be extracted "
                f"from line: {line}"
            )

        try:
            timestamp_str = timestamp_match.group(1)
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
            return (config_name, timestamp)
        except ValueError as e:
            raise ControlServerLogsParsingError(
                "Configuration load pattern found but timestamp could not be parsed "
                f"from line: {line}"
            ) from e

    def _filter_consecutive_configuration_duplicates(
        self, df: pd.DataFrame
    ) -> pd.DataFrame:
        """Filter out consecutive duplicates of the same configuration.

        If there are multiple consecutive timestamps with the same configuration,
        keep only the first occurrence.

        Args:
            df: DataFrame with columns ["timestamp", "configuration_name"]

        Returns:
            DataFrame with consecutive duplicates removed, keeping only the first
            occurrence of each configuration in consecutive sequences.
        """
        if df.empty:
            return df

        # Sort by timestamp
        df_sorted = df.sort_values("timestamp").reset_index(drop=True)

        # Compare each row with the previous one to find where the configuration changes
        config_changed = (
            df_sorted["configuration_name"] != df_sorted["configuration_name"].shift()
        )

        # Keep only the rows where configuration changed
        return df_sorted[config_changed].reset_index(drop=True)
