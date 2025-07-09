import json
import os
from typing import Dict, List

from configs.logger_config import logger
from fit_detector.apps.ageing.entities.dataset import Dataset


class Config:
    """Config class to store multiple datasets, organized by date."""

    def __init__(self):
        """Load the config file and initialize datasets."""
        logger.debug("Loading config...")

        # First try to load ageing_analysis_results.json for visualization
        results_path = os.path.join("ageing_analysis_results.json")
        if os.path.exists(results_path):
            logger.info("Loading analysis results for visualization...")
            self._load_analysis_results(results_path)
            return

        # If results file not found, try to load config.json for analysis
        config_path = os.path.join("config.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError("Neither config.json nor ageing_analysis_results.json found")

        logger.debug(f"Loading configuration from {os.path.abspath(config_path)}")
        with open(config_path, "r") as file:
            config = json.load(file)

        # Validate the 'inputs' field in the config file
        assert "inputs" in config, "inputs field not found in config file"

        logger.debug(f"Found {len(config['inputs'])} input datasets in configuration")

        # Log the current working directory
        logger.debug(f"Current working directory: {os.getcwd()}")

        self.datasets = self._load_datasets(config["inputs"])

        logger.info(f"Config loaded successfully: {len(self.datasets)} datasets found.")
        logger.debug(self)

    def _load_analysis_results(self, results_path):
        """Load analysis results from the results file for visualization only.

        This method is used only for visualization purposes, not for running analysis.
        It loads the results data directly into the config object and
        sets datasets to an empty list.

        Args:
            results_path (str): Path to the results file.
        """
        logger.debug(f"Loading analysis results from {results_path}...")
        with open(results_path, "r") as file:
            self.results_data = json.load(file)

        # Store the results data directly in the config object
        # This will be used by the visualization dashboard
        self.datasets = []  # Empty datasets list since we're using results directly

        logger.info("Analysis results loaded successfully for visualization.")

    def _load_datasets(self, inputs: List[Dict]) -> List[Dataset]:
        """Load datasets from the config inputs.

        Args:
            inputs (list): List of input datasets from config.

        Returns:
            List[Dataset]: List of Dataset objects.
        """
        datasets = []

        # Get the project root directory (where config.json is located)
        # The config.py file is in fit_detector/apps/ageing/entities/
        # So we need to go up 4 levels to get to the project root
        root_dir = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")
        )
        logger.debug(f"Project root directory: {root_dir}")

        for input_data in inputs:
            date = input_data.get("date")
            assert date, "date field missing in one of the input datasets"

            # Get the base path
            base_path = input_data.get("basePath", "")
            logger.debug(f"Original base path for dataset {date}: {base_path}")

            # If the path is relative, make it absolute relative to the root directory
            if not os.path.isabs(base_path):
                base_path = os.path.abspath(os.path.join(root_dir, base_path))
                logger.debug(f"Resolved relative path to: {base_path}")
            else:
                logger.debug(f"Path is already absolute: {base_path}")

            logger.debug(f"Final resolved base path: {base_path}")

            # Check if the path exists
            if not os.path.exists(base_path):
                logger.warning(f"basePath {base_path} does not exist. Skipping dataset {date}.")
                continue  # Skip this dataset instead of failing the entire analysis
            else:
                logger.debug(f"Path exists: {base_path}")

            files = input_data.get("files", {})
            logger.debug(f"Found {len(files)} files for dataset {date}")

            ref_ch = input_data.get("refCH", {})
            if type(ref_ch) is not dict:
                raise Exception("refCH field must be a dictionary (see README)")
            if ref_ch.get("PM") is None:
                raise Exception("refCH field missing PM key (reference PM, see README)")
            if ref_ch.get("CH") is None:
                raise Exception(
                    "refCH field missing CH key (list of reference channels, see README)"
                )
            validate_header = input_data.get("validateHeader", False)

            dataset = Dataset(date, base_path, files, ref_ch, validate_header)
            datasets.append(dataset)
            logger.debug(f"Added dataset {date} to the list")

        # Sort the datasets by date
        datasets.sort(key=lambda x: x.date)

        if not datasets:
            logger.warning("No valid datasets found in the configuration.")
        else:
            logger.debug(f"Loaded {len(datasets)} datasets: {[d.date for d in datasets]}")

        return datasets

    def to_dict(self, include_signal_data: bool = False) -> Dict:
        """Convert the Config to a dictionary.

        Returns:
            Dict: Dictionary representation of the Config.
        """
        # If we have loaded results data, return it directly
        if hasattr(self, "results_data"):
            return self.results_data

        # Otherwise, convert datasets to dictionary
        return {
            "datasets": [
                dataset.to_dict(include_signal_data)
                for dataset in sorted(self.datasets, key=lambda x: x.date)
            ]
        }

    def __str__(self):
        """String representation of the Config."""
        dataset_str = "\n  ".join(str(dataset) for dataset in self.datasets)
        return f"Config(datasets=[\n  {dataset_str}\n])"

    def __repr__(self):
        return self.__str__()
