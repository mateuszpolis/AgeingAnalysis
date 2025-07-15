"""Dataset entity for FIT detector ageing analysis."""

import logging
import os
from typing import Any, Dict, List, Optional

from ageing_analysis.utils.normalization import normalize_pm_name

from ..utils.validation import validate_file_identifier
from .module import Module

logger = logging.getLogger(__name__)


class Dataset:
    """Represents a single dataset with a collection of modules."""

    def __init__(
        self,
        date: str,
        base_path: str,
        files: Dict[str, str],
        ref_ch: Dict[str, Any],
        validate_header: bool,
        integrated_charge_data: Optional[Dict[str, Dict[str, float]]] = None,
    ):
        """Initialize and validate the dataset.

        Args:
            date: Date for the dataset.
            base_path: Base path for the files.
            files: Dictionary of PM files with their paths.
            ref_ch: Reference module and channel information.
            validate_header: Whether to validate headers in the files.
            integrated_charge_data: Integrated charge data for the dataset.
        """
        self.date: str = date
        self.modules: List[Module] = self._initialize_modules(
            base_path, files, ref_ch, validate_header, integrated_charge_data
        )
        self._reference_module: Module = self._get_reference_module(ref_ch)
        self._reference_means: Dict[str, float] = {
            "gaussian_mean": 0.0,
            "weighted_mean": 0.0,
        }

        logger.debug(
            f"Dataset {date} loaded successfully with {len(self.modules)} modules"
        )

    def _initialize_modules(
        self,
        base_path: str,
        files: Dict[str, str],
        ref_ch: Dict[str, Any],
        validate_header: bool,
        integrated_charge_data: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> List[Module]:
        """Load and validate modules.

        Args:
            base_path: Base path for the files.
            files: Dictionary of PM files with their paths.
            ref_ch: Reference module and channel information.
            validate_header: Whether to validate headers in files.
            integrated_charge_data: Integrated charge data for the dataset.

        Returns:
            List of Module objects.
        """
        modules = []
        ref_pm = ref_ch.get("PM")
        ref_channels = ref_ch.get("CH", [])

        for identifier, file_name in files.items():
            # Validate the file identifier against the expected pattern
            if not validate_file_identifier(identifier):
                raise ValueError(
                    f"Invalid file identifier '{identifier}'. "
                    f"Expected format is PMA0-PMA9 or PMC0-PMC9."
                )

            file_path = os.path.join(base_path, file_name.strip())
            is_reference = identifier == ref_pm

            module_integrated_charge_data = None
            # Get integrated charge data for this module if available
            print("Integrated charge data: ", integrated_charge_data)
            if integrated_charge_data:
                # Normalize the module identifier to match config keys
                normalized_identifier = normalize_pm_name(identifier)

                # Look for the normalized identifier in the integrated charge data
                for config_pm_name, pm_charge_data in integrated_charge_data.items():
                    normalized_config_pm = normalize_pm_name(config_pm_name)
                    if normalized_config_pm == normalized_identifier:
                        module_integrated_charge_data = {identifier: pm_charge_data}
                        logger.debug(
                            f"Found integrated charge data for module {identifier} "
                            f"(config: {config_pm_name})"
                        )
                        break

            # Initialize Module with appropriate attributes
            module = Module(
                path=file_path,
                identifier=identifier,
                is_reference=is_reference,
                ref_channels=ref_channels if is_reference else None,
                validate_header=validate_header,
                integrated_charge_data=module_integrated_charge_data,
            )
            modules.append(module)

        return modules

    def _get_reference_module(self, ref_ch: Dict[str, Any]) -> Module:
        """Get the reference module from the list of modules.

        Args:
            ref_ch: Reference module and channel information.

        Raises:
            Exception: If the reference module is not found.

        Returns:
            The reference module.
        """
        ref_pm = ref_ch.get("PM")
        for module in self.modules:
            if module.identifier == ref_pm:
                return module
        raise Exception(
            f"Reference module {ref_pm} not in files for dataset {self.date}"
        )

    def get_reference_module(self) -> Module:
        """Return the reference module.

        Returns:
            The reference module.
        """
        return self._reference_module

    def get_reference_gaussian_mean(self) -> float:
        """Return the reference Gaussian mean.

        Returns:
            The reference Gaussian mean.
        """
        return self._reference_means["gaussian_mean"]

    def get_reference_weighted_mean(self) -> float:
        """Return the reference weighted mean.

        Returns:
            The reference weighted mean.
        """
        return self._reference_means["weighted_mean"]

    def set_reference_means(self, gaussian_mean: float, weighted_mean: float):
        """Set the reference Gaussian and weighted means.

        Args:
            gaussian_mean: The reference Gaussian mean.
            weighted_mean: The reference weighted mean.
        """
        self._reference_means.update(
            {
                "gaussian_mean": gaussian_mean,
                "weighted_mean": weighted_mean,
            }
        )

    def to_dict(
        self, include_signal_data: bool = False, include_total_signal_data: bool = True
    ) -> Dict:
        """Convert the dataset to a dictionary.

        Args:
            include_signal_data: Whether to include signal data.
            include_total_signal_data: Whether to include total signal data.

        Returns:
            Dictionary representation of the dataset.
        """
        return {
            "date": self.date,
            "reference_means": self._reference_means,
            "modules": [
                module.to_dict(include_signal_data, include_total_signal_data)
                for module in self.modules
            ],
        }

    def __str__(self):
        """Return string representation of the Dataset."""
        modules_str = ", ".join(str(module) for module in self.modules)
        return (
            f"Dataset(date={self.date}, modules=[{modules_str}], "
            f"reference_module={self._reference_module})"
        )

    def __repr__(self):
        """Return string representation of the Dataset."""
        return self.__str__()
