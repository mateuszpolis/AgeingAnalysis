"""This module contains the RangeCorrectionConfigurationParser class.

This class is used to parse the range correction configuration files and save the range
corrections to a parquet file.
"""

import json
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


class RangeCorrectionConfigurationError(Exception):
    """Base exception for range correction configuration errors."""


class RangeCorrectionNoDataError(RangeCorrectionConfigurationError):
    """Raised when no range correction data is found in the configuration file."""


class RangeCorrectionProcessingError(RangeCorrectionConfigurationError):
    """Raised when data is found but cannot be processed.

    Occurs when the data exists but cannot be processed properly, for example when
    type 0/1 values are missing.
    """


class RangeCorrectionIncompleteDataError(RangeCorrectionConfigurationError):
    """Raised when data is incomplete (missing PMs or channels).

    Occurs when the data exists but is incomplete, for example when PMs or channels
    are missing.
    """


class RangeCorrectionConflictError(RangeCorrectionConfigurationError):
    """Raised when there are conflicts between new and existing configuration data.

    Occurs when the data exists but there are conflicts between the new and existing
    data, for example when the same PM and channel have different values.
    """


class RangeCorrectionConfigurationParser:
    """A class to parse configuration files and save the range corrections.

    This class handles parsing configuration files containing range correction data and
    saves the extracted data to a parquet file format. It supports processing both
    individual files and directories of files, including handling compressed archives.
    """

    def __init__(
        self,
        detector_name: str = "FT0",
        output_file_path: str = "storage/range_correction/range_corrections.parquet",
        error_file_path: str = "storage/range_correction/range_corrections_errors.log",
    ):
        """Initialize the RangeCorrectionConfigurationParser.

        Args:
          detector_name: The name of the detector. Defaults to "FT0".
          output_file_path: The path to the output parquet file. Defaults to
            "storage/range_correction/range_corrections.parquet".
          error_file_path: The path to the error log file. Defaults to
            "storage/range_correction/range_corrections_errors.log".
        """
        self.detector_name = detector_name
        self.range_correction_mapping = self._get_range_correction_mapping()
        self.output_file_path = output_file_path
        self.error_file_path = error_file_path

    def save_range_corrections_from_path(
        self,
        path: str,
    ) -> None:
        """Save the range corrections from a path to a parquet file.

        The function will save the range corrections for all configuration files in the
        path. The function works for paths to a single file or a directory. The function
        checks the files recursively. If the directory contains zip or tar files, the
        function will extract the files and save the range corrections for each file.

        Args:
          path: The path to the directory containing the configuration files.

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
        total_cfg_files = 0
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

        # Process a single .cfg file by calling the provided helper.
        def _process_cfg(p: Path) -> None:
            nonlocal total_cfg_files, processed_ok
            total_cfg_files += 1
            try:
                self._save_range_corrections_from_config_file(
                    file_path=str(p),
                )
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
                        self._safe_extract_zip(zf, dest)
                    return dest
                if _is_tar(p):
                    # Allow any compression handled by tarfile
                    with tarfile.open(p) as tf:
                        self._safe_extract_tar(tf, dest)
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

                        # If config file -> process
                        if current.suffix.lower() == ".cfg":
                            _process_cfg(current)
                            continue

                        # If archive -> extract then scan extracted directory
                        if _is_zip(current) or _is_tar(current):
                            extracted = _extract_archive(current, temp_dir)
                            if extracted and extracted.exists():
                                stack.append(extracted.resolve())
                            continue

                        # Otherwise ignore non-cfg regular file
                    else:
                        # Symlink or special file: ignore silently
                        continue
                except Exception as e:
                    # Unexpected filesystem error while traversing
                    _record_error("TraversalError", current, e)

        # Validate root existence; if missing, log and write an error file (no raise).
        if not root.exists():
            _record_error("PathNotFound", root)

        with tempfile.TemporaryDirectory(prefix="range_corr_") as td:
            temp_dir = Path(td)
            _walk_and_process(root, temp_dir)

        # Write error summary file
        try:
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            lines = []
            lines.append("# Range Correction Import Summary")
            lines.append(f"Timestamp: {now}")
            lines.append(f"Input path: {root}")
            lines.append(f"Detector: {self.detector_name}")
            lines.append(f"Output parquet: {self.output_file_path}")
            lines.append("")
            lines.append(f"Total .cfg files discovered: {total_cfg_files}")
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

    def _safe_extract_zip(self, zf: zipfile.ZipFile, dest: Path):
        """Extract a zip file safely.

        Args:
          zf: The zip file to extract.
          dest: The destination directory to extract the zip file to.
        """
        for member in zf.namelist():
            member_path = dest / member
            if not member_path.resolve().is_relative_to(dest.resolve()):
                raise Exception(f"Unsafe path detected in zip: {member}")
            zf.extract(member, dest)

    def _safe_extract_tar(self, tf: tarfile.TarFile, dest: Path):
        """Extract a tar file safely.

        Args:
          tf: The tar file to extract.
          dest: The destination directory to extract the tar file to.
        """
        for member in tf.getmembers():
            member_path = dest / member.name
            if not member_path.resolve().is_relative_to(dest.resolve()):
                raise Exception(f"Unsafe path detected in tar: {member.name}")
            tf.extract(member, dest)

    def _save_range_corrections_from_config_file(self, file_path: str) -> None:
        """Save the range corrections from a configuration file to a parquet file.

        Args:
          file_path: The path to the file containing the range corrections.

        Raises:
          RangeCorrectionProcessingError: If the range correction data cannot be
            processed.
          RangeCorrectionIncompleteDataError: If the range correction data is
            incomplete.
          RangeCorrectionConflictError: If the range correction data has
            conflicts.
          Exception: If an unexpected error occurs.
        """
        # Get the new range corrections from the config file
        try:
            new_data = self._get_range_corrections_from_config_file(file_path)
        except RangeCorrectionNoDataError as e:
            raise RangeCorrectionNoDataError(
                f"No range correction data found in configuration file {file_path} "
                f"for detector {self.detector_name}. {e}"
            )
        except RangeCorrectionProcessingError as e:
            raise RangeCorrectionProcessingError(
                f"Error getting range corrections from config file {file_path} "
                f"for detector {self.detector_name}: {e}"
            )
        except RangeCorrectionIncompleteDataError as e:
            raise RangeCorrectionIncompleteDataError(
                f"Error getting range corrections from config file {file_path} "
                f"for detector {self.detector_name}: {e}"
            )
        except Exception as e:
            raise Exception(
                f"Error getting range corrections from config file {file_path} "
                f"for detector {self.detector_name}: {e}"
            )

        # Extract configuration name from file path
        config_name = os.path.splitext(os.path.basename(file_path))[0]

        # Load existing data if the parquet file exists
        existing_data = pd.DataFrame()
        if os.path.exists(self.output_file_path):
            existing_data = pd.read_parquet(self.output_file_path)

        # Check if this configuration already exists for this detector
        if not existing_data.empty:
            existing_config_data = existing_data[
                (existing_data["detector_name"] == self.detector_name)
                & (existing_data["configuration"] == config_name)
            ]

            if not existing_config_data.empty:
                # Configuration already exists - check for conflicts
                try:
                    self._check_configuration_conflicts(
                        new_data, existing_config_data, config_name
                    )
                except RangeCorrectionConflictError as e:
                    msg = (
                        f"Configuration {config_name} for detector "
                        f"{self.detector_name} has conflicts. {e}"
                    )
                    raise RangeCorrectionConflictError(msg)
                except UserWarning as e:
                    msg = (
                        f"Configuration {config_name} for detector "
                        f"{self.detector_name} already exists with identical values. "
                        f"{e}"
                    )
                    print(msg)
                except Exception as e:
                    raise Exception(
                        f"Error checking configuration conflicts for {config_name} "
                        f"for detector {self.detector_name}: {e}"
                    )

        # Merge new data with existing data
        merged_data = pd.concat([existing_data, new_data], ignore_index=True)

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(self.output_file_path), exist_ok=True)

        # Save the merged data
        merged_data.to_parquet(self.output_file_path, index=False)

    def _get_range_corrections_from_config_file(
        self,
        file_path: str,
    ) -> pd.DataFrame:
        """Get the range corrections from a configuration file.

        Args:
          file_path: The path to the file containing the range corrections.

        Returns:
          A pandas DataFrame containing the range corrections. The dataframe has
          columns for detector_name, configuration, PM, and channel information,
          where each row represents a range correction value for a specific channel
          within a PM for a given configuration and detector.

        Raises:
          RangeCorrectionNoDataError: If no range correction data is found in the
            configuration file.
          RangeCorrectionProcessingError: If the data is found but cannot be
            processed (e.g., missing type 0/1 values).
          RangeCorrectionIncompleteDataError: If the data is incomplete (missing
            PMs or channels).
        """
        # Setup and light pre-processing
        valid_pm_names = set(self._get_all_pm_names())
        pm_mapping = self._get_pm_mapping()
        config_name = os.path.splitext(os.path.basename(file_path))[0]

        # Pre-parse the mapping once: register -> (channel_num, type_str, channel_name)
        # This avoids repeated int() parsing of channel_name later.
        prepped_mapping: Dict[str, Tuple[int, str, str]] = {}
        for reg, (ch_name, ch_type) in self.range_correction_mapping.items():
            try:
                ch_num = int(ch_name[2:])  # "Ch01" -> 1
            except (ValueError, IndexError):
                # Skip invalid mapping entries; matches original logic that would
                # skip later
                continue
            prepped_mapping[reg] = (ch_num, str(ch_type), ch_name)

        # Regex to recognize [PM] headers and "reg=value" lines with hex values
        pm_header_re = re.compile(r"^\[(?P<pm>[^\]]+)\]\s*$")
        kv_re = re.compile(r"^(?P<reg>[^=\s]+)\s*=\s*(?P<val>[0-9A-Fa-f]+)\s*$")

        # Parse the file in a single pass
        rows: List[Tuple[str, str, str, int, str, str, str, int]] = []
        current_pm = None

        with open(file_path) as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue

                # New PM section?
                m = pm_header_re.match(line)
                if m:
                    pm = m.group("pm")
                    # Use PM mapping to handle channel switching (e.g., PMA8 -> PMA0)
                    normalized_pm = pm_mapping.get(pm)
                    if normalized_pm:
                        current_pm = normalized_pm
                    else:
                        current_pm = None
                    continue

                # Register lines inside a valid PM section
                if current_pm:
                    m = kv_re.match(line)
                    if not m:
                        continue

                    reg = m.group("reg")
                    # Fast-path reject when register isn't in mapping
                    meta = prepped_mapping.get(reg)
                    if meta is None:
                        continue

                    hex_val = m.group("val")
                    try:
                        dec_val = int(hex_val, 16)
                    except ValueError:
                        continue

                    ch_num, ch_type, ch_name = meta
                    rows.append(
                        (
                            self.detector_name,
                            config_name,
                            current_pm,
                            ch_num,
                            ch_name,
                            ch_type,
                            reg,
                            dec_val,
                        )
                    )

        # Build DataFrame
        df = pd.DataFrame(
            rows,
            columns=[
                "detector_name",
                "configuration",
                "pm",
                "channel",
                "channel_name",
                "type",
                "register",
                "value",
            ],
        )

        if df.empty:
            raise RangeCorrectionNoDataError(
                f"No range correction data found in configuration file for detector "
                f"{self.detector_name}. This suggests the configuration file format "
                f"is incorrect or the file is empty. Expected PM sections in format "
                f"[PMC8] with register values like reg25=000006C2."
            )

        # Vectorized averaging with exact original logic
        by = df.groupby(["pm", "channel", "type"])["value"].agg(["sum", "count"])
        unstacked = by.unstack("type", fill_value=0)

        # Extract sums and counts for '0' and '1' as strings (mapping uses string types)
        sum0 = unstacked.get(("sum", "0"), pd.Series(0, index=unstacked.index))
        sum1 = unstacked.get(("sum", "1"), pd.Series(0, index=unstacked.index))
        cnt0 = unstacked.get(("count", "0"), pd.Series(0, index=unstacked.index))
        cnt1 = unstacked.get(("count", "1"), pd.Series(0, index=unstacked.index))

        both_present = (cnt0 > 0) & (cnt1 > 0)
        total_sum = sum0 + sum1
        total_cnt = cnt0 + cnt1

        avg_series = (total_sum / total_cnt).where(both_present)
        avg_series.name = "value"

        result_df = avg_series.dropna().reset_index()
        if result_df.empty:
            found_pms = df["pm"].unique()
            found_channels = df["channel"].unique()
            raise RangeCorrectionProcessingError(
                f"Range correction data found but could not be processed for detector "
                f"{self.detector_name}. Found PMs: {list(found_pms)}. Found channels: "
                f"{list(found_channels)}. This suggests the data format is partially "
                f"correct but missing type 0 or type 1 values for averaging."
            )

        # Format output columns to match your existing contract
        result_df["detector_name"] = self.detector_name
        result_df["configuration"] = config_name
        result_df["channel"] = result_df["channel"].apply(lambda c: f"Ch{c:02d}")
        result_df = result_df[
            ["detector_name", "configuration", "pm", "channel", "value"]
        ]

        # Completeness validation
        self._validate_completeness_of_range_correction_data(
            result_df, list(valid_pm_names)
        )

        return result_df

    def _get_range_correction_mapping(self) -> Dict[str, Tuple[str, str]]:
        """Get the range correction mapping for a given detector name.

        Args:
          detector_name: The name of the detector.

        Returns:
          A dictionary with the range correction mapping.
          The key is the name of the register (e.g. "reg3C")
          and the value is a tuple of the Channel and it's type, either 0 or 1.
        """
        with open(f"storage/range_correction/mappings/{self.detector_name}.json") as f:
            data = json.load(f)

        # Extract the registers mapping from the JSON structure
        registers_data = data.get("registers", {})

        # Convert the list values to tuples as specified in the return type
        mapping = {}
        for register, channel_info in registers_data.items():
            if isinstance(channel_info, list) and len(channel_info) == 2:
                mapping[register] = (channel_info[0], channel_info[1])

        return mapping

    def _get_all_pm_names(self, include_channel_switching: bool = True) -> List[str]:
        """Get the names of all PMs for a given detector.

        Args:
          include_channel_switching: If True, includes PMs used for channel switching
            (like PMA8). If False, excludes them since they get normalized to other PMs.

        Returns:
          A list of the names of all PMs for the given detector.

        Raises:
          ValueError: If the detector name is not supported.
        """
        if self.detector_name == "FT0":
            # PMA0-PMA7 and PMC0-PMC9
            pma_names = [f"PMA{i}" for i in range(8)]
            pmc_names = [f"PMC{i}" for i in range(10)]

            if include_channel_switching:
                # Add PMA8 for channel switching cases
                pma_names.append("PMA8")

            return pma_names + pmc_names
        else:
            raise ValueError(f"Detector name {self.detector_name} not supported")

    def _get_pm_mapping(self) -> Dict[str, str]:
        """Get the PM mapping to handle channel switching cases.

        Returns:
          A dictionary mapping from actual PM names in config files to
          normalized PM names. For example, PMA8 -> PMA0 for channel switching cases.
        """
        if self.detector_name == "FT0":
            # Normal mapping (no switching)
            normal_mapping = {f"PMA{i}": f"PMA{i}" for i in range(8)}
            pmc_mapping = {f"PMC{i}": f"PMC{i}" for i in range(10)}

            # Channel switching mapping: PMA8 -> PMA0
            switching_mapping = {"PMA8": "PMA0"}

            return {**normal_mapping, **pmc_mapping, **switching_mapping}
        else:
            raise ValueError(f"Detector name {self.detector_name} not supported")

    def _validate_completeness_of_range_correction_data(
        self, result_df: pd.DataFrame, valid_pm_names: List[str]
    ) -> None:
        """Validate that all PMs and all 12 channels for each PM are present in results.

        Args:
          result_df: The DataFrame containing the range correction results.
          valid_pm_names: List of all valid PM names for the detector.

        Raises:
          RangeCorrectionNoDataError: If no range correction data is found.
          RangeCorrectionIncompleteDataError: If any PMs or channels are missing,
              with detailed information about what's missing.
        """
        if result_df.empty:
            raise RangeCorrectionNoDataError(
                f"No range correction data found for detector {self.detector_name}"
            )

        # Use expected PMs for validation (excludes channel switching PMs like PMA8)
        expected_pms = set(self._get_all_pm_names(include_channel_switching=False))

        # Check for missing PMs
        found_pms = set(result_df["pm"].unique())
        missing_pms = expected_pms - found_pms

        # Check for missing channels for each PM
        missing_channels = []
        for pm in found_pms:
            pm_channels = set(result_df[result_df["pm"] == pm]["channel"].unique())
            expected_channels = {
                f"Ch{i:02d}" for i in range(1, 13)
            }  # Channels Ch01-Ch12
            pm_missing_channels = expected_channels - pm_channels

            for channel in pm_missing_channels:
                # Extract channel number from channel name (e.g., "Ch01" -> 1)
                channel_num = int(channel[2:])  # Remove "Ch" prefix
                missing_channels.append(
                    {
                        "pm": pm,
                        "channel": channel_num,
                        "channel_name": channel,
                        "description": f"Missing channel {channel} for PM {pm}",
                    }
                )

        # If there are any missing items, create detailed error message
        if missing_pms or missing_channels:
            error_parts = []

            if missing_pms:
                error_parts.append(f"Missing PMs: {', '.join(sorted(missing_pms))}")

            if missing_channels:
                total_missing = len(missing_channels)
                error_parts.append(f"Missing {total_missing} channels total")

                # Show first 5 missing channels with details
                first_5_missing = missing_channels[:5]
                missing_details = []
                for item in first_5_missing:
                    missing_details.append(
                        f"PM: {item['pm']}, Channel: {item['channel']} "
                        f"({item['channel_name']})"
                    )

                error_parts.append(
                    f"First {len(first_5_missing)} missing channels: "
                    f"{'; '.join(missing_details)}"
                )

                if total_missing > 5:
                    error_parts.append(
                        f"... and {total_missing - 5} more missing channels"
                    )

            error_message = (
                f"Range correction data incomplete for detector {self.detector_name}. "
                f"{'; '.join(error_parts)}"
            )
            raise RangeCorrectionIncompleteDataError(error_message)

    def _check_configuration_conflicts(
        self, new_data: pd.DataFrame, existing_data: pd.DataFrame, config_name: str
    ) -> None:
        """Check for conflicts between new and existing configuration data.

        Args:
          new_data: The new range correction data.
          existing_data: The existing range correction data for the same
            detector/configuration.
          config_name: The name of the configuration.

        Raises:
          RangeCorrectionConflictError: If the configuration has different values.
          UserWarning: If the configuration has identical values.
        """
        # Merge the dataframes on the key columns for comparison
        comparison_columns = ["detector_name", "configuration", "pm", "channel"]

        # Ensure both dataframes have the same structure
        new_data_subset = new_data[comparison_columns + ["value"]].copy()
        existing_data_subset = existing_data[comparison_columns + ["value"]].copy()

        # Rename the value columns to distinguish between new and existing
        new_data_subset = new_data_subset.rename(columns={"value": "new_value"})
        existing_data_subset = existing_data_subset.rename(
            columns={"value": "existing_value"}
        )

        # Merge on the key columns
        merged = new_data_subset.merge(
            existing_data_subset, on=comparison_columns, how="outer"
        )

        # Check for missing data in either dataset
        missing_in_new = merged[merged["new_value"].isna()]
        missing_in_existing = merged[merged["existing_value"].isna()]

        if not missing_in_new.empty or not missing_in_existing.empty:
            missing_details = []
            if not missing_in_new.empty:
                missing_details.append(
                    f"Missing in new data: {len(missing_in_new)} entries"
                )
            if not missing_in_existing.empty:
                missing_details.append(
                    f"Missing in existing data: {len(missing_in_existing)} entries"
                )

            raise RangeCorrectionConflictError(
                f"Configuration {config_name} for detector {self.detector_name} "
                f"has structural differences. {'; '.join(missing_details)}"
            )

        # Check for value differences
        merged["value_difference"] = merged["new_value"] - merged["existing_value"]
        different_values = merged[merged["value_difference"] != 0]

        if not different_values.empty:
            # There are conflicting values - this is a serious error
            conflict_count = len(different_values)
            first_5_conflicts = different_values.head(5)

            conflict_details = []
            for _, row in first_5_conflicts.iterrows():
                conflict_details.append(
                    f"PM: {row['pm']}, Channel: {row['channel']} "
                    f"(new: {row['new_value']}, existing: {row['existing_value']}, "
                    f"diff: {row['value_difference']})"
                )

            error_message = (
                f"Configuration {config_name} for detector {self.detector_name} "
                f"has {conflict_count} conflicting values. "
                f"First 5 conflicts: {'; '.join(conflict_details)}"
            )

            if conflict_count > 5:
                error_message += f"; ... and {conflict_count - 5} more conflicts"

            raise RangeCorrectionConflictError(error_message)

        # If we get here, all values are identical - this is just a warning
        import warnings

        warnings.warn(
            f"Configuration {config_name} for detector {self.detector_name} "
            f"already exists with identical values. "
            f"This is a duplicate configuration.",
            UserWarning,
            stacklevel=2,
        )
