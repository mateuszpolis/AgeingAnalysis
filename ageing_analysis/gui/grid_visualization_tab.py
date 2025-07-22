"""Grid Visualizations Tab for Ageing Analysis Visualization."""

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict

from ..services.grid_visualization_service import GridVisualizationService

logger = logging.getLogger(__name__)


class GridVisualizationTab:
    """Grid Visualization Tab for Ageing Analysis Visualization."""

    def __init__(self, parent: tk.Widget, status_var: tk.StringVar):
        """Initialize the GridVisualizationTab.

        Args:
            parent: The parent tkinter widget that this tab belongs to
            status_var: The tkinter StringVar to display status messages
        """
        self.parent = parent
        self.status_var = status_var
        self.results_data: Dict[str, Any] | None = None
        self.grid_service = GridVisualizationService()

        # GUI components
        self.frame = ttk.Frame(self.parent)
        self.mapping_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.ageing_factor_var = tk.StringVar(value="normalized_gauss_ageing_factor")
        self.colormap_var = tk.StringVar(value="custom")
        self.vmin_var = tk.DoubleVar(value=0.4)
        self.vmax_var = tk.DoubleVar(value=1.2)

        # Custom color palette
        self.custom_colormap_colors = [
            "#000000",
            "#623200",
            "#944A00",
            "#C66300",
            "#F77B02",
            "#FF9B19",
            "#FFC642",
            "#FFEE6B",
            "#EEF773",
            "#C5DE62",
            "#9BC64A",
            "#73AD39",
            "#4A8C22",
            "#207311",
            "#016300",
        ]

        # Plot components
        self.fig = None
        self.canvas = None

        self._create_widgets()
        self._populate_mapping_dropdown()
        self._populate_date_dropdown()
        self._populate_ageing_factor_dropdown()

    def _create_widgets(self):
        """Create the GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Control panel
        control_frame = ttk.LabelFrame(
            main_frame, text="Grid Visualization Controls", padding=10
        )
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # Mapping and date selection
        selection_frame = ttk.Frame(control_frame)
        selection_frame.pack(fill=tk.X, pady=(0, 10))

        # Mapping selection
        mapping_frame = ttk.Frame(selection_frame)
        mapping_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(mapping_frame, text="Mapping:").pack(side=tk.LEFT, padx=(0, 5))
        self.mapping_combobox = ttk.Combobox(
            mapping_frame, textvariable=self.mapping_var, state="readonly", width=30
        )
        self.mapping_combobox.pack(side=tk.LEFT, padx=(0, 10))
        self.mapping_combobox.bind("<<ComboboxSelected>>", self._on_mapping_selected)

        # Mapping info
        self.mapping_info_label = ttk.Label(mapping_frame, text="")
        self.mapping_info_label.pack(side=tk.LEFT, padx=(10, 0))

        # Date selection
        date_frame = ttk.Frame(selection_frame)
        date_frame.pack(fill=tk.X)

        ttk.Label(date_frame, text="Date:").pack(side=tk.LEFT, padx=(0, 5))
        self.date_combobox = ttk.Combobox(
            date_frame, textvariable=self.date_var, state="readonly", width=30
        )
        self.date_combobox.pack(side=tk.LEFT, padx=(0, 10))
        self.date_combobox.bind("<<ComboboxSelected>>", self._on_date_selected)

        # Date info
        self.date_info_label = ttk.Label(date_frame, text="")
        self.date_info_label.pack(side=tk.LEFT, padx=(10, 0))

        # Ageing factor selection
        ageing_factor_frame = ttk.Frame(selection_frame)
        ageing_factor_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(ageing_factor_frame, text="Ageing Factor:").pack(
            side=tk.LEFT, padx=(0, 5)
        )
        self.ageing_factor_combobox = ttk.Combobox(
            ageing_factor_frame,
            textvariable=self.ageing_factor_var,
            state="readonly",
            width=30,
        )
        self.ageing_factor_combobox.pack(side=tk.LEFT, padx=(0, 10))
        self.ageing_factor_combobox.bind(
            "<<ComboboxSelected>>", self._on_ageing_factor_selected
        )

        # Ageing factor info
        self.ageing_factor_info_label = ttk.Label(ageing_factor_frame, text="")
        self.ageing_factor_info_label.pack(side=tk.LEFT, padx=(10, 0))

        # Visualization options
        options_frame = ttk.Frame(control_frame)
        options_frame.pack(fill=tk.X, pady=(0, 10))

        # Colormap selection
        colormap_frame = ttk.Frame(options_frame)
        colormap_frame.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(colormap_frame, text="Colormap:").pack(side=tk.LEFT, padx=(0, 5))
        colormap_combobox = ttk.Combobox(
            colormap_frame,
            textvariable=self.colormap_var,
            values=["custom", "RdYlGn", "viridis", "plasma", "coolwarm", "seismic"],
            state="readonly",
            width=15,
        )
        colormap_combobox.pack(side=tk.LEFT)
        colormap_combobox.bind("<<ComboboxSelected>>", self._on_visualization_changed)

        # Value range
        range_frame = ttk.Frame(options_frame)
        range_frame.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(range_frame, text="Min:").pack(side=tk.LEFT, padx=(0, 5))
        vmin_spinbox = ttk.Spinbox(
            range_frame,
            from_=0.0,
            to=2.0,
            increment=0.1,
            textvariable=self.vmin_var,
            width=8,
        )
        vmin_spinbox.pack(side=tk.LEFT, padx=(0, 10))
        vmin_spinbox.bind("<KeyRelease>", self._on_visualization_changed)
        vmin_spinbox.bind("<<Increment>>", self._on_visualization_changed)
        vmin_spinbox.bind("<<Decrement>>", self._on_visualization_changed)

        ttk.Label(range_frame, text="Max:").pack(side=tk.LEFT, padx=(0, 5))
        vmax_spinbox = ttk.Spinbox(
            range_frame,
            from_=0.0,
            to=2.0,
            increment=0.1,
            textvariable=self.vmax_var,
            width=8,
        )
        vmax_spinbox.pack(side=tk.LEFT)
        vmax_spinbox.bind("<KeyRelease>", self._on_visualization_changed)
        vmax_spinbox.bind("<<Increment>>", self._on_visualization_changed)
        vmax_spinbox.bind("<<Decrement>>", self._on_visualization_changed)

        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)

        refresh_button = ttk.Button(
            button_frame, text="Refresh Mappings", command=self._refresh_mappings
        )
        refresh_button.pack(side=tk.LEFT, padx=(0, 10))

        update_button = ttk.Button(
            button_frame,
            text="Update Visualization",
            command=self._update_visualization,
        )
        update_button.pack(side=tk.LEFT, padx=(0, 10))

        save_button = ttk.Button(
            button_frame, text="Save Plot", command=self._save_plot
        )
        save_button.pack(side=tk.LEFT)

        # Plot area
        plot_frame = ttk.LabelFrame(main_frame, text="Grid Visualization", padding=10)
        plot_frame.pack(fill=tk.BOTH, expand=True)

        # Create matplotlib canvas
        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure

            self.fig = Figure(figsize=(10, 8), dpi=100)
            self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # Show placeholder
            self._show_placeholder()

        except ImportError as e:
            logger.error(f"Matplotlib not available: {e}")
            error_label = ttk.Label(
                plot_frame,
                text="Matplotlib is required for grid visualization",
                foreground="red",
            )
            error_label.pack(expand=True)

    def _populate_mapping_dropdown(self):
        """Populate the mapping dropdown with available mappings."""
        try:
            mappings = self.grid_service.get_available_mappings()
            if mappings:
                mapping_names = [mapping["name"] for mapping in mappings]
                self.mapping_combobox["values"] = mapping_names
                if mapping_names:
                    self.mapping_combobox.set(mapping_names[0])
                    self._update_mapping_info()
            else:
                self.mapping_combobox["values"] = ["No mappings available"]
                self.mapping_combobox.set("No mappings available")
        except Exception as e:
            logger.error(f"Failed to populate mapping dropdown: {e}")
            self.mapping_combobox["values"] = ["Error loading mappings"]
            self.mapping_combobox.set("Error loading mappings")

    def _populate_date_dropdown(self):
        """Populate the date dropdown with available dates from results data."""
        if not self.results_data:
            self.date_combobox["values"] = ["No data available"]
            self.date_combobox.set("No data available")
            return

        try:
            dates = self.grid_service.get_available_dates(self.results_data)
            if dates:
                self.date_combobox["values"] = dates
                self.date_combobox.set(dates[0])
                self._update_date_info()
            else:
                self.date_combobox["values"] = ["No dates available"]
                self.date_combobox.set("No dates available")
        except Exception as e:
            logger.error(f"Failed to populate date dropdown: {e}")
            self.date_combobox["values"] = ["Error loading dates"]
            self.date_combobox.set("Error loading dates")

    def _populate_ageing_factor_dropdown(self):
        """Populate the ageing factor dropdown with available options."""
        ageing_factors = [
            ("normalized_gauss_ageing_factor", "Normalized Gaussian"),
            ("normalized_weighted_ageing_factor", "Normalized Weighted"),
            ("gaussian_ageing_factor", "Gaussian"),
            ("weighted_ageing_factor", "Weighted"),
        ]

        self.ageing_factor_combobox["values"] = [
            display_name for _, display_name in ageing_factors
        ]
        self.ageing_factor_combobox.set("Normalized Gaussian")  # Default
        self._update_ageing_factor_info()

    def _update_ageing_factor_info(self):
        """Update the ageing factor information display."""
        selected_factor = self.ageing_factor_var.get()
        if selected_factor:
            # Get display name for the selected factor
            factor_display_names = {
                "normalized_gauss_ageing_factor": "Normalized Gaussian",
                "normalized_weighted_ageing_factor": "Normalized Weighted",
                "gaussian_ageing_factor": "Gaussian",
                "weighted_ageing_factor": "Weighted",
            }
            display_name = factor_display_names.get(selected_factor, selected_factor)
            self.ageing_factor_info_label.config(text=f"Type: {display_name}")
        else:
            self.ageing_factor_info_label.config(text="")

    def _update_mapping_info(self):
        """Update the mapping information display."""
        selected_mapping = self.mapping_var.get()
        if selected_mapping and selected_mapping != "No mappings available":
            try:
                mapping_info = self.grid_service.get_mapping(selected_mapping)
                if mapping_info:
                    info_text = f"Channels: {mapping_info['channel_count']}"
                    self.mapping_info_label.config(text=info_text)
                else:
                    self.mapping_info_label.config(text="")
            except Exception as e:
                logger.error(f"Failed to update mapping info: {e}")
                self.mapping_info_label.config(text="")
        else:
            self.mapping_info_label.config(text="")

    def _update_date_info(self):
        """Update the date information display."""
        selected_date = self.date_var.get()
        if selected_date and selected_date not in [
            "No data available",
            "No dates available",
            "Error loading dates",
        ]:
            try:
                # Count channels for this date
                channel_count = 0
                for dataset in self.results_data.get("datasets", []):
                    if dataset.get("date") == selected_date:
                        for module in dataset.get("modules", []):
                            channel_count += len(module.get("channels", []))
                        break
                info_text = f"Channels: {channel_count}"
                self.date_info_label.config(text=info_text)
            except Exception as e:
                logger.error(f"Failed to update date info: {e}")
                self.date_info_label.config(text="")
        else:
            self.date_info_label.config(text="")

    def _on_mapping_selected(self, event=None):
        """Handle mapping selection change."""
        self._update_mapping_info()
        if self.results_data:
            self._update_visualization()

    def _on_date_selected(self, event=None):
        """Handle date selection change."""
        self._update_date_info()
        if self.results_data:
            self._update_visualization()

    def _on_ageing_factor_selected(self, event=None):
        """Handle ageing factor selection change."""
        # Map display name back to internal name
        display_name = self.ageing_factor_combobox.get()
        factor_mapping = {
            "Normalized Gaussian": "normalized_gauss_ageing_factor",
            "Normalized Weighted": "normalized_weighted_ageing_factor",
            "Gaussian": "gaussian_ageing_factor",
            "Weighted": "weighted_ageing_factor",
        }
        self.ageing_factor_var.set(
            factor_mapping.get(display_name, "normalized_gauss_ageing_factor")
        )
        self._update_ageing_factor_info()
        if self.results_data:
            self._update_visualization()

    def _on_visualization_changed(self, event=None):
        """Handle visualization parameter changes."""
        if (
            self.results_data
            and self.mapping_var.get()
            and self.mapping_var.get() != "No mappings available"
            and self.date_var.get()
            and self.date_var.get()
            not in ["No data available", "No dates available", "Error loading dates"]
        ):
            self._update_visualization()

    def _refresh_mappings(self):
        """Refresh the mappings from the directory."""
        try:
            self.grid_service.refresh_mappings()
            self._populate_mapping_dropdown()
            self.status_var.set("Mappings refreshed successfully")
        except Exception as e:
            error_msg = f"Failed to refresh mappings: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
            self.status_var.set("Failed to refresh mappings")

    def _save_plot(self):
        """Save the current grid visualization plot."""
        if not self.fig or not self.canvas:
            messagebox.showwarning("Warning", "No plot available to save")
            return

        try:
            from pathlib import Path
            from tkinter import filedialog

            # Get current mapping and date for filename suggestion
            mapping_name = self.mapping_var.get()
            date_str = self.date_var.get()

            # Create default filename
            if (
                mapping_name
                and date_str
                and mapping_name != "No mappings available"
                and date_str
                not in [
                    "No data available",
                    "No dates available",
                    "Error loading dates",
                ]
            ):
                # Clean up date string for filename
                clean_date = date_str.replace("-", "")
                default_filename = f"grid_visualization_{mapping_name}_{clean_date}.png"
            else:
                default_filename = "grid_visualization.png"

            # Ask user for save location
            file_path = filedialog.asksaveasfilename(
                title="Save Grid Visualization",
                defaultextension=".png",
                initialfile=default_filename,
                filetypes=[
                    ("PNG files", "*.png"),
                    ("PDF files", "*.pdf"),
                    ("SVG files", "*.svg"),
                    ("JPEG files", "*.jpg"),
                    ("All files", "*.*"),
                ],
                parent=self.frame,
            )

            if file_path:
                # Save the plot
                self.fig.savefig(
                    file_path,
                    dpi=300,
                    bbox_inches="tight",
                    facecolor="white",
                    edgecolor="none",
                )

                # Update status
                filename = Path(file_path).name
                self.status_var.set(f"Grid visualization saved as {filename}")

                # Show success message
                messagebox.showinfo(
                    "Success",
                    f"Grid visualization saved successfully!\n\nFile:"
                    f" {filename}\nLocation: {Path(file_path).parent}",
                    parent=self.frame,
                )

        except Exception as e:
            error_msg = f"Failed to save plot: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg, parent=self.frame)
            self.status_var.set("Failed to save plot")

    def _update_visualization(self):
        """Update the grid visualization."""
        if not self.results_data:
            self.status_var.set("No results data available")
            return

        selected_mapping = self.mapping_var.get()
        if not selected_mapping or selected_mapping == "No mappings available":
            self.status_var.set("No mapping selected")
            return

        try:
            # Get the mapping and ageing factors
            mapping_info = self.grid_service.get_mapping(selected_mapping)
            if not mapping_info:
                self.status_var.set("Mapping not found")
                return

            selected_date = self.date_var.get()
            if not selected_date or selected_date in [
                "No data available",
                "No dates available",
                "Error loading dates",
            ]:
                self.status_var.set("No date selected")
                return

            ageing_factors = self.grid_service._extract_ageing_factors(
                self.results_data, selected_date, self.ageing_factor_var.get()
            )

            # Clear the current figure
            self.fig.clear()
            ax = self.fig.add_subplot(111)

            # Create the grid visualization
            self._create_grid_plot(
                ax,
                mapping_info["mapping"],
                ageing_factors,
                self.colormap_var.get(),
                self.vmin_var.get(),
                self.vmax_var.get(),
                selected_mapping,
                selected_date,
                self.ageing_factor_var.get(),
            )

            # Update the canvas
            self.canvas.draw()
            self.status_var.set(f"Grid visualization updated for {selected_mapping}")

        except Exception as e:
            error_msg = f"Failed to update visualization: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
            self.status_var.set("Failed to update visualization")

    def _show_placeholder(self):
        """Show a placeholder when no visualization is available."""
        if self.fig:
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            ax.text(
                0.5,
                0.5,
                "Select a mapping and load results data\nto view grid visualization",
                ha="center",
                va="center",
                transform=ax.transAxes,
                fontsize=12,
            )
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_frame_on(False)
            self.canvas.draw()

    def _create_grid_plot(
        self,
        ax,
        mapping,
        ageing_factors,
        colormap,
        vmin,
        vmax,
        mapping_name,
        selected_date,
        ageing_factor_type,
    ):
        """Create the grid plot on the given axes.

        Args:
            ax: Matplotlib axes to plot on
            mapping: Dictionary mapping PM:Channel to (row, col) positions
            ageing_factors: Dictionary mapping PM:Channel to ageing factor values
            colormap: Matplotlib colormap name
            vmin: Minimum value for color scaling
            vmax: Maximum value for color scaling
            mapping_name: Name of the mapping for display
            selected_date: Selected date for the visualization
            ageing_factor_type: Type of ageing factor being displayed
        """
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap

        # Create the grid visualization using rectangles
        if colormap == "custom":
            # Create custom colormap from the color list
            cmap = ListedColormap(self.custom_colormap_colors)
        else:
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

        if not values:  # No data to plot
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
            return

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
        if self.results_data and self.results_data.get("datasets"):
            reference_date = self.results_data["datasets"][0].get("date")

        # Set title with date comparison
        factor_display_names = {
            "normalized_gauss_ageing_factor": "Normalized Gaussian",
            "normalized_weighted_ageing_factor": "Normalized Weighted",
            "gaussian_ageing_factor": "Gaussian",
            "weighted_ageing_factor": "Weighted",
        }
        display_name = factor_display_names.get(ageing_factor_type, ageing_factor_type)

        # Main title with date comparison
        if reference_date and reference_date != selected_date:
            title = (
                f"{display_name} Ageing Factors - {mapping_name}\n"
                f"{selected_date} vs {reference_date}"
            )
        else:
            title = (
                f"{display_name} Ageing Factors - {mapping_name}\n" f"{selected_date}"
            )

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
        if colormap == "custom":
            # Create custom colormap for the colorbar
            cbar_cmap = ListedColormap(self.custom_colormap_colors)
        else:
            cbar_cmap = cmap

        cbar = self.fig.colorbar(
            plt.cm.ScalarMappable(
                cmap=cbar_cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax)
            ),
            ax=ax,
        )
        cbar.set_label(f"{display_name} Ageing Factor")

        # Invert y-axis to match original grid layout
        ax.invert_yaxis()
        ax.set_aspect("equal")

        # Adjust layout
        self.fig.tight_layout()

    def update_results_data(self, results_data: Dict[str, Any]):
        """Update the results data and refresh visualization if possible."""
        self.results_data = results_data
        self._populate_date_dropdown()
        if (
            self.mapping_var.get()
            and self.mapping_var.get() != "No mappings available"
            and self.date_var.get()
            and self.date_var.get()
            not in ["No data available", "No dates available", "Error loading dates"]
        ):
            self._update_visualization()
        else:
            self._show_placeholder()
