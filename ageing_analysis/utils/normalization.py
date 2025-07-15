"""Normalization utilities for FIT detector ageing analysis."""

import re


def normalize_channel_name(channel_name: str) -> str:
    """Normalize channel name to standard format.

    This function handles various channel name formats and converts them to
    the standard format used by the application (e.g., "CH01").

    Args:
        channel_name: The channel name to normalize (e.g., "Ch01", "ch01", "CH1")

    Returns:
        Normalized channel name in standard format (e.g., "CH01")
    """
    if not channel_name:
        return channel_name

    # Remove any non-alphanumeric characters and convert to uppercase
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", channel_name.upper())

    # Extract the channel number
    match = re.search(r"CH?(\d+)", cleaned)
    if match:
        channel_num = int(match.group(1))
        return f"CH{channel_num:02d}"

    # If no match found, return the original cleaned name
    return cleaned


def normalize_pm_name(pm_name: str) -> str:
    """Normalize PM name to standard format.

    Args:
        pm_name: The PM name to normalize (e.g., "PMA0", "pma0")

    Returns:
        Normalized PM name in standard format (e.g., "PMA0")
    """
    if not pm_name:
        return pm_name

    return pm_name.upper()
