#!/usr/bin/env python3

"""
Simplified Ageing Factors Visualization.

This script provides a simplified version of the ageing factors visualization
that focuses on the ageing plot functionality.
"""

import argparse
import json
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class AgeingPlot:
    """Simplified Ageing Factors Visualization."""

    def __init__(self, root, json_file=None):
        """Initialize the ageing plot.

        Args:
            root (tk.Tk): The root Tkinter window.
            json_file (str, optional): Path to a JSON file containing analysis results.
        """
        self.root = root
        self.data = None
        self.channel_vars = {}
        self.module_vars = {}

        # Set window properties
        self.root.title("Ageing Factors Visualization")
        self.root.geometry("1200x800")

        # Create main layout
        self.create_layout()

        # Load data if JSON file is provided
        if json_file:
            self.load_from_json_file(json_file)

    def create_layout(self):
        """Create the main layout."""
        # Create a PanedWindow for resizable sections
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel for controls
        self.control_frame = ttk.Frame(self.paned_window, width=300)
        self.paned_window.add(self.control_frame, weight=1)

        # Right panel for plot
        self.plot_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.plot_frame, weight=3)

        # Create control panel contents
        self.create_control_panel()

        # Create plot panel contents
        self.create_plot_panel()

        # Create status bar
        self.status_frame = ttk.Frame(self.root)
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

    def create_control_panel(self):
        """Create the control panel with selection options."""
        # Header
        header_label = ttk.Label(
            self.control_frame, text="Selection Controls", font=("TkDefaultFont", 12, "bold")
        )
        header_label.pack(anchor=tk.W, pady=(0, 10))

        # Factor type selection
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

        # Module selection
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
            lambda e: self.canvas_scroll.configure(scrollregion=self.canvas_scroll.bbox("all")),
        )

        self.canvas_scroll.create_window((0, 0), window=self.scrollable_frame, anchor=tk.NW)
        self.canvas_scroll.configure(yscrollcommand=scrollbar.set)

        # Enable mousewheel scrolling
        self.canvas_scroll.bind(
            "<Enter>", lambda e: self.canvas_scroll.bind_all("<MouseWheel>", self._on_mousewheel)
        )
        self.canvas_scroll.bind("<Leave>", lambda e: self.canvas_scroll.unbind_all("<MouseWheel>"))

        self.canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Placeholder text when no data is loaded
        self.placeholder_label = ttk.Label(
            self.scrollable_frame, text="No data loaded. Please load a JSON file.", wraplength=250
        )
        self.placeholder_label.pack(pady=20, padx=10)

        # Clear selection button
        ttk.Button(self.control_frame, text="Clear Selection", command=self._clear_selection).pack(
            fill=tk.X, pady=10, padx=10
        )

    def create_plot_panel(self):
        """Create the plot panel."""
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
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Setup hover annotation
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
            arrowprops={"arrowstyle": "->", "connectionstyle": "arc3,rad=.2", "color": "black"},
            fontsize=10,
            fontweight="bold",
        )
        self.annot.set_visible(False)

        # Connect hover events
        self.hover_cid = self.canvas.mpl_connect("motion_notify_event", self._on_hover)

        # Connect click event
        self.click_cid = self.canvas.mpl_connect("button_press_event", self._on_click)

        # Initial plot setup
        self._setup_empty_plot()

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

    def load_from_json_file(self, file_path):
        """Load data from a JSON file.

        Args:
            file_path (str): Path to the JSON file to load.

        Returns:
            bool: True if loading was successful, False otherwise.
        """
        try:
            print(f"Loading data from {file_path}")
            with open(file_path, "r") as f:
                data = json.load(f)

            # Store the data
            self.data = data

            # Process the data structure
            if "datasets" in data:
                print(f"Found {len(data['datasets'])} datasets")

                # Check if we have the expected structure
                if len(data["datasets"]) > 0:
                    first_dataset = data["datasets"][0]
                    print(f"First dataset date: {first_dataset.get('date', 'unknown')}")

                    if "modules" in first_dataset:
                        print(f"Found {len(first_dataset['modules'])} modules in first dataset")

                        # Check if modules have the expected structure
                        if len(first_dataset["modules"]) > 0:
                            first_module = first_dataset["modules"][0]
                            id = first_module.get("identifier") or first_module.get("id", "unknown")
                            print(f"First module ID: {id}")

                            if "channels" in first_module:
                                print(
                                    f"Found {len(first_module['channels'])} "
                                    f"channels in first module"
                                )

                                # Check if channels have ageing factors
                                if len(first_module["channels"]) > 0:
                                    first_channel = first_module["channels"][0]
                                    if "ageing_factors" in first_channel:
                                        print("Found ageing factors in first channel")

            # Populate the module selection panel
            self._populate_module_selection()

            self.status_var.set(
                f"Loaded data from {Path(file_path).name} - Select channels to view ageing factors"
            )
            return True
        except Exception as e:
            import traceback

            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to load JSON file: {str(e)}")
            self.status_var.set("Error loading file")
            return False

    def _populate_module_selection(self):
        """Populate the module selection panel with data from the loaded file."""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Clear existing variables
        self.channel_vars.clear()
        self.module_vars.clear()

        print("Populating module selection...")

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

        # Add "Select All Modules" button at the top
        select_all_frame = ttk.Frame(self.scrollable_frame)
        select_all_frame.pack(fill=tk.X, pady=5, padx=5)

        ttk.Button(
            select_all_frame, text="Select All Channels", command=self._select_all_channels
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(
            select_all_frame, text="Deselect All Channels", command=self._deselect_all_channels
        ).pack(side=tk.LEFT, padx=5, pady=5)

        # Create module sections
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
                command=lambda mid=module_id: self._toggle_module(mid),
            ).pack(anchor=tk.W, padx=5, pady=2)

            # Channel checkboxes
            for channel in modules[module_id]:
                channel_id = f"{module_id}:{channel}"
                channel_var = tk.BooleanVar(value=False)
                self.channel_vars[channel_id] = channel_var

                ttk.Checkbutton(
                    module_frame, text=channel, variable=channel_var, command=self._update_plot
                ).pack(anchor=tk.W, padx=20, pady=2)

        # Update the canvas scroll region
        self.canvas_scroll.configure(scrollregion=self.canvas_scroll.bbox("all"))

        # Make sure the scrollbar is visible and working
        self.canvas_scroll.update_idletasks()
        self.canvas_scroll.yview_moveto(0)

    def _process_module_data(self):
        """Process the loaded data to extract module and channel information.

        Returns:
            dict: A dictionary mapping module IDs to lists of channel names.
        """
        modules = {}

        # Extract from datasets
        if "datasets" in self.data:
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

        # Print debug information
        if not modules:
            print("No modules found in data")
        else:
            print(f"Found {len(modules)} modules with data")
            for module_id, channels in modules.items():
                print(f"Module {module_id} has {len(channels)} channels")

        return modules

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

    def _toggle_module(self, module_id):
        """Toggle all channels in a module.

        Args:
            module_id (str): The ID of the module to toggle.
        """
        state = self.module_vars[module_id].get()
        print(f"Toggling module {module_id} to {state}")

        # Set all channel checkboxes for this module to the same state
        for channel_id, var in self.channel_vars.items():
            if channel_id.startswith(f"{module_id}:"):
                var.set(state)

        # Update the plot
        self._update_plot()

    def _clear_selection(self):
        """Clear all selected channels."""
        self._deselect_all_channels()

        # Clear the plot
        self.ax.clear()
        self.ax.set_title("No channels selected")
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Ageing Factor")
        self.canvas.draw()

        # Update status
        self.status_var.set("Selection cleared - Select channels to view ageing factors")

    def _get_selected_channels(self):
        """Get the list of currently selected channels.

        Returns:
            list: A list of selected channel IDs.
        """
        selected = []

        for channel_id, channel_var in self.channel_vars.items():
            if channel_var.get():
                selected.append(channel_id)

        print(f"Selected channels: {selected}")
        return selected

    def _update_plot(self):
        """Update the plot with selected channels."""
        # Clear the current plot
        self.ax.clear()

        # Get selected channels
        selected_channels = self._get_selected_channels()
        print(f"Selected channels: {selected_channels}")

        # If no channels are selected, show empty plot
        if not selected_channels:
            self.ax.set_title("No channels selected")
            self.status_var.set("No channels selected. Please select at least one channel.")
            self._setup_empty_plot()
            return

        # Add traces for selected channels
        traces_added = self._add_channel_traces(selected_channels)

        if not traces_added:
            self.ax.set_title("No data available for selected channels")
            self.status_var.set("No data available for the selected channels and factor types.")
            self._setup_empty_plot()
            return

        # Set plot title
        factor_types = []
        if self.gaussian_var.get():
            factor_types.append("Gaussian")
        if self.weighted_var.get():
            factor_types.append("Weighted")

        title = f"Ageing Factors ({', '.join(factor_types)})"
        self.ax.set_title(title)

        # Set axis labels
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Ageing Factor")

        # Format x-axis as dates
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())

        # Rotate date labels for better readability
        plt.setp(self.ax.get_xticklabels(), rotation=45, ha="right")

        # Add grid for readability
        self.ax.grid(True, linestyle="--", alpha=0.7)

        # Set y-axis limits
        self.ax.set_ylim(0, 1.1)

        # Add legend
        self.ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)

        # Adjust layout to make room for the legend
        self.fig.tight_layout()
        self.fig.subplots_adjust(right=0.8)

        # Update the canvas
        self.canvas.draw()

        # Reconnect hover and click events
        if hasattr(self, "hover_cid"):
            self.canvas.mpl_disconnect(self.hover_cid)
        if hasattr(self, "click_cid"):
            self.canvas.mpl_disconnect(self.click_cid)

        self.hover_cid = self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.click_cid = self.canvas.mpl_connect("button_press_event", self._on_click)

        # Update status
        self.status_var.set(
            f"Displaying ageing factors for {len(selected_channels)} selected channels."
        )

    def _add_channel_traces(self, selected_channels):
        """Add traces for selected channels to the plot.

        Args:
            selected_channels (list): List of selected channel IDs.

        Returns:
            bool: True if any traces were added, False otherwise.
        """
        if not self.data or "datasets" not in self.data or not self.data["datasets"]:
            print("No datasets found in data")
            return False

        # Get the factor types to display
        show_gaussian = self.gaussian_var.get()
        show_weighted = self.weighted_var.get()

        if not show_gaussian and not show_weighted:
            print("No factor types selected")
            return False

        # Initialize scatter points list
        self.scatter_points = []

        # Track if we added any traces
        added_traces = False

        # Process each selected channel
        for channel_id in selected_channels:
            print(f"Processing channel: {channel_id}")

            # Split the channel ID into module and channel
            if ":" not in channel_id:
                print(f"Invalid channel ID format: {channel_id}")
                continue

            module_id, channel_name = channel_id.split(":")

            # Collect dates and factors for this channel across all datasets
            gaussian_dates = []
            gaussian_factors = []
            weighted_dates = []
            weighted_factors = []

            # Process each dataset
            for dataset in self.data["datasets"]:
                # Get the date for this dataset
                if "date" not in dataset:
                    continue

                date_str = dataset["date"]
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    print(f"Invalid date format: {date_str}")
                    continue

                # Find the module in this dataset
                module = None
                for m in dataset.get("modules", []):
                    if m.get("identifier", m.get("id", "")) == module_id:
                        module = m
                        break

                if not module:
                    continue

                # Find the channel in this module
                channel = None
                for c in module.get("channels", []):
                    if c.get("name", "") == channel_name:
                        channel = c
                        break

                if not channel:
                    continue

                # Get the ageing factors
                ageing_factors = channel.get("ageing_factors", {})

                # Add Gaussian factor if available and selected
                if show_gaussian and "gaussian" in ageing_factors:
                    gaussian_factor = ageing_factors["gaussian"]
                    if gaussian_factor is not None:
                        gaussian_dates.append(date)
                        gaussian_factors.append(gaussian_factor)

                # Add weighted factor if available and selected
                if show_weighted and "weighted" in ageing_factors:
                    weighted_factor = ageing_factors["weighted"]
                    if weighted_factor is not None:
                        weighted_dates.append(date)
                        weighted_factors.append(weighted_factor)

            # Add traces if we have data
            if show_gaussian and gaussian_dates and gaussian_factors:
                # Create a scatter plot for Gaussian factors
                scatter = self.ax.scatter(
                    gaussian_dates,
                    gaussian_factors,
                    label=f"{channel_id} (Gaussian)",
                    marker="o",
                    s=20,  # Size of markers
                    alpha=0.7,
                )

                # Store the scatter plot and its data for hover functionality
                labels = [f"{channel_id} (Gaussian)"] * len(gaussian_dates)
                self.scatter_points.append((scatter, gaussian_dates, gaussian_factors, labels))

                added_traces = True

            if show_weighted and weighted_dates and weighted_factors:
                # Create a scatter plot for Weighted factors
                scatter = self.ax.scatter(
                    weighted_dates,
                    weighted_factors,
                    label=f"{channel_id} (Weighted)",
                    marker="s",  # Square marker to distinguish from Gaussian
                    s=20,  # Size of markers
                    alpha=0.7,
                )

                # Store the scatter plot and its data for hover functionality
                labels = [f"{channel_id} (Weighted)"] * len(weighted_dates)
                self.scatter_points.append((scatter, weighted_dates, weighted_factors, labels))

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
            # Skip if the scatter plot is not visible
            if not scatter.get_visible():
                continue

            # Get the data from the scatter plot
            for i, (x, y, label) in enumerate(zip(dates, values, labels)):
                # Convert event.xdata to datetime for comparison if needed
                if isinstance(x, datetime):
                    # Convert event.xdata (float) to datetime for comparison
                    try:
                        event_date = mdates.num2date(event.xdata)
                        # Calculate distance in days
                        x_dist = abs((x - event_date).total_seconds())
                    except (TypeError, ValueError):
                        continue
                else:
                    # Regular numerical comparison
                    x_dist = abs(x - event.xdata)

                y_dist = abs(y - event.ydata)
                dist = (x_dist**2 + y_dist**2) ** 0.5

                # Update if this point is closer
                if dist < min_dist:
                    min_dist = dist
                    closest_point = (scatter, i, x, y, label)

        # If we found a close point and it's within a reasonable distance
        if closest_point and min_dist < 0.1:  # Adjust threshold as needed
            scatter, idx, x, y, label = closest_point

            # Update annotation
            self.annot.xy = (mdates.date2num(x) if isinstance(x, datetime) else x, y)

            # Format the date for display
            if isinstance(x, datetime):
                date_str = x.strftime("%Y-%m-%d")
                text = f"{label}\nDate: {date_str}\nValue: {y:.4f}"
            else:
                text = f"{label}\nX: {x:.4f}\nY: {y:.4f}"

            self.annot.set_text(text)
            self.annot.get_bbox_patch().set_alpha(0.9)
            self.annot.set_visible(True)

            # Highlight the point
            for s in [s for s, _, _, _ in self.scatter_points]:
                s.set_sizes(
                    [30 if s == scatter and i == idx else 20 for i in range(len(s.get_offsets()))]
                )

            self.canvas.draw_idle()
        else:
            # If no close point, hide annotation and reset point sizes
            if self.annot.get_visible():
                self.annot.set_visible(False)
                for s, _, _, _ in self.scatter_points:
                    s.set_sizes([20] * len(s.get_offsets()))
                self.canvas.draw_idle()

    def _on_click(self, event):
        """Handle mouse click events on the plot."""
        # Just use the same hover logic for clicks
        self._on_hover(event)

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        self.canvas_scroll.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def run(self):
        """Run the application."""
        self.root.mainloop()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Simplified Ageing Factors Visualization")
    parser.add_argument("--json", type=str, help="Path to a JSON file containing analysis results")
    return parser.parse_args()


def main():
    """Main entry point for the application."""
    args = parse_arguments()

    # Create a new Tkinter root window
    root = tk.Tk()

    # Create the ageing plot
    plot = AgeingPlot(root=root, json_file=args.json)

    # Start the Tkinter main loop
    plot.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
