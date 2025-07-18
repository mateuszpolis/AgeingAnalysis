"""Grid Visualization Service for Ageing Analysis."""

import csv
import importlib
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)


def normalize_pm_channel(pm: str, channel: str) -> str:
    """Normalize PM and channel names for consistent matching.

    Args:
        pm: PM identifier (e.g., 'A6', 'PMA6', 'a6')
        channel: Channel name (e.g., 'CH1', 'CH01', 'Ch01', 'ch1')

    Returns:
        Normalized PM:Channel string (e.g., 'A6:CH01')
    """
    # Normalize PM: remove 'PM' prefix if present, convert to uppercase
    pm_normalized = pm.upper()
    if pm_normalized.startswith("PM"):
        pm_normalized = pm_normalized[2:]  # Remove 'PM' prefix

    # Normalize channel: convert to uppercase and ensure consistent format
    channel_normalized = channel.upper()

    # Extract channel number and ensure it has leading zero if needed
    # Handle various formats: CH1, CH01, Ch1, ch01, etc.
    channel_match = re.search(r"CH?(\d+)", channel_normalized, re.IGNORECASE)
    if channel_match:
        channel_num = channel_match.group(1)
        # Ensure 2-digit format with leading zero if needed
        channel_num = channel_num.zfill(2)
        channel_normalized = f"CH{channel_num}"
    else:
        # If no match, just use the original in uppercase
        channel_normalized = channel_normalized

    return f"{pm_normalized}:{channel_normalized}"


class GridVisualizationService:
    """Service for handling grid visualizations of ageing analysis results."""

    def __init__(self, mappings_dir: Optional[str] = None):
        """Initialize the GridVisualizationService.

        Args:
            mappings_dir: Directory containing mapping CSV files. Package resources
                are used if not provided.
        """
        self.mappings_dir = Path(mappings_dir) if mappings_dir else None
        self.mappings_cache: Dict[str, Dict[str, Any]] = {}
        self._load_mappings()

    def _load_mappings(self):
        """Load all mapping files from the mappings directory."""
        if self.mappings_dir is not None:
            # Use file system path if provided
            if not self.mappings_dir.exists():
                logger.warning(f"Mappings directory {self.mappings_dir} does not exist")
                return

            for csv_file in self.mappings_dir.glob("*.csv"):
                try:
                    mapping_info = self._load_mapping_file_from_path(csv_file)
                    if mapping_info:
                        self.mappings_cache[csv_file.stem] = mapping_info
                        logger.info(
                            f"Loaded mapping: {csv_file.stem} with"
                            f" {len(mapping_info['mapping'])} channels"
                        )
                except Exception as e:
                    logger.error(f"Failed to load mapping file {csv_file}: {e}")
        else:
            # Use package resources
            try:
                # Use contents() for Python 3.8 compatibility
                import importlib.resources as resources

                try:
                    # Try the newer API first (Python 3.9+)
                    mappings_path = resources.files(
                        "ageing_analysis.grid_visualization_mappings"
                    )
                    csv_files = [
                        f for f in mappings_path.iterdir() if f.name.endswith(".csv")
                    ]
                    logger.debug(f"Found {len(csv_files)} CSV files using files() API")
                except AttributeError:
                    # Fallback to older API (Python 3.8)
                    csv_files = resources.contents(
                        "ageing_analysis.grid_visualization_mappings"
                    )
                    csv_files = [f for f in csv_files if f.endswith(".csv")]
                    logger.debug(
                        f"Found {len(csv_files)} CSV files using contents() API"
                    )

                if not csv_files:
                    logger.warning("No CSV files found in package resources")
                    return

                for csv_file in csv_files:
                    try:
                        mapping_info = self._load_mapping_file_from_resource(
                            csv_file.name if hasattr(csv_file, "name") else csv_file
                        )
                        if mapping_info:
                            file_stem = (
                                csv_file.stem
                                if hasattr(csv_file, "stem")
                                else csv_file.replace(".csv", "")
                            )
                            self.mappings_cache[file_stem] = mapping_info
                            logger.info(
                                f"Loaded mapping: {file_stem} with"
                                f" {len(mapping_info['mapping'])} channels"
                            )
                    except Exception as e:
                        logger.error(f"Failed to load mapping file {csv_file}: {e}")
            except Exception as e:
                logger.error(f"Failed to access package resources: {e}")
                # Add more detailed error information for debugging
                import sys

                logger.error(f"Python version: {sys.version}")
                logger.error(
                    f"importlib.resources available: {hasattr(importlib, 'resources')}"
                )

                # Fallback: try to find mappings in the package directory
                try:
                    import os

                    package_dir = os.path.dirname(__file__)
                    mappings_dir = os.path.join(
                        package_dir, "..", "grid_visualization_mappings"
                    )
                    if os.path.exists(mappings_dir):
                        logger.info(
                            f"Trying fallback mappings directory: {mappings_dir}"
                        )
                        for csv_file in os.listdir(mappings_dir):
                            if csv_file.endswith(".csv"):
                                file_path = os.path.join(mappings_dir, csv_file)
                                mapping_info = self._load_mapping_file_from_path(
                                    Path(file_path)
                                )
                                if mapping_info:
                                    file_stem = csv_file.replace(".csv", "")
                                    self.mappings_cache[file_stem] = mapping_info
                                    logger.info(
                                        f"Loaded mapping (fallback): {file_stem} with"
                                        f" {len(mapping_info['mapping'])} channels"
                                    )
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")

    def _load_mapping_file_from_path(self, file_path: Path) -> Optional[Dict]:
        """Load a single mapping file from file system path and return mapping data.

        Args:
            file_path: Path to the CSV mapping file

        Returns:
            Dictionary containing mapping data and metadata
        """
        mapping = {}
        channel_count = 0

        try:
            with open(file_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pm_channel = row.get("PM:Channel", "").strip()
                    if pm_channel:
                        try:
                            row_pos = float(row.get("row", 0))
                            col_pos = float(row.get("col", 0))

                            # Split PM:Channel and normalize
                            if ":" in pm_channel:
                                pm, channel = pm_channel.split(":", 1)
                                normalized_key = normalize_pm_channel(pm, channel)
                            else:
                                # If no colon, assume it's just a channel name
                                normalized_key = normalize_pm_channel("", pm_channel)

                            mapping[normalized_key] = (row_pos, col_pos)
                            channel_count += 1
                        except ValueError as e:
                            logger.warning(
                                f"Invalid position values in {file_path}: {e}"
                            )

            return {
                "mapping": mapping,
                "channel_count": channel_count,
                "file_path": str(file_path),
                "name": file_path.stem,
            }
        except Exception as e:
            logger.error(f"Error loading mapping file {file_path}: {e}")
            return None

    def _load_mapping_file_from_resource(self, filename: str) -> Optional[Dict]:
        """Load a single mapping file from package resources and return mapping data.

        Args:
            filename: Name of the CSV mapping file

        Returns:
            Dictionary containing mapping data and metadata
        """
        mapping = {}
        channel_count = 0

        try:
            # Use files() API for better compatibility
            import importlib.resources as resources

            try:
                # Try the newer API first (Python 3.9+)
                mappings_path = resources.files(
                    "ageing_analysis.grid_visualization_mappings"
                )
                file_path = mappings_path / filename
                with file_path.open(encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        pm_channel = row.get("PM:Channel", "").strip()
                        if pm_channel:
                            try:
                                row_pos = float(row.get("row", 0))
                                col_pos = float(row.get("col", 0))

                                # Split PM:Channel and normalize
                                if ":" in pm_channel:
                                    pm, channel = pm_channel.split(":", 1)
                                    normalized_key = normalize_pm_channel(pm, channel)
                                else:
                                    # If no colon, assume it's just a channel name
                                    normalized_key = normalize_pm_channel(
                                        "", pm_channel
                                    )

                                mapping[normalized_key] = (row_pos, col_pos)
                                channel_count += 1
                            except ValueError as e:
                                logger.warning(
                                    f"Invalid position values in {filename}: {e}"
                                )
            except AttributeError:
                # Fallback to older API (Python 3.8)
                with resources.open_text(
                    "ageing_analysis.grid_visualization_mappings", filename
                ) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        pm_channel = row.get("PM:Channel", "").strip()
                        if pm_channel:
                            try:
                                row_pos = float(row.get("row", 0))
                                col_pos = float(row.get("col", 0))

                                # Split PM:Channel and normalize
                                if ":" in pm_channel:
                                    pm, channel = pm_channel.split(":", 1)
                                    normalized_key = normalize_pm_channel(pm, channel)
                                else:
                                    # If no colon, assume it's just a channel name
                                    normalized_key = normalize_pm_channel(
                                        "", pm_channel
                                    )

                                mapping[normalized_key] = (row_pos, col_pos)
                                channel_count += 1
                            except ValueError as e:
                                logger.warning(
                                    f"Invalid position values in {filename}: {e}"
                                )

            return {
                "mapping": mapping,
                "channel_count": channel_count,
                "file_path": (
                    f"package://ageing_analysis.grid_visualization_mappings/"
                    f"{filename}"
                ),
                "name": Path(filename).stem,
            }
        except Exception as e:
            logger.error(f"Error loading mapping file {filename} from resources: {e}")
            return None

    def get_available_mappings(self) -> List[Dict]:
        """Get list of available mappings with metadata.

        Returns:
            List of dictionaries containing mapping information
        """
        mappings = []
        for name, info in self.mappings_cache.items():
            mappings.append(
                {
                    "name": name,
                    "channel_count": info["channel_count"],
                    "file_path": info["file_path"],
                }
            )
        return sorted(mappings, key=lambda x: x["name"])

    def get_mapping(self, mapping_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific mapping by name.

        Args:
            mapping_name: Name of the mapping to retrieve

        Returns:
            Mapping dictionary or None if not found
        """
        return self.mappings_cache.get(mapping_name)

    def create_grid_visualization(
        self,
        mapping_name: str,
        results_data: Dict,
        colormap: str = "RdYlGn",
        vmin: float = 0.5,
        vmax: float = 1.5,
        ageing_factor_type: str = "normalized_gauss_ageing_factor",
        selected_date: Optional[str] = None,
    ) -> Optional[Figure]:
        """Create a grid visualization using the specified mapping and results data.

        Args:
            mapping_name: Name of the mapping to use
            results_data: Analysis results data
            colormap: Matplotlib colormap name
            vmin: Minimum value for color scaling
            vmax: Maximum value for color scaling
            ageing_factor_type: Type of ageing factor to display

        Returns:
            Matplotlib Figure with the grid visualization or None if failed
        """
        mapping_info = self.get_mapping(mapping_name)
        if not mapping_info:
            logger.error(f"Mapping '{mapping_name}' not found")
            return None

        try:
            # Extract ageing factors from results data
            ageing_factors = self._extract_ageing_factors(
                results_data, selected_date, ageing_factor_type
            )

            # Create the visualization
            fig = self._create_grid_figure(
                mapping_info["mapping"],
                ageing_factors,
                colormap,
                vmin,
                vmax,
                mapping_name,
                ageing_factor_type,
                selected_date,
                results_data,
            )

            return fig
        except Exception as e:
            logger.error(f"Failed to create grid visualization: {e}")
            return None

    def get_available_dates(self, results_data: Dict) -> List[str]:
        """Get list of available dates from the results data.

        Args:
            results_data: Analysis results data

        Returns:
            List of date strings
        """
        dates = []
        for dataset in results_data.get("datasets", []):
            date = dataset.get("date")
            if date:
                dates.append(date)
        return sorted(dates)

    def _extract_ageing_factors(
        self,
        results_data: Dict,
        selected_date: Optional[str] = None,
        ageing_factor_type: str = "normalized_gauss_ageing_factor",
    ) -> Dict[str, float]:
        """Extract ageing factors from results.

        Args:
            results_data: Analysis results data
            selected_date: Date to extract factors from. If None, uses last dataset.
            ageing_factor_type: Type of ageing factor to extract

        Returns:
            Dictionary mapping PM:Channel to ageing factor
        """
        factors: Dict[str, float] = {}

        # Find the dataset for the selected date
        target_dataset = None
        for dataset in results_data.get("datasets", []):
            if selected_date is None or dataset.get("date") == selected_date:
                target_dataset = dataset
                break

        if not target_dataset:
            logger.warning(f"No dataset found for date: {selected_date}")
            return factors

        # Extract ageing factors from the target dataset
        for module in target_dataset.get("modules", []):
            module_id = module.get("identifier", module.get("id", "unknown"))

            for channel in module.get("channels", []):
                channel_name = channel.get("name", "unknown")

                # Normalize the PM:Channel key for consistent matching
                normalized_key = normalize_pm_channel(module_id, channel_name)

                # Extract the ageing factor
                ageing_factors = channel.get("ageing_factors", {})
                if isinstance(ageing_factors, dict):
                    factor = ageing_factors.get(ageing_factor_type)
                    if factor is not None and not isinstance(factor, str):
                        try:
                            factors[normalized_key] = float(factor)
                        except (ValueError, TypeError):
                            logger.warning(
                                f"Invalid ageing factor for {normalized_key}: {factor}"
                            )
                            factors[normalized_key] = 1.0  # Default value
                    else:
                        logger.debug(f"No valid ageing factor for {normalized_key}")
                        factors[normalized_key] = 1.0  # Default value

        logger.info(
            f"Extracted {len(factors)} {ageing_factor_type} factors for date:"
            f" {target_dataset.get('date')}"
        )
        return factors

    def _create_grid_figure(
        self,
        mapping: Dict[str, Tuple[float, float]],
        ageing_factors: Dict[str, float],
        colormap: str,
        vmin: float,
        vmax: float,
        mapping_name: str,
        ageing_factor_type: str = "normalized_gauss_ageing_factor",
        selected_date: Optional[str] = None,
        results_data: Optional[Dict] = None,
    ) -> Figure:
        """Create the actual grid visualization figure.

        Args:
            mapping: Dictionary mapping PM:Channel to (row, col) positions
            ageing_factors: Dictionary mapping PM:Channel to ageing factor values
            colormap: Matplotlib colormap name
            vmin: Minimum value for color scaling
            vmax: Maximum value for color scaling
            mapping_name: Name of the mapping for display
            ageing_factor_type: Type of ageing factor being displayed
            selected_date: Selected date for the visualization
            results_data: Analysis results data for reference date extraction

        Returns:
            Matplotlib Figure with the grid visualization
        """
        fig = Figure(figsize=(12, 10), dpi=100)
        ax = fig.add_subplot(111)

        # Create the grid visualization using rectangles
        cmap = plt.get_cmap(colormap)

        # Collect data points
        x_positions = []
        y_positions = []
        values = []
        labels = []

        for pm_channel, (row, col) in mapping.items():
            value = ageing_factors.get(pm_channel, 1.0)  # Default to 1.0 if no data

            x_positions.append(col)
            y_positions.append(row)
            values.append(value)
            labels.append(pm_channel)

        if not values:
            ax.text(
                0.5,
                0.5,
                "No data available",
                ha="center",
                va="center",
                transform=ax.transAxes,
                fontsize=12,
            )
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_frame_on(False)
            return fig

        # Create squares for each position
        for x, y, value in zip(x_positions, y_positions, values):
            rect = plt.Rectangle(
                (x - 0.5, y - 0.5),
                1,
                1,
                facecolor=cmap((value - vmin) / (vmax - vmin)),
                edgecolor="black",
                linewidth=1,
            )
            ax.add_patch(rect)

        # Add values inside each square
        for x, y, value in zip(x_positions, y_positions, values):
            text = f"{value:.2f}"
            value_normalized = (value - vmin) / (vmax - vmin)
            text_color = "black" if 0.3 < value_normalized < 0.7 else "white"
            ax.text(x, y, text, ha="center", va="center", color=text_color, fontsize=8)

        # Get reference date (first dataset is typically the reference)
        reference_date = None
        if results_data and results_data.get("datasets"):
            reference_date = results_data["datasets"][0].get("date")

        # Set title with date comparison
        factor_display_names = {
            "normalized_gauss_ageing_factor": "Normalized Gaussian",
            "normalized_weighted_ageing_factor": "Normalized Weighted",
            "gaussian_ageing_factor": "Gaussian",
            "weighted_ageing_factor": "Weighted",
        }
        display_name = factor_display_names.get(ageing_factor_type, ageing_factor_type)

        # Main title with date comparison
        if selected_date and reference_date and reference_date != selected_date:
            title = (
                f"{display_name} Ageing Factors - {mapping_name}\n"
                f"{selected_date} vs {reference_date}"
            )
        elif selected_date:
            title = (
                f"{display_name} Ageing Factors - {mapping_name}\n" f"{selected_date}"
            )
        else:
            title = f"{display_name} Ageing Factors - {mapping_name}"

        ax.set_title(title, fontsize=14, fontweight="bold")

        # Set axis limits with padding
        if x_positions and y_positions:
            x_min, x_max = min(x_positions), max(x_positions)
            y_min, y_max = min(y_positions), max(y_positions)
            padding = 0.5
            ax.set_xlim(x_min - padding, x_max + padding)
            ax.set_ylim(y_min - padding, y_max + padding)

        # Remove axis ticks and labels
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_frame_on(False)

        # Add colorbar
        cbar = fig.colorbar(
            plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax)),
            ax=ax,
        )
        cbar.set_label(f"{display_name} Ageing Factor")

        # Invert y-axis to match original grid layout
        ax.invert_yaxis()
        ax.set_aspect("equal")

        # Adjust layout
        fig.tight_layout()

        return fig

    def refresh_mappings(self):
        """Refresh the mappings cache by reloading all mapping files."""
        self.mappings_cache.clear()
        self._load_mappings()
