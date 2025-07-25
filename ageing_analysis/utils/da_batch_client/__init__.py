"""DA_batch_client package for communicating with the DARMA API server."""

try:
    from .DA_batch_client import (
        get_result_file,
        request_and_save_parsed_data,
        save_result_file,
        upload_file,
    )
except ImportError:
    # DA_batch_client not available (e.g., in CI environment)
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


__all__ = [
    "upload_file",
    "get_result_file",
    "save_result_file",
    "request_and_save_parsed_data",
]
