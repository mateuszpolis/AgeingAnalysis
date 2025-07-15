"""Ageing Visualization Window for FIT detector ageing analysis."""

import json
import logging
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, Optional

from .grid_visualization_tab import GridVisualizationTab
from .time_series_tab import TimeSeriesTab

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
        """Initialize the AgeingVisualizationWindow.

        Args:
            parent: The parent tkinter widget that this window belongs to
            results_data: Optional dictionary containing the analysis results
        """
        self.parent = parent
        self.results_data = results_data
        self.window = None
        self.status_var = None
        self.notebook = None
        self.time_series_tab = None
        self.grid_tab = None
        self._create_window()
        if results_data:
            self.update_results_data(results_data)

    def _create_window(self):
        """Create the main visualization window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Ageing Analysis Visualization")
        self.window.geometry("1600x1000")
        self.window.minsize(1200, 800)
        self._create_menu_bar()
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.status_var = tk.StringVar(
            value="Ready - Load results to begin visualization"
        )
        # Create tabs
        self.time_series_tab = TimeSeriesTab(
            self.notebook, self.results_data, self.status_var
        )
        self.notebook.add(self.time_series_tab.frame, text="Time Series Analysis")
        self.grid_tab = GridVisualizationTab(self.notebook, self.status_var)
        self.notebook.add(self.grid_tab.frame, text="Grid Visualizations")
        self._create_status_bar()
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Bind keyboard shortcuts
        self.window.bind("<Control-s>", lambda e: self._export_plot())

    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Results...", command=self._load_results_file)
        file_menu.add_separator()
        file_menu.add_command(
            label="Export Plot...", command=self._export_plot, accelerator="Ctrl+S"
        )
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self._on_closing)
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh Plot", command=self._refresh_tabs)
        view_menu.add_command(label="Reset Zoom", command=self._reset_zoom)

    def _create_status_bar(self):
        """Create the status bar."""
        status_bar = ttk.Label(
            self.window,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2),
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _load_results_file(self):
        """Load results from a file."""
        try:
            file_path = filedialog.askopenfilename(
                title="Load Analysis Results",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                parent=self.window,
            )
            if file_path:
                with open(file_path) as f:
                    self.results_data = json.load(f)
                self.update_results_data(self.results_data)
                self.status_var.set(f"Results loaded from {Path(file_path).name}")
        except Exception as e:
            error_msg = f"Failed to load results: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg, parent=self.window)

    def update_results_data(self, results_data: Dict[str, Any]):
        """Update the results data."""
        self.results_data = results_data
        if self.time_series_tab:
            self.time_series_tab.results_data = results_data
            self.time_series_tab._process_data()
        if self.grid_tab:
            self.grid_tab.update_results_data(results_data)

    def _refresh_tabs(self):
        """Refresh the tabs."""
        if self.time_series_tab:
            self.time_series_tab._process_data()
        if self.grid_tab and self.results_data:
            self.grid_tab.update_results_data(self.results_data)

    def _export_plot(self):
        """Export the plot from the currently active tab."""
        try:
            # Determine which tab is currently active
            current_tab = self.notebook.select()
            tab_id = self.notebook.index(current_tab)

            if tab_id == 0:  # Time Series tab
                if self.time_series_tab and hasattr(self.time_series_tab, "fig"):
                    file_path = filedialog.asksaveasfilename(
                        title="Export Time Series Plot",
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
                        self.time_series_tab.fig.savefig(
                            file_path, dpi=300, bbox_inches="tight"
                        )
                        self.status_var.set(
                            f"Time series plot exported to {Path(file_path).name}"
                        )
                else:
                    messagebox.showwarning(
                        "Warning",
                        "No time series plot available to export",
                        parent=self.window,
                    )

            elif tab_id == 1:  # Grid Visualization tab
                if (
                    self.grid_tab
                    and hasattr(self.grid_tab, "fig")
                    and self.grid_tab.fig
                ):
                    # Use the grid tab's save functionality
                    self.grid_tab._save_plot()
                else:
                    messagebox.showwarning(
                        "Warning",
                        "No grid visualization available to export",
                        parent=self.window,
                    )
            else:
                messagebox.showwarning(
                    "Warning", "No plot available to export", parent=self.window
                )

        except Exception as e:
            error_msg = f"Failed to export plot: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg, parent=self.window)

    def _reset_zoom(self):
        """Reset the zoom."""
        if self.time_series_tab and hasattr(self.time_series_tab, "_reset_zoom"):
            self.time_series_tab._reset_zoom()

    def _on_closing(self):
        """Handle window closing."""
        self.window.destroy()

    def load_results_data(self, results_data: Dict[str, Any]):
        """Load the results data."""
        self.update_results_data(results_data)

    def show(self):
        """Show the window."""
        if self.window:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
