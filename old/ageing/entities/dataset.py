import os
import re
from typing import Any, Dict, List

from configs.logger_config import logger
from fit_detector.apps.ageing.entities.module import Module


class Dataset:
    """Represents a single dataset with a collection of modules and reference module information."""

    def __init__(
        self,
        date: str,
        base_path: str,
        files: Dict[str, str],
        ref_ch: Dict[str, Any],
        validate_header: bool,
    ):
        """Initialize and validate the dataset.

        Args:
            date (str): Date for the dataset.
            base_path (str): Base path for the files.
            files (dict): Dictionary of PM files with their paths.
            ref_ch (dict): Reference module and channel information.
            validate_header (bool): Whether to validate headers in the files.
        """
        self.date: str = date
        self.modules: List[Module] = self._initialize_modules(
            base_path, files, ref_ch, validate_header
        )
        self._reference_module: Module = self._get_reference_module(ref_ch)
        self._reference_means: Dict[str, float] = {"gaussian_mean": 0.0, "weighted_mean": 0.0}

        logger.debug(f"Dataset {date} loaded successfully with {len(self.modules)} modules")

    def _initialize_modules(
        self,
        base_path: str,
        files: Dict[str, str],
        ref_ch: Dict[str, Any],
        validate_header: bool,
    ) -> List[Module]:
        """Load and validate modules

        Args:
            base_path (str): Base path for the files.
            files (Dict[str, str]): Dictionary of PM files with their paths.
            ref_ch (Dict[str, Any]): Reference module and channel information.
            validate_header (bool): Whether to validate headers in the files.

        Returns:
            List[Module]: List of Module objects.
        """
        modules = []
        ref_pm = ref_ch.get("PM")
        ref_channels = ref_ch.get("CH", [])

        # Define the valid naming pattern for file names (PM0A to PM9A and PM0C to PM9C)
        valid_pattern = re.compile(r"^PM[AC][0-9]$")

        for identifier, file_name in files.items():
            # Validate the file identifier against the expected pattern
            if not valid_pattern.match(identifier):
                raise ValueError(
                    f"Invalid file identifier '{identifier}'. "
                    f"Expected format is PM0A-PM9A or PM0C-PM9C."
                )

            file_path = os.path.join(base_path, file_name.strip())
            is_reference = identifier == ref_pm

            # Initialize Module with appropriate attributes
            module = Module(
                path=file_path,
                identifier=identifier,
                is_reference=is_reference,
                ref_channels=ref_channels if is_reference else None,
                validate_header=validate_header,
            )
            modules.append(module)

        return modules

    def _get_reference_module(self, ref_ch: Dict[str, Any]) -> Module:
        """Get the reference module from the list of modules.

        Args:
            ref_ch (Dict[str, Any]): Reference module and channel information.

        Raises:
            Exception: If the reference module is not found.

        Returns:
            Module: The reference module.
        """
        ref_pm = ref_ch.get("PM")
        for module in self.modules:
            if module.identifier == ref_pm:
                return module
        raise Exception(f"Reference module {ref_pm} not found in files for dataset {self.date}")

    def get_reference_module(self) -> Module:
        """Return the reference module.

        Returns:
            Module: The reference module.
        """
        return self._reference_module

    def get_reference_gaussian_mean(self) -> float:
        """Return the reference Gaussian mean.

        Returns:
            float: The reference Gaussian mean.
        """
        return self._reference_means["gaussian_mean"]

    def get_reference_weighted_mean(self) -> float:
        """Return the reference weighted mean.

        Returns:
            float: The reference weighted mean.
        """
        return self._reference_means["weighted_mean"]

    def set_reference_means(self, gaussian_mean: float, weighted_mean: float):
        """Set the reference Gaussian and weighted means.

        Args:
            gaussian_mean (float): The reference Gaussian mean.
            weighted_mean (float): The reference weighted mean.
        """
        self._reference_means.update(
            {
                "gaussian_mean": gaussian_mean,
                "weighted_mean": weighted_mean,
            }
        )

    def to_dict(self, include_signal_data: bool = False) -> Dict:
        """Convert the dataset to a dictionary.

        Args:
            include_signal_data (bool, optional): Whether to include signal data. Defaults to False.

        Returns:
            Dict: Dictionary representation of the dataset.
        """
        return {
            "date": self.date,
            "reference_means": self._reference_means,
            "modules": [module.to_dict(include_signal_data) for module in self.modules],
        }

    def __str__(self):
        """String representation of the Dataset."""
        modules_str = ", ".join(str(module) for module in self.modules)
        return (
            f"Dataset(date={self.date}, modules=[{modules_str}], "
            f"reference_module={self._reference_module})"
        )

    def __repr__(self):
        return self.__str__()
