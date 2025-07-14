"""Grid Visualizations Tab for Ageing Analysis Visualization."""

import tkinter as tk
from tkinter import ttk


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
        self.frame = ttk.Frame(self.parent)
        label = ttk.Label(
            self.frame,
            text="Grid visualizations coming soon!",
            font=("TkDefaultFont", 16, "bold"),
        )
        label.pack(expand=True, fill=tk.BOTH, pady=100)
