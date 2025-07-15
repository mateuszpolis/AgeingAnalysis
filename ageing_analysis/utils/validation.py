"""Validation utilities for FIT detector ageing analysis."""

import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def validate_csv(file_path: str, validate_header: bool = False) -> bool:
    """Validate a CSV file for ageing analysis.

    Args:
        file_path: Path to the CSV file to validate.
        validate_header: Whether to validate the header format.

    Returns:
        True if the file is valid, False otherwise.
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            return False

        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            logger.error(f"File is not readable: {file_path}")
            return False

        # Check file size (should not be empty)
        if os.path.getsize(file_path) == 0:
            logger.error(f"File is empty: {file_path}")
            return False

        # Basic CSV validation
        with open(file_path) as f:
            first_line = f.readline().strip()
            if not first_line:
                logger.error(f"File appears to be empty: {file_path}")
                return False

        # Optional header validation
        if validate_header:
            # Add specific header validation logic here if needed
            logger.debug(f"Header validation requested for {file_path}")

        logger.debug(f"File validation passed: {file_path}")
        return True

    except Exception as e:
        logger.error(f"Error validating file {file_path}: {e}")
        return False


def validate_file_identifier(identifier: str) -> bool:
    """Validate that a file identifier matches the expected PM format.

    Args:
        identifier: The identifier to validate (e.g., "PMA0", "PMC5").

    Returns:
        True if the identifier is valid, False otherwise.
    """
    import re

    # Pattern for PMA0-PMA9 and PMC0-PMC9
    pattern = re.compile(r"^PM[AC][0-9]$")
    return bool(pattern.match(identifier))


def validate_path_exists(path: str) -> bool:
    """Validate that a path exists and is accessible.

    Args:
        path: The path to validate.

    Returns:
        True if the path exists and is accessible, False otherwise.
    """
    try:
        path_obj = Path(path)
        return path_obj.exists() and path_obj.is_dir()
    except Exception as e:
        logger.error(f"Error validating path {path}: {e}")
        return False


def validate_integrated_charge_format(
    integrated_charge_data: Any, dataset_date: str
) -> bool:
    """Validate the format of integrated charge data.

    Expected format:
    {
        "PMA0": {
            "Ch01": 0.0,
            "Ch02": 0.0,
            ...
        },
        "PMA1": {
            "Ch01": 0.0,
            "Ch02": 0.0,
            ...
        },
        ...
    }

    Args:
        integrated_charge_data: The integrated charge data to validate.
        dataset_date: The date of the dataset for logging purposes.

    Returns:
        True if the format is valid, False otherwise.
    """
    if integrated_charge_data is None:
        return True  # None is valid (no integrated charge data)

    if not isinstance(integrated_charge_data, dict):
        logger.warning(
            f"Integrated charge data for dataset {dataset_date} is not a dictionary. "
            f"Expected dict, got {type(integrated_charge_data).__name__}. "
            "Integrated charge analysis will be skipped for this dataset."
        )
        return False

    # Validate PM structure
    for pm_name, pm_data in integrated_charge_data.items():
        # Check PM name format
        if not validate_file_identifier(pm_name):
            logger.warning(
                f"Invalid PM name '{pm_name}' in integrated charge data for "
                f"dataset {dataset_date}. "
                f"Expected format: PMA0-PMA9 or PMC0-PMC9. "
                "Integrated charge analysis will be skipped for this dataset."
            )
            return False

        # Check PM data structure
        if not isinstance(pm_data, dict):
            logger.warning(
                f"PM data for '{pm_name}' in dataset {dataset_date} is not a "
                f"dictionary. "
                f"Expected dict, got {type(pm_data).__name__}. "
                "Integrated charge analysis will be skipped for this dataset."
            )
            return False

        # Validate channel structure
        for channel_name, charge_value in pm_data.items():
            # Check channel name format (Ch01-Ch12)
            if not re.match(r"^Ch(0[1-9]|1[0-2])$", channel_name):
                logger.warning(
                    f"Invalid channel name '{channel_name}' for PM '{pm_name}' "
                    f"in dataset {dataset_date}. "
                    "Expected format: Ch01-Ch12. "
                    "Integrated charge analysis will be skipped for this dataset."
                )
                return False

            # Check charge value type
            if not isinstance(charge_value, (int, float)):
                logger.warning(
                    f"Invalid charge value type for channel '{channel_name}' in "
                    f"PM '{pm_name}' for dataset {dataset_date}. Expected number, "
                    f"got {type(charge_value).__name__}. "
                    "Integrated charge analysis will be skipped for this dataset."
                )
                return False

            # Check for negative values
            if charge_value < 0:
                logger.warning(
                    f"Negative charge value {charge_value} for channel "
                    f"'{channel_name}' in PM '{pm_name}' "
                    f"for dataset {dataset_date}. "
                    "Integrated charge analysis will be skipped for this dataset."
                )
                return False

    logger.debug(
        f"Integrated charge data format validation passed for dataset {dataset_date}"
    )
    return True
