"""Results saving utilities for FIT detector ageing analysis."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def save_results(config, output_path: str = None) -> str:
    """Save analysis results to a JSON file.

    Args:
        config: Configuration object containing analysis results.
        output_path: Optional path to save results. If None, uses default.

    Returns:
        Path to the saved results file.
    """
    try:
        # Generate default filename if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = (
                f"ageing_analysis_results/ageing_analysis_results_{timestamp}.json"
            )

        # Ensure the output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert config to dictionary
        results_data = config.to_dict(include_signal_data=False)

        # Add metadata
        results_data["metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "analysis_type": "ageing_analysis",
        }

        # Save to JSON file
        with open(output_file, "w") as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved successfully to {output_file}")
        return str(output_file)

    except Exception as e:
        logger.error(f"Error saving results: {e}")
        raise


def load_results(file_path: str) -> Dict[str, Any]:
    """Load analysis results from a JSON file.

    Args:
        file_path: Path to the results file.

    Returns:
        Dictionary containing the analysis results.
    """
    try:
        with open(file_path) as f:
            results = json.load(f)

        logger.info(f"Results loaded successfully from {file_path}")
        results_dict: Dict[str, Any] = results
        return results_dict

    except Exception as e:
        logger.error(f"Error loading results from {file_path}: {e}")
        raise


def export_results_csv(results: Dict[str, Any], output_path: str = None) -> str:
    """Export analysis results to CSV format.

    Args:
        results: Dictionary containing analysis results.
        output_path: Optional path to save CSV. If None, uses default.

    Returns:
        Path to the saved CSV file.
    """
    try:
        import pandas as pd

        # Generate default filename if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = (
                f"ageing_analysis_results/ageing_analysis_results_{timestamp}.csv"
            )

        # Flatten the results for CSV export
        flattened_data = []

        for dataset in results.get("datasets", []):
            date = dataset.get("date", "unknown")

            for module in dataset.get("modules", []):
                module_id = module.get("identifier", "unknown")

                for channel in module.get("channels", []):
                    channel_name = channel.get("name", "unknown")
                    means = channel.get("means", {})
                    ageing_factors = channel.get("ageing_factors", {})

                    row = {
                        "date": date,
                        "module": module_id,
                        "channel": channel_name,
                        "gaussian_mean": means.get("gaussian_mean", "N/A"),
                        "weighted_mean": means.get("weighted_mean", "N/A"),
                        "gaussian_ageing_factor": ageing_factors.get(
                            "gaussian_ageing_factor", "N/A"
                        ),
                        "weighted_ageing_factor": ageing_factors.get(
                            "weighted_ageing_factor", "N/A"
                        ),
                        "normalized_gauss_ageing_factor": ageing_factors.get(
                            "normalized_gauss_ageing_factor", "N/A"
                        ),
                        "normalized_weighted_ageing_factor": ageing_factors.get(
                            "normalized_weighted_ageing_factor", "N/A"
                        ),
                    }
                    flattened_data.append(row)

        # Create DataFrame and save to CSV
        df = pd.DataFrame(flattened_data)
        df.to_csv(output_path, index=False)

        logger.info(f"Results exported to CSV: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error exporting results to CSV: {e}")
        raise
