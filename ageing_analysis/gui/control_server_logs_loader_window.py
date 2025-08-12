"""GUI window to parse control server logs (configuration loads).

Allows the user to select a file, a folder, or a zip/tar archive. The program
will extract archives automatically and process contained log files. The
processing calls `save_configuration_loads_from_path` from the service.
"""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from ageing_analysis.services.control_server_logs_service import (
    ControlServerLogsService,
)

logger = logging.getLogger(__name__)


class ControlServerLogsLoaderWindow:
    """Window to import control server logs from file/folder/archive.

    The user can select a file, a folder, or a zip/tar archive. The program
    will extract archives automatically and process contained log files
    (typically .log/.txt). The results are saved to parquet via the service.
    """

    def __init__(self, parent: tk.Tk | tk.Toplevel, detector_name: str = "FT0") -> None:
        """Initialize the window.

        Args:
          parent: The parent window.
          detector_name: The detector name; currently only "FT0" is supported.
        """
        self.parent = parent
        self.detector_name = detector_name
        self.window: tk.Toplevel | None = None
        self.path_var = tk.StringVar(value="")
        self.progress_var = tk.StringVar(value="Idle")
        self._worker: threading.Thread | None = None
        self.progressbar: ttk.Progressbar | None = None
        self.start_btn: ttk.Button | None = None
        self.log_widget: scrolledtext.ScrolledText | None = None

    def show(self) -> None:
        """Show the window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Parse Control Server Logs (Configuration Loads)")
        self.window.geometry("700x520")
        self.window.minsize(650, 480)
        self.window.transient(self.parent)
        self.window.grab_set()

        main = ttk.Frame(self.window, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        # Header / instructions
        header = ttk.Label(
            main,
            text=(
                "Select or drop a log file, folder, or zip/tar archive.\n"
                "The program will handle extraction automatically and parse log files."
            ),
            anchor=tk.W,
            justify=tk.LEFT,
        )
        header.pack(fill=tk.X)

        # Detector/info
        info_frame = ttk.Frame(main)
        info_frame.pack(fill=tk.X, pady=(8, 8))
        ttk.Label(info_frame, text=f"Detector: {self.detector_name} (default)").pack(
            side=tk.LEFT
        )
        ttk.Label(
            info_frame,
            text=(
                "Supported inputs: single file or directory."
                "Archives (.zip/.tar/.tgz/.tar.gz) are extracted automatically."
                "Log files with .log/.txt are scanned recursively."
            ),
            wraplength=380,
            justify=tk.RIGHT,
        ).pack(side=tk.RIGHT)

        # Path selector
        path_frame = ttk.LabelFrame(main, text="Source Path", padding=10)
        path_frame.pack(fill=tk.X)

        entry = ttk.Entry(path_frame, textvariable=self.path_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        ttk.Button(path_frame, text="Select File", command=self._select_file).pack(
            side=tk.LEFT
        )
        ttk.Button(path_frame, text="Select Folder", command=self._select_folder).pack(
            side=tk.LEFT, padx=(8, 0)
        )

        # Progress and actions
        actions = ttk.Frame(main)
        actions.pack(fill=tk.X, pady=(10, 6))

        ttk.Label(actions, textvariable=self.progress_var).pack(side=tk.LEFT)
        self.progressbar = ttk.Progressbar(actions, mode="indeterminate")
        self.progressbar.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Log area
        log_frame = ttk.LabelFrame(main, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        self.log_widget = scrolledtext.ScrolledText(
            log_frame, height=12, state=tk.NORMAL
        )
        self.log_widget.pack(fill=tk.BOTH, expand=True)
        self._log(
            "Detector is fixed to FT0 for now. Other detectors are not supported yet."
        )

        # Footer buttons
        footer = ttk.Frame(main)
        footer.pack(fill=tk.X, pady=(8, 0))
        self.start_btn = ttk.Button(footer, text="Start Parsing", command=self._start)
        self.start_btn.pack(side=tk.RIGHT)
        ttk.Button(footer, text="Close", command=self.window.destroy).pack(
            side=tk.RIGHT, padx=(8, 0)
        )

        entry.focus_set()

    def _select_file(self) -> None:
        """Select a file."""
        file_path = filedialog.askopenfilename(
            parent=self.window,
            title="Select log file or archive",
            filetypes=[
                ("Logs/Archive", "*.log *.txt *.zip *.tar *.tar.gz *.tgz *.tar.bz2"),
                ("All files", "*.*"),
            ],
        )
        if file_path:
            self.path_var.set(file_path)

    def _select_folder(self) -> None:
        """Select a folder."""
        dir_path = filedialog.askdirectory(parent=self.window, title="Select folder")
        if dir_path:
            self.path_var.set(dir_path)

    def _start(self) -> None:
        """Start the parsing."""
        if self.window is None or self.progressbar is None or self.start_btn is None:
            return
        source = self.path_var.get().strip()
        if not source:
            messagebox.showwarning(
                "Missing path",
                "Please select a file, folder, or archive (zip/tar) to import.",
                parent=self.window,
            )
            return
        path = Path(source)
        if not path.exists():
            messagebox.showerror(
                "Invalid path",
                f"The selected path does not exist:\n{source}",
                parent=self.window,
            )
            return

        # Disable UI while running
        self.start_btn.config(state=tk.DISABLED)
        self.progressbar.start(10)
        self.progress_var.set("Running...")
        self._log(f"Starting log parsing from: {source}")

        def worker() -> None:
            try:
                service = ControlServerLogsService(detector_name=self.detector_name)
                service.save_configuration_loads_from_path(source)
                if self.window is not None:
                    self.window.after(0, self._on_success)
            except Exception as e:
                if self.window is not None:
                    self.window.after(0, self._on_error, str(e))

        self._worker = threading.Thread(target=worker, daemon=True)
        self._worker.start()

    def _on_success(self) -> None:
        """Handle successful parsing."""
        if self.progressbar is not None:
            self.progressbar.stop()
        self.progress_var.set("Completed")
        self._log("Parsing completed successfully. Configuration loads saved.")
        if self.window is not None:
            messagebox.showinfo(
                "Parse Control Server Logs",
                (
                    "Parsing completed successfully.\n\n"
                    "You can now re-run actions that use configuration load history."
                ),
                parent=self.window,
            )
        if self.start_btn is not None:
            self.start_btn.config(state=tk.NORMAL)

    def _on_error(self, msg: str) -> None:
        """Handle error."""
        if self.progressbar is not None:
            self.progressbar.stop()
        self.progress_var.set("Error")
        self._log(f"Error: {msg}")
        if self.window is not None:
            messagebox.showerror("Parse Control Server Logs", msg, parent=self.window)
        if self.start_btn is not None:
            self.start_btn.config(state=tk.NORMAL)

    def _log(self, text: str) -> None:
        """Log a message to the window."""
        if self.log_widget is None:
            return
        self.log_widget.insert(tk.END, text + "\n")
        self.log_widget.see(tk.END)
