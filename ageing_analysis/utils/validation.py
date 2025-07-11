"""Validation utilities for FIT detector ageing analysis."""

import logging
import os
from pathlib import Path

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
