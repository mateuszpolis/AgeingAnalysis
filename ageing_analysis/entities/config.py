"""Configuration entity for FIT detector ageing analysis."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List

from ..utils.validation import validate_integrated_charge_format
from .dataset import Dataset

logger = logging.getLogger(__name__)


class Config:
    """Config class to store multiple datasets, organized by date."""

    def __init__(self, config_path: str = None):
        """Load the config file and initialize datasets.

        Args:
            config_path: Optional path to config file. If None, searches for
                default files.
        """
        logger.debug("Loading config...")

        # Determine which config file to use
        if config_path and os.path.exists(config_path):
            self._load_config_file(config_path)
        else:
            # First try to load ageing_analysis_results.json for visualization
            results_path = os.path.join("ageing_analysis_results.json")
            if os.path.exists(results_path):
                logger.info("Loading analysis results for visualization...")
                self._load_analysis_results(results_path)
                return

            # If results file not found, try to load config.json for analysis
            config_path = os.path.join("config.json")
            if os.path.exists(config_path):
                self._load_config_file(config_path)
            else:
                raise FileNotFoundError(
                    "Neither config.json nor ageing_analysis_results.json found"
                )

    def _load_config_file(self, config_path: str):
        """Load configuration from config.json file.

        Args:
            config_path: Path to the configuration file.
        """
        logger.debug(f"Loading configuration from {os.path.abspath(config_path)}")

        with open(config_path) as file:
            config = json.load(file)

        # Validate the 'inputs' field in the config file
        if "inputs" not in config:
            raise ValueError("inputs field not found in config file")

        logger.debug(f"Found {len(config['inputs'])} input datasets in configuration")

        # Get global basePath if provided
        global_base_path = config.get("basePath", "")
        if global_base_path:
            logger.debug(f"Global basePath specified: {global_base_path}")
        else:
            logger.debug("No global basePath specified")

        # Log the current working directory
        logger.debug(f"Current working directory: {os.getcwd()}")

        self.datasets = self._load_datasets(config["inputs"], global_base_path)

        logger.info(f"Config loaded successfully: {len(self.datasets)} datasets found.")
        logger.debug(self)

    def _load_analysis_results(self, results_path: str):
        """Load analysis results from the results file for visualization only.

        This method is used only for visualization purposes, not for running analysis.
        It loads the results data directly into the config object and
        sets datasets to an empty list.

        Args:
            results_path: Path to the results file.
        """
        logger.debug(f"Loading analysis results from {results_path}...")
        with open(results_path) as file:
            self.results_data = json.load(file)

        # Store the results data directly in the config object
        # This will be used by the visualization dashboard
        self.datasets = []  # Empty datasets list since we're using results directly

        logger.info("Analysis results loaded successfully for visualization.")

    def _load_datasets(
        self, inputs: List[Dict], global_base_path: str = ""
    ) -> List[Dataset]:
        """Load datasets from the config inputs.

        Args:
            inputs: List of input datasets from config.
            global_base_path: Global base path to prepend to all dataset paths.

        Returns:
            List of Dataset objects.
        """
        datasets = []

        # Get the project root directory (where config.json is located)
        root_dir = Path.cwd()
        logger.debug(f"Project root directory: {root_dir}")

        # Resolve global base path
        resolved_global_base_path = ""
        if global_base_path:
            if os.path.isabs(global_base_path):
                resolved_global_base_path = global_base_path
                logger.debug(
                    f"Global basePath is absolute: {resolved_global_base_path}"
                )
            else:
                resolved_global_base_path = os.path.abspath(
                    os.path.join(root_dir, global_base_path)
                )
                logger.debug(
                    f"Resolved global basePath from relative to absolute: "
                    f"{resolved_global_base_path}"
                )

        for input_data in inputs:
            date = input_data.get("date")
            if not date:
                raise ValueError("date field missing in one of the input datasets")

            # Get the dataset-specific base path
            dataset_base_path = input_data.get("basePath", "")
            logger.debug(f"Original dataset base path for {date}: {dataset_base_path}")

            # Combine global base path with dataset base path
            if resolved_global_base_path and dataset_base_path:
                # Both global and dataset paths exist
                if os.path.isabs(dataset_base_path):
                    # Dataset path is absolute, use it as-is (ignore global path)
                    base_path = dataset_base_path
                    logger.debug(f"Dataset path is absolute, using as-is: {base_path}")
                else:
                    # Dataset path is relative, combine with global path
                    base_path = os.path.join(
                        resolved_global_base_path, dataset_base_path
                    )
                    logger.debug(f"Combined global + dataset path: {base_path}")
            elif resolved_global_base_path:
                # Only global path exists
                base_path = resolved_global_base_path
                logger.debug(f"Using global path only: {base_path}")
            elif dataset_base_path:
                # Only dataset path exists
                if os.path.isabs(dataset_base_path):
                    base_path = dataset_base_path
                    logger.debug(f"Using absolute dataset path: {base_path}")
                else:
                    base_path = os.path.abspath(
                        os.path.join(root_dir, dataset_base_path)
                    )
                    logger.debug(f"Resolved relative dataset path: {base_path}")
            else:
                # No path specified, use current directory
                base_path = str(root_dir)
                logger.debug(f"No path specified, using current directory: {base_path}")

            # Normalize the path
            base_path = os.path.normpath(base_path)
            logger.debug(f"Final normalized base path for {date}: {base_path}")

            # Check if the path exists
            if not os.path.exists(base_path):
                logger.warning(
                    f"basePath {base_path} does not exist. Skipping dataset {date}."
                )
                continue  # Skip this dataset instead of failing the entire analysis
            else:
                logger.debug(f"Path exists: {base_path}")

            files = input_data.get("files", {})
            logger.debug(f"Found {len(files)} files for dataset {date}")

            ref_ch = input_data.get("refCH", {})
            if not isinstance(ref_ch, dict):
                raise Exception("refCH field must be a dictionary (see README)")
            if ref_ch.get("PM") is None:
                raise Exception("refCH field missing PM key (reference PM, see README)")
            if ref_ch.get("CH") is None:
                raise Exception(
                    "refCH field missing CH key (list of reference channels, "
                    "see README)"
                )
            validate_header = input_data.get("validateHeader", False)

            # Get integrated charge data if available
            integrated_charge_data = input_data.get("integratedCharge", None)

            # Validate integrated charge data format
            if integrated_charge_data is not None:
                if not validate_integrated_charge_format(integrated_charge_data, date):
                    logger.warning(
                        "Integrated charge data format validation failed for "
                        f"dataset {date}. "
                        "Continuing analysis without integrated charge data."
                    )
                    integrated_charge_data = None

            dataset = Dataset(
                date, base_path, files, ref_ch, validate_header, integrated_charge_data
            )

            datasets.append(dataset)
            logger.debug(f"Added dataset {date} to the list")

        # Sort the datasets by date
        datasets.sort(key=lambda x: x.date)

        if not datasets:
            logger.warning("No valid datasets found in the configuration.")
        else:
            logger.debug(
                f"Loaded {len(datasets)} datasets: {[d.date for d in datasets]}"
            )

        return datasets

    def to_dict(self, include_signal_data: bool = False) -> Dict:
        """Convert the Config to a dictionary.

        Args:
            include_signal_data: Whether to include signal data.

        Returns:
            Dictionary representation of the Config.
        """
        # If we have loaded results data, return it directly
        if hasattr(self, "results_data"):
            return dict(self.results_data)

        # Otherwise, convert datasets to dictionary
        return {
            "datasets": [
                dataset.to_dict(include_signal_data)
                for dataset in sorted(self.datasets, key=lambda x: x.date)
            ]
        }

    def __str__(self):
        """Return string representation of the Config."""
        dataset_str = "\n  ".join(str(dataset) for dataset in self.datasets)
        return f"Config(datasets=[\n  {dataset_str}\n])"

    def __repr__(self):
        """Return string representation of the Config."""
        return self.__str__()
