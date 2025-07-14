"""Ageing Visualization Window for FIT detector ageing analysis."""

import json
import logging
import re
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)


def _natural_sort_key(text):
    """Generate a key for natural sorting of channel names like CH1, CH2, ..., CH12."""
    # Extract number from channel name (e.g., "CH1" -> 1, "CH12" -> 12)
    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1))
    return 0


class AgeingVisualizationWindow:
    """Separate window for ageing analysis visualization with tabbed interface."""

    def __init__(
        self, parent: tk.Widget, results_data: Optional[Dict[str, Any]] = None
    ):
        """Initialize the visualization window.

        Args:
            parent: Parent tkinter widget.
            results_data: Optional analysis results data.
        """
        self.parent = parent
        self.results_data = results_data
        self.window = None
        self.channel_vars: Dict[str, tk.BooleanVar] = {}
        self.module_vars: Dict[str, tk.BooleanVar] = {}
        self.gaussian_var = tk.BooleanVar(value=True)  # Show gaussian method
        self.weighted_var = tk.BooleanVar(value=False)  # Show weighted method
        self._update_pending = False  # Flag to prevent multiple simultaneous updates
        self.plot_data_info: Dict[
            Tuple[str, int], Dict[str, Any]
        ] = {}  # Store data point information for tooltips
        self.tooltip_annotation = None  # Matplotlib annotation for tooltip

        # Create the window
        self._create_window()

        # Load data if provided
        if results_data:
            self._process_data()

    def _create_window(self):
        """Create the main visualization window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Ageing Analysis Visualization")
        self.window.geometry("1600x1000")
        self.window.minsize(1200, 800)

        # Create menu bar
        self._create_menu_bar()

        # Create main notebook for future tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create time series tab
        self._create_time_series_tab()

        # Create status bar
        self._create_status_bar()

        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Results...", command=self._load_results_file)
        file_menu.add_separator()
        file_menu.add_command(label="Export Plot...", command=self._export_plot)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self._on_closing)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh Plot", command=self._update_plot)
        view_menu.add_command(label="Reset Zoom", command=self._reset_zoom)

    def _create_time_series_tab(self):
        """Create the time series analysis tab."""
        self.time_series_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.time_series_frame, text="Time Series Analysis")

        # Create horizontal paned window
        paned_window = ttk.PanedWindow(self.time_series_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel for controls
        self.control_frame = ttk.Frame(paned_window, width=350)
        paned_window.add(self.control_frame, weight=0)

        # Right panel for plot
        self.plot_frame = ttk.Frame(paned_window)
        paned_window.add(self.plot_frame, weight=1)

        # Create control panel
        self._create_control_panel()

        # Create plot panel
        self._create_plot_panel()

    def _create_control_panel(self):
        """Create the control panel with selection options."""
        # Method selection
        method_frame = ttk.LabelFrame(
            self.control_frame, text="Reference Methods", padding="10"
        )
        method_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        ttk.Checkbutton(
            method_frame,
            text="Gaussian Mean",
            variable=self.gaussian_var,
            command=self._update_plot,
        ).pack(anchor=tk.W)

        ttk.Checkbutton(
            method_frame,
            text="Weighted Mean",
            variable=self.weighted_var,
            command=self._update_plot,
        ).pack(anchor=tk.W)

        # Channel selection
        self.channel_frame = ttk.LabelFrame(
            self.control_frame, text="Channel Selection", padding="10"
        )
        self.channel_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Buttons for channel selection
        button_frame = ttk.Frame(self.channel_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            button_frame, text="Select All", command=self._select_all_channels
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            button_frame, text="Deselect All", command=self._deselect_all_channels
        ).pack(side=tk.LEFT, padx=5)

        # Scrollable frame for channel checkboxes
        self._create_scrollable_channel_frame()

    def _create_scrollable_channel_frame(self):
        """Create scrollable frame for channel selection."""
        # Canvas and scrollbar for scrolling
        canvas = tk.Canvas(self.channel_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            self.channel_frame, orient="vertical", command=canvas.yview
        )
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)

    def _create_plot_panel(self):
        """Create the matplotlib plot panel."""
        # Create figure and axis
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Create navigation toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()

        # Setup empty plot
        self._setup_empty_plot()

        # Setup hover functionality (must be after packing)
        self._setup_hover_events()

    def _setup_hover_events(self):
        """Set up hover event handling for tooltips."""
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("button_press_event", self._on_click)

    def _on_hover(self, event):
        """Handle mouse hover events to show tooltips."""
        if event.inaxes != self.ax:
            self._hide_tooltip()
            return

        # Find the closest data point across all lines
        closest_distance = float("inf")
        closest_point_info = None
        closest_x = None
        closest_y = None

        # Get axis limits to normalize distances
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        x_range = xlim[1] - xlim[0]
        y_range = ylim[1] - ylim[0]

        for line in self.ax.get_lines():
            xdata, ydata = line.get_data()
            if len(xdata) == 0:
                continue

            # Convert all x to matplotlib date numbers if needed
            xdata_num = [mdates.date2num(x) if hasattr(x, "year") else x for x in xdata]
            event_x_num = event.xdata

            for i, (x_num, y) in enumerate(zip(xdata_num, ydata)):
                # Normalize coordinates to [0,1] range for fair distance calculation
                norm_x = (x_num - xlim[0]) / x_range if x_range > 0 else 0
                norm_y = (y - ylim[0]) / y_range if y_range > 0 else 0
                norm_event_x = (event_x_num - xlim[0]) / x_range if x_range > 0 else 0
                norm_event_y = (event.ydata - ylim[0]) / y_range if y_range > 0 else 0

                # Calculate Euclidean distance in normalized space
                distance = (
                    (norm_x - norm_event_x) ** 2 + (norm_y - norm_event_y) ** 2
                ) ** 0.5

                # Check if this is the closest point so far
                if distance < closest_distance:
                    closest_distance = distance
                    # Use the original x (not x_num) for tooltip display
                    closest_x = x_num
                    closest_y = y

                    # Get point information
                    point_key = (line.get_label(), i)
                    if point_key in self.plot_data_info:
                        closest_point_info = self.plot_data_info[point_key]

        # Show tooltip if we found a close enough point (within reasonable proximity)
        proximity_threshold = 0.25  # 25% of the plot area for easier testing

        if closest_distance < proximity_threshold and closest_point_info:
            self._show_tooltip(closest_x, closest_y, closest_point_info)
        else:
            self._hide_tooltip()

    def _on_click(self, event):
        """Handle mouse click events."""
        # Hide tooltip on click
        self._hide_tooltip()

    def _show_tooltip(self, x, y, info):
        """Show tooltip with point information."""
        if self.tooltip_annotation:
            self.tooltip_annotation.remove()

        tooltip_text = (
            f"PM: {info['pm']}\n"
            f"Channel: {info['channel']}\n"
            f"Method: {info['method']}\n"
            f"Date: {info['date']}\n"
            f"Value: {info['value']:.4f}"
        )

        self.tooltip_annotation = self.ax.annotate(
            tooltip_text,
            xy=(x, y),
            xytext=(20, 20),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.8),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
        )
        self.canvas.draw_idle()

    def _hide_tooltip(self):
        """Hide the tooltip."""
        if self.tooltip_annotation:
            self.tooltip_annotation.remove()
            self.tooltip_annotation = None
            self.canvas.draw_idle()

    def _create_status_bar(self):
        """Create status bar at the bottom."""
        self.status_var = tk.StringVar(
            value="Ready - Load results to begin visualization"
        )
        status_bar = ttk.Label(
            self.window,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2),
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _setup_empty_plot(self):
        """Set up empty plot with instructions."""
        self.ax.clear()
        self.ax.text(
            0.5,
            0.5,
            "Load analysis results to view ageing data\n\nFile → Load Results...",
            horizontalalignment="center",
            verticalalignment="center",
            transform=self.ax.transAxes,
            fontsize=14,
            alpha=0.6,
        )
        self.ax.set_title("Ageing Analysis - Time Series")
        # Use consistent layout with generous space for date labels
        self.fig.subplots_adjust(bottom=0.35, right=0.95, top=0.9, left=0.12)

        # Clear tooltip data and hide any existing tooltip
        self.plot_data_info.clear()
        self._hide_tooltip()

        self.canvas.draw_idle()

    def _load_results_file(self):
        """Load results from a JSON file."""
        try:
            file_path = filedialog.askopenfilename(
                title="Load Analysis Results",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                parent=self.window,
            )

            if file_path:
                with open(file_path) as f:
                    self.results_data = json.load(f)

                self._process_data()
                self.status_var.set(f"Results loaded from {Path(file_path).name}")

        except Exception as e:
            error_msg = f"Failed to load results: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg, parent=self.window)

    def _process_data(self):
        """Process the loaded results data."""
        if not self.results_data:
            return

        try:
            # Clear existing channel variables
            self.channel_vars.clear()
            self.module_vars.clear()

            # Clear scrollable frame
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()

            # Process datasets and create channel selection
            self._populate_channel_selection()

            # Update plot
            self._update_plot()

        except Exception as e:
            error_msg = f"Error processing data: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg, parent=self.window)

    def _populate_channel_selection(self):
        """Populate the channel selection interface."""
        datasets = self.results_data.get("datasets", [])
        if not datasets:
            return

        # Group channels by module across all datasets
        modules_channels = {}

        for dataset in datasets:
            for module in dataset.get("modules", []):
                module_id = module.get("identifier", "unknown")
                if module_id not in modules_channels:
                    modules_channels[module_id] = set()

                for channel in module.get("channels", []):
                    channel_name = channel.get("name", "unknown")
                    modules_channels[module_id].add(channel_name)

        # Create UI for each module
        for module_id, channels in modules_channels.items():
            # Sort channels naturally
            sorted_channels = sorted(channels, key=_natural_sort_key)
            self._create_module_section(module_id, sorted_channels)

    def _create_module_section(self, module_id: str, channels: List[str]):
        """Create a section for a module with its channels."""
        # Module frame
        module_frame = ttk.LabelFrame(
            self.scrollable_frame, text=f"Module {module_id}", padding="5"
        )
        module_frame.pack(fill=tk.X, padx=5, pady=2)

        # Module checkbox for select all/none
        module_var = tk.BooleanVar()
        self.module_vars[module_id] = module_var

        # Create callback with explicit type annotation
        def toggle_callback(mid: str = module_id) -> None:
            self._toggle_module(mid)

        module_cb = ttk.Checkbutton(
            module_frame,
            text=f"Select All ({module_id})",
            variable=module_var,
            command=toggle_callback,
        )
        module_cb.pack(anchor=tk.W)

        # Separator
        ttk.Separator(module_frame, orient="horizontal").pack(fill=tk.X, pady=2)

        # Channel checkboxes in a grid
        channels_frame = ttk.Frame(module_frame)
        channels_frame.pack(fill=tk.X)

        for i, channel_name in enumerate(channels):
            channel_key = f"{module_id}_{channel_name}"
            channel_var = tk.BooleanVar()
            self.channel_vars[channel_key] = channel_var

            cb = ttk.Checkbutton(
                channels_frame,
                text=channel_name,
                variable=channel_var,
                command=self._on_channel_change,
            )
            # Arrange in columns of 4
            cb.grid(row=i // 4, column=i % 4, sticky=tk.W, padx=5, pady=1)

    def _toggle_module(self, module_id: str):
        """Toggle all channels in a module."""
        module_var = self.module_vars[module_id]
        state = module_var.get()

        for channel_key, channel_var in self.channel_vars.items():
            if channel_key.startswith(f"{module_id}_"):
                channel_var.set(state)

        # Auto-refresh plot
        self._update_plot()

    def _on_channel_change(self):
        """Handle channel selection change."""
        self._update_module_state()
        self._update_plot()

    def _update_module_state(self):
        """Update module checkbox state based on individual channels."""
        for module_id in self.module_vars:
            # Get all channels for this module
            module_channels = [
                cv
                for ck, cv in self.channel_vars.items()
                if ck.startswith(f"{module_id}_")
            ]

            if not module_channels:
                continue

            # Check if all channels are selected
            all_selected = all(cv.get() for cv in module_channels)
            any_selected = any(cv.get() for cv in module_channels)

            module_var = self.module_vars[module_id]
            if all_selected:
                module_var.set(True)
            elif any_selected:
                # For mixed state, we'll leave it as is for now
                pass
            else:
                module_var.set(False)

    def _select_all_channels(self):
        """Select all channels."""
        for channel_var in self.channel_vars.values():
            channel_var.set(True)
        for module_var in self.module_vars.values():
            module_var.set(True)
        # Auto-refresh plot
        self._update_plot()

    def _deselect_all_channels(self):
        """Deselect all channels."""
        for channel_var in self.channel_vars.values():
            channel_var.set(False)
        for module_var in self.module_vars.values():
            module_var.set(False)
        # Auto-refresh plot
        self._update_plot()

    def _get_selected_channels(self) -> List[str]:
        """Get list of selected channel keys."""
        return [
            channel_key for channel_key, var in self.channel_vars.items() if var.get()
        ]

    def _update_plot(self):
        """Update the plot with selected channels and method."""
        # Prevent multiple simultaneous updates for better performance
        if self._update_pending:
            return
        self._update_pending = True

        # Schedule the actual update to run after current events
        self.window.after_idle(self._do_update_plot)

    def _do_update_plot(self):
        """Actually perform the plot update."""
        self._update_pending = False

        if not self.results_data:
            self._setup_empty_plot()
            return

        try:
            selected_channels = self._get_selected_channels()
            show_gaussian = self.gaussian_var.get()
            show_weighted = self.weighted_var.get()

            if not selected_channels or (not show_gaussian and not show_weighted):
                self.ax.clear()
                if not selected_channels:
                    message = "Select channels to display data"
                else:
                    message = (
                        "Select at least one reference method\n"
                        "(Gaussian Mean or Weighted Mean)"
                    )
                self.ax.text(
                    0.5,
                    0.5,
                    message,
                    horizontalalignment="center",
                    verticalalignment="center",
                    transform=self.ax.transAxes,
                    fontsize=14,
                    alpha=0.6,
                )
                self.ax.set_title("Ageing Analysis - Time Series")
                self.canvas.draw()
                return

            # Clear plot completely
            self.ax.clear()
            # Clear any existing legends to prevent overlay
            if hasattr(self.ax, "legend_") and self.ax.legend_:
                self.ax.legend_.remove()

            # Clear tooltip data for new plot
            self.plot_data_info.clear()
            self._hide_tooltip()

            # Plot data for each selected channel
            datasets = self.results_data.get("datasets", [])

            # Prepare data structure: {channel_key_method: [(date, value), ...]}
            channel_data = {}

            for dataset in datasets:
                date_str = dataset.get("date", "unknown")
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    # Try other common date formats
                    for fmt in ["%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]:
                        try:
                            date = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        logger.warning(f"Could not parse date: {date_str}")
                        continue

                for module in dataset.get("modules", []):
                    module_id = module.get("identifier", "unknown")

                    for channel in module.get("channels", []):
                        channel_name = channel.get("name", "unknown")
                        channel_key = f"{module_id}_{channel_name}"

                        if channel_key in selected_channels:
                            ageing_factors = channel.get("ageing_factors", {})

                            # Plot Gaussian method if selected
                            if show_gaussian:
                                gaussian_value = ageing_factors.get(
                                    "normalized_gauss_ageing_factor", None
                                )
                                if gaussian_value is not None and isinstance(
                                    gaussian_value, (int, float)
                                ):
                                    gaussian_key = f"{channel_key}_gaussian"
                                    if gaussian_key not in channel_data:
                                        channel_data[gaussian_key] = []
                                    channel_data[gaussian_key].append(
                                        (date, gaussian_value)
                                    )

                            # Plot Weighted method if selected
                            if show_weighted:
                                weighted_value = ageing_factors.get(
                                    "normalized_weighted_ageing_factor", None
                                )
                                if weighted_value is not None and isinstance(
                                    weighted_value, (int, float)
                                ):
                                    weighted_key = f"{channel_key}_weighted"
                                    if weighted_key not in channel_data:
                                        channel_data[weighted_key] = []
                                    channel_data[weighted_key].append(
                                        (date, weighted_value)
                                    )

            # Sort data by date and plot
            colors = plt.cm.tab20(range(len(selected_channels)))

            for channel_key_method, data_points in enumerate(channel_data.items()):
                if data_points:
                    data_points.sort(key=lambda x: x[0])  # Sort by date
                    dates, values = zip(*data_points)

                    # Extract channel and method from key
                    if channel_key_method.endswith("_gaussian"):
                        channel_key = channel_key_method[:-9]  # Remove '_gaussian'
                        method_label = "Gaussian"
                        linestyle = "-"
                        marker = "o"
                    elif channel_key_method.endswith("_weighted"):
                        channel_key = channel_key_method[:-9]  # Remove '_weighted'
                        method_label = "Weighted"
                        linestyle = "--"
                        marker = "s"
                    else:
                        channel_key = channel_key_method
                        method_label = ""
                        linestyle = "-"
                        marker = "o"

                    # Extract PM and channel from channel_key (format: "PMA0_CH1")
                    parts = channel_key.split("_", 1)
                    pm_id = parts[0] if len(parts) > 0 else "Unknown"
                    channel_name = parts[1] if len(parts) > 1 else "Unknown"

                    # Get color based on channel (consistent across methods)
                    channel_index = (
                        selected_channels.index(channel_key)
                        if channel_key in selected_channels
                        else 0
                    )
                    color = colors[channel_index % len(colors)]

                    label = f"{channel_key} ({method_label})"

                    # Plot the line
                    self.ax.plot(
                        dates,
                        values,
                        linestyle=linestyle,
                        marker=marker,
                        label=label,
                        color=color,
                        linewidth=2,
                        markersize=6,
                    )[0]

                    # Store data point information for tooltips
                    for idx, (date, value) in enumerate(zip(dates, values)):
                        point_key = (label, idx)
                        self.plot_data_info[point_key] = {
                            "pm": pm_id,
                            "channel": channel_name,
                            "method": method_label,
                            "date": date.strftime("%Y-%m-%d"),
                            "value": value,
                        }

            # Configure plot
            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Normalized Ageing Factor")

            # Create title based on selected methods
            title_methods = []
            if show_gaussian:
                title_methods.append("Gaussian")
            if show_weighted:
                title_methods.append("Weighted")
            title = (
                f"Ageing Analysis - {' & '.join(title_methods)} Method"
                f"{'s' if len(title_methods) > 1 else ''}"
            )
            self.ax.set_title(title)
            self.ax.grid(True, alpha=0.3)

            # Format x-axis with aggressive spacing to prevent overlap completely
            num_datasets = len(datasets)

            # Use MaxNLocator to limit the number of ticks from the start
            max_ticks = min(
                8, max(3, num_datasets)
            )  # Never more than 8 ticks, at least 3

            from matplotlib.ticker import MaxNLocator

            self.ax.xaxis.set_major_locator(MaxNLocator(nbins=max_ticks, prune="both"))
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))

            # Rotate labels with proper alignment
            plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

            # Ensure no label overlap by setting minimum spacing
            self.ax.tick_params(axis="x", which="major", pad=10)

            # Add legend if there are channels
            if channel_data:
                # Limit number of legend entries to prevent overcrowding
                handles, labels = self.ax.get_legend_handles_labels()
                if len(handles) <= 20:  # Show legend only if not too many entries
                    # Place legend inside plot area to avoid layout issues
                    self.ax.legend(
                        loc="upper right",
                        bbox_to_anchor=(0.98, 0.98),
                        fontsize="small",
                        framealpha=0.9,
                    )
                else:
                    # Too many entries, don't show legend
                    pass

            # Use constrained layout with generous bottom space for rotated date labels
            self.fig.subplots_adjust(bottom=0.35, right=0.95, top=0.9, left=0.12)

            # Draw canvas only once at the end
            self.canvas.draw_idle()  # Use draw_idle for better performance

            # Update status
            method_text = " & ".join(title_methods) if title_methods else "no"
            unique_channels = len(
                {
                    key[:-9] if key.endswith(("_gaussian", "_weighted")) else key
                    for key in channel_data.keys()
                }
            )
            self.status_var.set(
                f"Displaying {unique_channels} channels using {method_text} method"
                f"{'s' if len(title_methods) > 1 else ''}"
            )

        except Exception as e:
            error_msg = f"Error updating plot: {str(e)}"
            logger.error(error_msg)
            self.status_var.set("Error updating plot")
        finally:
            self._update_pending = False

    def _export_plot(self):
        """Export the current plot."""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export Plot",
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("PDF files", "*.pdf"),
                    ("SVG files", "*.svg"),
                    ("All files", "*.*"),
                ],
                parent=self.window,
            )

            if file_path:
                self.fig.savefig(file_path, dpi=300, bbox_inches="tight")
                self.status_var.set(f"Plot exported to {Path(file_path).name}")

        except Exception as e:
            error_msg = f"Failed to export plot: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg, parent=self.window)

    def _reset_zoom(self):
        """Reset plot zoom to show all data."""
        self.ax.relim()
        self.ax.autoscale()
        self.canvas.draw_idle()

    def _on_closing(self):
        """Handle window closing."""
        self.window.destroy()

    def load_results_data(self, results_data: Dict[str, Any]):
        """Load results data from external source."""
        self.results_data = results_data
        self._process_data()

    def show(self):
        """Show the visualization window."""
        if self.window:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
