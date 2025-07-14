"""Configuration management service for FIT detector ageing analysis."""

import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ConfigManager:
    """Service for managing configuration generation, import, export, and validation."""

    def __init__(self, root_path: Optional[str] = None):
        """Initialize the ConfigManager.

        Args:
            root_path: The root path of the project. Used for path optimization.
        """
        self.root_path = root_path
        self.inputs: List[Dict] = []

    def get_input_count(self) -> int:
        """Get the number of input groups.

        Returns:
            Number of input groups.
        """
        return len(self.inputs)

    def clear_inputs(self):
        """Clear all input groups."""
        self.inputs = []

    def add_input_group(
        self,
        folder_path: str,
        file_paths: List[str],
        reference_pm: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Add a new input group from folder and file paths.

        Args:
            folder_path: Path to the folder containing the files.
            file_paths: List of file paths to include.
            reference_pm: Reference PM identifier (optional).

        Returns:
            Tuple of (success, message).
        """
        try:
            # Validate folder path
            if not os.path.exists(folder_path):
                return False, f"Folder path does not exist: {folder_path}"

            # Extract date from the directory path
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", folder_path)
            if not date_match:
                return (
                    False,
                    "Directory path does not contain a valid date (YYYY-MM-DD format)",
                )

            date_str = date_match.group(0)

            # Validate file paths and extract PM identifiers
            files_dict = {}
            for file_path in file_paths:
                if not os.path.exists(file_path):
                    return False, f"File does not exist: {file_path}"

                if not file_path.lower().endswith(".csv"):
                    return False, f"Only CSV files are allowed: {file_path}"

                filename = os.path.basename(file_path)

                # Extract PM identifier from filename
                pm_match = re.search(r"(PM[AC][0-9])", filename)
                if not pm_match:
                    return (
                        False,
                        f"File '{filename}' does not contain a valid PM identifier",
                    )

                pm_key = pm_match.group(0)
                files_dict[pm_key] = filename

            # Validate maximum file count
            if len(files_dict) > 20:
                return False, "Maximum of 20 files are allowed per input group"

            # Determine reference channel configuration
            ref_ch = self._determine_reference_channel(files_dict, reference_pm)

            # Store absolute path for internal use
            folder_path_abs = os.path.abspath(folder_path)

            # Create input group
            input_group = {
                "date": date_str,
                "validateHeader": False,
                "basePath": folder_path_abs,
                "files": files_dict,
                "refCH": ref_ch,
            }

            self.inputs.append(input_group)
            logger.info(f"Added input group: {date_str} with {len(files_dict)} files")

            return True, f"Input group added: {date_str} with {len(files_dict)} files"

        except Exception as e:
            logger.error(f"Error adding input group: {e}")
            return False, f"Error adding input group: {str(e)}"

    def _determine_reference_channel(
        self, files_dict: Dict[str, str], reference_pm: Optional[str] = None
    ) -> Dict:
        """Determine the reference channel configuration.

        Args:
            files_dict: Dictionary of PM identifiers and filenames.
            reference_pm: Optional reference PM identifier.

        Returns:
            Reference channel configuration dictionary.
        """
        if reference_pm and reference_pm in files_dict:
            return {"PM": reference_pm, "CH": [5, 7, 8]}

        # Default logic: use PMC9 if available, otherwise use first available PM
        if "PMC9" in files_dict:
            return {"PM": "PMC9", "CH": [5, 7, 8]}
        elif len(files_dict) > 0:
            # Use the first available PM as reference
            first_pm = next(iter(files_dict.keys()))
            return {"PM": first_pm, "CH": [5, 7, 8]}

        return {}

    def _validate_loaded_config_paths(self) -> Tuple[bool, List[str]]:
        """Validate that loaded config paths actually exist.

        Returns:
            Tuple of (all_valid, invalid_paths).
        """
        invalid_paths = []

        for input_group in self.inputs:
            base_path = input_group.get("basePath", "")
            if base_path and not os.path.exists(base_path):
                invalid_paths.append(base_path)

        return len(invalid_paths) == 0, invalid_paths

    def _calculate_optimal_base_path(self, all_paths: List[str]) -> str:
        """Calculate the optimal (deepest common) base path for all dataset folders.

        Args:
            all_paths: List of absolute paths to all dataset folders.

        Returns:
            The deepest common directory path.
        """
        if not all_paths:
            return ""

        if len(all_paths) == 1:
            # For single path, use its parent directory
            return os.path.dirname(all_paths[0])

        try:
            # Find the common path among all dataset folders
            common_path = os.path.commonpath(all_paths)

            # Ensure the common path is meaningful (not root or too short)
            if common_path and common_path != os.path.sep and len(common_path) > 3:
                return common_path
            else:
                # If no meaningful common path, use the first path's parent
                return os.path.dirname(all_paths[0])

        except (ValueError, TypeError):
            # If paths are on different drives or commonpath fails
            logger.warning("Cannot find common path, using first path's parent")
            return os.path.dirname(all_paths[0])

    def optimize_base_paths(self) -> Tuple[str, List[Dict]]:
        """Optimize base paths to avoid repetition.

        This method calculates the deepest common directory of all dataset folders
        and makes all paths relative to it. It treats all inputs equally regardless
        of whether they were loaded or newly added.

        Returns:
            Tuple of (global_base_path, optimized_inputs).
        """
        if not self.inputs:
            return "", []

        # Get all absolute paths, ensuring they're all absolute
        all_paths = []
        for input_group in self.inputs:
            path = input_group["basePath"]
            if not os.path.isabs(path):
                path = os.path.abspath(path)
            all_paths.append(path)

        try:
            # Calculate the optimal base path (deepest common directory)
            global_base_path = self._calculate_optimal_base_path(all_paths)

            # Create optimized inputs with relative paths
            optimized_inputs = []
            for i, input_group in enumerate(self.inputs):
                optimized_group = input_group.copy()

                try:
                    # Make the path relative to the global base path
                    relative_path = os.path.relpath(all_paths[i], global_base_path)
                    optimized_group["basePath"] = relative_path
                except ValueError:
                    # If paths are on different drives, keep absolute path
                    logger.warning(
                        f"Cannot make path relative, keeping absolute: {all_paths[i]}"
                    )
                    optimized_group["basePath"] = all_paths[i]

                # Remove any internal tracking fields
                optimized_group.pop("_original_relative_path", None)
                optimized_inputs.append(optimized_group)

            logger.info(f"Optimized base path: {global_base_path}")
            return global_base_path, optimized_inputs

        except Exception as e:
            # If path optimization fails, return inputs with absolute paths
            logger.warning(f"Path optimization failed: {e}")
            optimized_inputs = []
            for i, input_group in enumerate(self.inputs):
                optimized_group = input_group.copy()
                optimized_group["basePath"] = all_paths[i]
                # Remove any internal tracking fields
                optimized_group.pop("_original_relative_path", None)
                optimized_inputs.append(optimized_group)

            return "", optimized_inputs

    def generate_config(self) -> Dict:
        """Generate the complete configuration dictionary.

        Returns:
            Configuration dictionary ready for JSON serialization.
        """
        global_base_path, optimized_inputs = self.optimize_base_paths()

        config = {"basePath": global_base_path, "inputs": optimized_inputs}

        return config

    def save_config(self, file_path: Optional[str] = None) -> Tuple[bool, str]:
        """Save the configuration to a JSON file.

        Args:
            file_path: Path to save the file. If None, uses default location.

        Returns:
            Tuple of (success, message_or_path).
        """
        if not self.inputs:
            return False, "No input groups to save"

        try:
            # Generate the configuration
            config = self.generate_config()

            # Determine output path
            if file_path is None:
                if self.root_path:
                    output_path = os.path.join(self.root_path, "config.json")
                else:
                    output_path = "config.json"
            else:
                output_path = file_path

            # Ensure directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:  # Only create directory if there is one
                os.makedirs(output_dir, exist_ok=True)

            # Write JSON file
            with open(output_path, "w") as f:
                json.dump(config, f, indent=4)

            logger.info(f"Configuration saved to {output_path}")
            return True, output_path

        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False, f"Error saving configuration: {str(e)}"

    def load_config(self, file_path: str) -> Tuple[bool, str]:
        """Load configuration from a JSON file.

        Args:
            file_path: Path to the configuration file.

        Returns:
            Tuple of (success, message).
        """
        try:
            if not os.path.exists(file_path):
                return False, f"Configuration file not found: {file_path}"

            with open(file_path) as f:
                config = json.load(f)

            # Validate structure
            if "inputs" not in config or not isinstance(config["inputs"], list):
                return False, "Invalid configuration structure"

            # Clear existing inputs
            self.inputs = []

            # Process each input
            global_base_path = config.get("basePath", "")
            invalid_paths = []

            for input_group in config["inputs"]:
                # Convert relative paths back to absolute
                input_base_path = input_group.get("basePath", "")
                if global_base_path and input_base_path:
                    if not os.path.isabs(input_base_path):
                        absolute_path = os.path.abspath(
                            os.path.join(global_base_path, input_base_path)
                        )
                    else:
                        absolute_path = input_base_path
                else:
                    absolute_path = input_base_path

                # Validate that the path exists
                if not os.path.exists(absolute_path):
                    invalid_paths.append(absolute_path)

                input_group["basePath"] = absolute_path
                self.inputs.append(input_group)

            # Check for invalid paths
            if invalid_paths:
                logger.warning(f"Some paths in config don't exist: {invalid_paths}")
                return (
                    False,
                    f"Invalid paths found: {', '.join(invalid_paths[:3])}"
                    f"{'...' if len(invalid_paths) > 3 else ''}",
                )

            logger.info(f"Configuration loaded from {file_path}")
            return True, f"Loaded {len(self.inputs)} input groups"

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False, f"Error loading configuration: {str(e)}"

    def validate_paths(self) -> Tuple[bool, List[str]]:
        """Validate that all paths in the configuration exist.

        Returns:
            Tuple of (all_valid, missing_paths).
        """
        return self._validate_loaded_config_paths()

    def get_inputs_summary(self) -> List[Dict]:
        """Get a summary of all input groups.

        Returns:
            List of input group summaries.
        """
        summaries = []
        for input_group in self.inputs:
            summary = {
                "date": input_group.get("date", "Unknown"),
                "path": input_group.get("basePath", ""),
                "file_count": len(input_group.get("files", {})),
                "reference_pm": input_group.get("refCH", {}).get("PM", "None"),
            }
            summaries.append(summary)
        return summaries
