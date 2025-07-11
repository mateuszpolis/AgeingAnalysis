"""Plotting widget for FIT detector ageing analysis visualization."""

import json
import logging
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Dict, List, Optional

import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)


class AgeingPlotWidget:
    """Widget for plotting ageing factors with interactive controls."""

    def __init__(self, parent: tk.Widget, json_file: Optional[str] = None):
        """Initialize the plotting widget.

        Args:
            parent: Parent tkinter widget.
            json_file: Optional path to JSON file containing analysis results.
        """
        self.parent = parent
        self.data = None
        self.channel_vars: Dict[str, tk.BooleanVar] = {}
        self.module_vars: Dict[str, tk.BooleanVar] = {}
        self.scatter_points: List = []

        # Create main layout
        self._create_layout()

        # Load data if JSON file is provided
        if json_file:
            self.load_from_json_file(json_file)

    def _create_layout(self):
        """Create the main layout with control and plot panels."""
        # Create a PanedWindow for resizable sections
        self.paned_window = ttk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel for controls
        self.control_frame = ttk.Frame(self.paned_window, width=300)
        self.paned_window.add(self.control_frame, weight=1)

        # Right panel for plot
        self.plot_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.plot_frame, weight=3)

        # Create control panel contents
        self._create_control_panel()

        # Create plot panel contents
        self._create_plot_panel()

        # Create status bar
        self._create_status_bar()

    def _create_control_panel(self):
        """Create the control panel with selection options."""
        # Header
        header_label = ttk.Label(
            self.control_frame,
            text="Selection Controls",
            font=("TkDefaultFont", 12, "bold"),
        )
        header_label.pack(anchor=tk.W, pady=(0, 10))

        # Factor type selection
        self._create_factor_selection()

        # Module selection
        self._create_module_selection()

        # Control buttons
        self._create_control_buttons()

    def _create_factor_selection(self):
        """Create factor type selection checkboxes."""
        factor_frame = ttk.LabelFrame(self.control_frame, text="Factor Types")
        factor_frame.pack(fill=tk.X, pady=5)

        self.gaussian_var = tk.BooleanVar(value=True)
        self.weighted_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(
            factor_frame,
            text="Gaussian Ageing Factor",
            variable=self.gaussian_var,
            command=self._update_plot,
        ).pack(anchor=tk.W, padx=10, pady=5)

        ttk.Checkbutton(
            factor_frame,
            text="Weighted Ageing Factor",
            variable=self.weighted_var,
            command=self._update_plot,
        ).pack(anchor=tk.W, padx=10, pady=5)

    def _create_module_selection(self):
        """Create scrollable module selection area."""
        self.module_frame = ttk.LabelFrame(self.control_frame, text="Modules")
        self.module_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Scrollable frame for modules
        self.canvas_scroll = tk.Canvas(self.module_frame, height=500)
        scrollbar = ttk.Scrollbar(
            self.module_frame, orient=tk.VERTICAL, command=self.canvas_scroll.yview
        )
        self.scrollable_frame = ttk.Frame(self.canvas_scroll)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas_scroll.configure(
                scrollregion=self.canvas_scroll.bbox("all")
            ),
        )

        self.canvas_scroll.create_window(
            (0, 0), window=self.scrollable_frame, anchor=tk.NW
        )
        self.canvas_scroll.configure(yscrollcommand=scrollbar.set)

        # Enable mousewheel scrolling
        self.canvas_scroll.bind(
            "<Enter>",
            lambda e: self.canvas_scroll.bind_all("<MouseWheel>", self._on_mousewheel),
        )
        self.canvas_scroll.bind(
            "<Leave>", lambda e: self.canvas_scroll.unbind_all("<MouseWheel>")
        )

        self.canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Placeholder text when no data is loaded
        self.placeholder_label = ttk.Label(
            self.scrollable_frame,
            text="No data loaded. Please load a JSON file.",
            wraplength=250,
        )
        self.placeholder_label.pack(pady=20, padx=10)

    def _create_control_buttons(self):
        """Create control buttons."""
        button_frame = ttk.Frame(self.control_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            button_frame, text="Select All", command=self._select_all_channels
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, text="Deselect All", command=self._deselect_all_channels
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, text="Clear Selection", command=self._clear_selection
        ).pack(side=tk.LEFT, padx=5)

    def _create_plot_panel(self):
        """Create the plot panel with matplotlib figure."""
        # Create matplotlib figure
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # Create canvas for matplotlib figure
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Add toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()

        # Setup hover annotation
        self._setup_hover_annotation()

        # Connect events
        self.hover_cid = self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.click_cid = self.canvas.mpl_connect("button_press_event", self._on_click)

        # Initial plot setup
        self._setup_empty_plot()

    def _create_status_bar(self):
        """Create status bar at the bottom."""
        self.status_frame = ttk.Frame(self.parent)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            self.status_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2),
        )
        self.status_label.pack(fill=tk.X)

    def _setup_hover_annotation(self):
        """Set up hover annotation for plot points."""
        self.annot = self.ax.annotate(
            "",
            xy=(0, 0),
            xytext=(20, 20),
            textcoords="offset points",
            bbox={
                "boxstyle": "round,pad=0.7",
                "fc": "yellow",
                "alpha": 0.9,
                "ec": "black",
                "lw": 1,
            },
            arrowprops={
                "arrowstyle": "->",
                "connectionstyle": "arc3,rad=.2",
                "color": "black",
            },
            fontsize=10,
            fontweight="bold",
        )
        self.annot.set_visible(False)

    def _setup_empty_plot(self):
        """Set up an empty plot with proper labels."""
        self.ax.clear()
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Ageing Factor")
        self.ax.set_ylim(0, 1.1)
        self.ax.grid(True, linestyle="--", alpha=0.7)
        self.ax.set_title("Ageing Factors Visualization")
        self.fig.tight_layout()
        self.canvas.draw()

    def load_from_json_file(self, file_path: str) -> bool:
        """Load data from a JSON file.

        Args:
            file_path: Path to the JSON file to load.

        Returns:
            True if loading was successful, False otherwise.
        """
        try:
            logger.info(f"Loading data from {file_path}")
            with open(file_path) as f:
                data = json.load(f)

            # Store the data
            self.data = data

            # Process the data structure
            self._process_loaded_data()

            # Populate the module selection panel
            self._populate_module_selection()

            self.status_var.set(
                f"Loaded data from {Path(file_path).name} - "
                "Select channels to view ageing factors"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to load JSON file: {e}")
            messagebox.showerror("Error", f"Failed to load JSON file: {str(e)}")
            self.status_var.set("Error loading file")
            return False

    def _process_loaded_data(self):
        """Process loaded data and log information."""
        if "datasets" in self.data:
            logger.info(f"Found {len(self.data['datasets'])} datasets")

            # Check if we have the expected structure
            if len(self.data["datasets"]) > 0:
                first_dataset = self.data["datasets"][0]
                logger.info(
                    f"First dataset date: {first_dataset.get('date', 'unknown')}"
                )

                if "modules" in first_dataset:
                    logger.info(
                        f"Found {len(first_dataset['modules'])} "
                        "modules in first dataset"
                    )

    def _populate_module_selection(self):
        """Populate the module selection panel with data from the loaded file."""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Clear existing variables
        self.channel_vars.clear()
        self.module_vars.clear()

        logger.info("Populating module selection...")

        # Check for valid data structure
        if not self.data or "datasets" not in self.data:
            self.placeholder_label = ttk.Label(
                self.scrollable_frame,
                text="No valid data found in the loaded file.",
                wraplength=250,
            )
            self.placeholder_label.pack(pady=20, padx=10)
            return

        # Process modules data
        modules = self._process_module_data()

        # If no modules were found after processing, show error
        if not modules:
            self.placeholder_label = ttk.Label(
                self.scrollable_frame,
                text="No modules found in the data structure.",
                wraplength=250,
            )
            self.placeholder_label.pack(pady=20, padx=10)
            return

        # Create module sections
        self._create_module_sections(modules)

    def _process_module_data(self) -> Dict[str, List[str]]:
        """Process the loaded data to extract module and channel information.

        Returns:
            Dictionary mapping module IDs to lists of channel names.
        """
        modules: Dict[str, List[str]] = {}

        # Extract from datasets
        if self.data and isinstance(self.data.get("datasets"), list):
            for dataset in self.data["datasets"]:
                for module in dataset.get("modules", []):
                    # Check both "id" and "identifier" fields
                    module_id = module.get("id", module.get("identifier", "unknown"))

                    if module_id not in modules:
                        modules[module_id] = []

                    for channel in module.get("channels", []):
                        channel_name = channel.get("name", "unknown")
                        if channel_name not in modules[module_id]:
                            modules[module_id].append(channel_name)

        # Log debug information
        if not modules:
            logger.warning("No modules found in data")
        else:
            logger.info(f"Found {len(modules)} modules with data")
            for module_id, channels in modules.items():
                logger.debug(f"Module {module_id} has {len(channels)} channels")

        return modules

    def _create_module_sections(self, modules: Dict[str, List[str]]):
        """Create module sections with channel checkboxes.

        Args:
            modules: Dictionary mapping module IDs to channel lists.
        """
        for module_id in sorted(modules.keys()):
            module_frame = ttk.LabelFrame(self.scrollable_frame, text=module_id)
            module_frame.pack(fill=tk.X, pady=5, padx=5)

            # Module checkbox
            module_var = tk.BooleanVar(value=False)
            self.module_vars[module_id] = module_var

            ttk.Checkbutton(
                module_frame,
                text="Select All",
                variable=module_var,
                command=lambda mid: self._toggle_module(mid),  # type: ignore
            ).pack(anchor=tk.W, padx=5, pady=2)

            # Channel checkboxes
            for channel in modules[module_id]:
                channel_id = f"{module_id}: {channel}"
                channel_var = tk.BooleanVar(value=False)
                self.channel_vars[channel_id] = channel_var

                ttk.Checkbutton(
                    module_frame,
                    text=channel,
                    variable=channel_var,
                    command=self._update_plot,
                ).pack(anchor=tk.W, padx=20, pady=2)

        # Update the canvas scroll region
        self.canvas_scroll.configure(scrollregion=self.canvas_scroll.bbox("all"))
        self.canvas_scroll.update_idletasks()
        self.canvas_scroll.yview_moveto(0)

    def _select_all_channels(self):
        """Select all channels."""
        for var in self.channel_vars.values():
            var.set(True)
        for var in self.module_vars.values():
            var.set(True)
        self._update_plot()

    def _deselect_all_channels(self):
        """Deselect all channels."""
        for var in self.channel_vars.values():
            var.set(False)
        for var in self.module_vars.values():
            var.set(False)
        self._update_plot()

    def _clear_selection(self):
        """Clear all selections."""
        self._deselect_all_channels()

    def _toggle_module(self, module_id: str):
        """Toggle all channels in a module.

        Args:
            module_id: ID of the module to toggle.
        """
        module_var = self.module_vars[module_id]
        is_selected = module_var.get()

        # Toggle all channels in this module
        for channel_id, channel_var in self.channel_vars.items():
            if channel_id.startswith(f"{module_id}: "):
                channel_var.set(is_selected)

        self._update_plot()

    def _get_selected_channels(self) -> List[str]:
        """Get list of selected channel IDs.

        Returns:
            List of selected channel IDs.
        """
        selected = []
        for channel_id, var in self.channel_vars.items():
            if var.get():
                selected.append(channel_id)
        return selected

    def _update_plot(self):
        """Update the plot with selected channels."""
        if not self.data:
            return

        # Get selected channels
        selected_channels = self._get_selected_channels()

        if not selected_channels:
            self._setup_empty_plot()
            return

        # Clear the plot
        self.ax.clear()
        self.scatter_points = []

        # Add channel traces
        if self._add_channel_traces(selected_channels):
            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Ageing Factor")
            self.ax.set_ylim(0, 1.1)
            self.ax.grid(True, linestyle="--", alpha=0.7)
            self.ax.set_title("Ageing Factors Visualization")
            self.ax.legend()
            self.fig.tight_layout()
        else:
            self.ax.text(
                0.5,
                0.5,
                "No data to display",
                ha="center",
                va="center",
                transform=self.ax.transAxes,
                fontsize=14,
            )

        self.canvas.draw()

    def _add_channel_traces(self, selected_channels: List[str]) -> bool:
        """Add traces for selected channels to the plot.

        Args:
            selected_channels: List of selected channel IDs.

        Returns:
            True if any traces were added, False otherwise.
        """
        added_traces = False
        show_gaussian = self.gaussian_var.get()
        show_weighted = self.weighted_var.get()

        for channel_id in selected_channels:
            module_id, channel_name = channel_id.split(":", 1)

            # Collect data points for this channel
            gaussian_dates: List[datetime] = []
            gaussian_factors: List[float] = []
            weighted_dates: List[datetime] = []
            weighted_factors: List[float] = []

            if self.data is None:
                return False
            for dataset in self.data.get("datasets", []):
                if not dataset.get("date"):
                    continue

                try:
                    date = datetime.strptime(dataset["date"], "%Y-%m-%d")
                except ValueError:
                    logger.warning(f"Invalid date format: {dataset['date']}")
                    continue

                # Find the module and channel
                module_data = None
                for m in dataset.get("modules", []):
                    if m.get("identifier", m.get("id", "")) == module_id:
                        module_data = m
                        break

                if not module_data:
                    continue

                channel_data = None
                for c in module_data.get("channels", []):
                    if c.get("name", "") == channel_name:
                        channel_data = c
                        break

                if not channel_data:
                    continue

                # Get the ageing factors
                ageing_factors = channel_data.get("ageing_factors", {})

                # Add Gaussian factor if available and selected
                if show_gaussian and "gaussian_ageing_factor" in ageing_factors:
                    gaussian_factor = ageing_factors["gaussian_ageing_factor"]
                    if gaussian_factor is not None and gaussian_factor != "N/A":
                        gaussian_dates.append(date)
                        gaussian_factors.append(gaussian_factor)

                # Add weighted factor if available and selected
                if show_weighted and "weighted_ageing_factor" in ageing_factors:
                    weighted_factor = ageing_factors["weighted_ageing_factor"]
                    if weighted_factor is not None and weighted_factor != "N/A":
                        weighted_dates.append(date)
                        weighted_factors.append(weighted_factor)

            # Add traces if we have data
            if show_gaussian and gaussian_dates and gaussian_factors:
                scatter = self.ax.scatter(
                    gaussian_dates,
                    gaussian_factors,
                    label=f"{channel_id} (Gaussian)",
                    marker="o",
                    s=20,
                    alpha=0.7,
                )
                labels = [f"{channel_id} (Gaussian)"] * len(gaussian_dates)
                self.scatter_points.append(
                    (scatter, gaussian_dates, gaussian_factors, labels)
                )
                added_traces = True

            if show_weighted and weighted_dates and weighted_factors:
                scatter = self.ax.scatter(
                    weighted_dates,
                    weighted_factors,
                    label=f"{channel_id} (Weighted)",
                    marker="s",
                    s=20,
                    alpha=0.7,
                )
                labels = [f"{channel_id} (Weighted)"] * len(weighted_dates)
                self.scatter_points.append(
                    (scatter, weighted_dates, weighted_factors, labels)
                )
                added_traces = True

        return added_traces

    def _on_hover(self, event):
        """Handle hover events to show annotations."""
        if (
            event.inaxes != self.ax
            or not hasattr(self, "scatter_points")
            or not self.scatter_points
        ):
            if self.annot.get_visible():
                self.annot.set_visible(False)
                self.canvas.draw_idle()
            return

        # Find the closest point
        closest_point = None
        min_dist = float("inf")

        for scatter, dates, values, labels in self.scatter_points:
            if not scatter.get_visible():
                continue

            for i, (x, y, label) in enumerate(zip(dates, values, labels)):
                try:
                    if isinstance(x, datetime):
                        event_date = mdates.num2date(event.xdata)
                        x_dist = abs((x - event_date).total_seconds())
                    else:
                        x_dist = abs(x - event.xdata)

                    y_dist = abs(y - event.ydata)
                    dist = (x_dist**2 + y_dist**2) ** 0.5

                    if dist < min_dist:
                        min_dist = dist
                        closest_point = (scatter, i, x, y, label)
                except (TypeError, ValueError):
                    continue

        # Show annotation if point is close enough
        if closest_point and min_dist < 0.1:
            scatter, idx, x, y, label = closest_point

            self.annot.xy = (mdates.date2num(x) if isinstance(x, datetime) else x, y)

            if isinstance(x, datetime):
                date_str = x.strftime("%Y-%m-%d")
                text = f"{label}\nDate: {date_str}\nValue: {y: .2f}"
            else:
                text = f"{label}\nX: {x: .2f}\nY: {y: .2f}"

            self.annot.set_text(text)
            self.annot.get_bbox_patch().set_alpha(0.9)
            self.annot.set_visible(True)
            self.canvas.draw_idle()
        else:
            if self.annot.get_visible():
                self.annot.set_visible(False)
                self.canvas.draw_idle()

    def _on_click(self, event):
        """Handle mouse click events on the plot."""
        self._on_hover(event)

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        self.canvas_scroll.yview_scroll(int(-1 * (event.delta / 120)), "units")
