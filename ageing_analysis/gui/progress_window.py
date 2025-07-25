"""Progress window for FIT detector ageing analysis."""

import logging
import threading
import time
import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class ProgressWindow:
    """Window to display analysis progress with real-time updates."""

    def __init__(self, parent: tk.Tk, on_complete: Optional[Callable] = None):
        """Initialize the progress window.

        Args:
            parent: Parent tkinter window.
            on_complete: Optional callback function to call when analysis is complete.
        """
        self.parent = parent
        self.on_complete = on_complete
        self.analysis_thread = None
        self.is_running = False

        # Configure parent window
        self.parent.title("Analysis Progress")
        self.parent.geometry("600x400")
        self.parent.resizable(True, True)

        # Create the UI
        self._create_ui()

        # Center the window
        self._center_window()

    def _create_ui(self):
        """Create the progress window UI."""
        # Main frame
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header frame for logo and title
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(pady=(0, 10))

        # Title
        title_label = ttk.Label(
            header_frame,
            text="FIT Detector Ageing Analysis",
            font=("TkDefaultFont", 16, "bold"),
        )
        title_label.pack()

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            length=400,
            mode="determinate",
        )
        self.progress_bar.pack(pady=(0, 10))

        # Status label
        self.status_var = tk.StringVar(value="Ready to start analysis...")
        self.status_label = ttk.Label(
            main_frame, textvariable=self.status_var, font=("TkDefaultFont", 10)
        )
        self.status_label.pack(pady=(0, 10))

        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Analysis Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, height=12, state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # Start button
        self.start_button = ttk.Button(
            button_frame,
            text="Start Analysis",
            command=self._start_analysis_clicked,
            state=tk.DISABLED,
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))

        # Cancel button
        self.cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel_analysis,
            state=tk.DISABLED,
        )
        self.cancel_button.pack(side=tk.LEFT, padx=(0, 10))

        # Close button
        self.close_button = ttk.Button(
            button_frame, text="Close", command=self._close_window
        )
        self.close_button.pack(side=tk.RIGHT)

        # Configure window close event
        self.parent.protocol("WM_DELETE_WINDOW", self._close_window)

    def _center_window(self):
        """Center the window on screen."""
        self.parent.update_idletasks()
        width = self.parent.winfo_width()
        height = self.parent.winfo_height()
        x = (self.parent.winfo_screenwidth() // 2) - (width // 2)
        y = (self.parent.winfo_screenheight() // 2) - (height // 2)
        self.parent.geometry(f"{width}x{height}+{x}+{y}")

    def start_analysis(self, analysis_function: Callable, *args, **kwargs):
        """Start the analysis in a separate thread.

        Args:
            analysis_function: Function to run for analysis.
            *args: Arguments to pass to the analysis function.
            **kwargs: Keyword arguments to pass to the analysis function.
        """
        if self.is_running:
            logger.warning("Analysis is already running")
            return

        self.analysis_function = analysis_function
        self.analysis_args = args
        self.analysis_kwargs = kwargs

        # Enable start button
        self.start_button.config(state=tk.NORMAL)
        self.add_log_message(
            "Analysis ready to start. Click 'Start Analysis' to begin."
        )

    def _start_analysis_clicked(self):
        """Handle start analysis button click."""
        if not hasattr(self, "analysis_function"):
            self.add_log_message("No analysis function configured.")
            return

        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)

        # Start analysis in separate thread
        self.analysis_thread = threading.Thread(target=self._run_analysis, daemon=True)
        self.analysis_thread.start()

    def _run_analysis(self):
        """Run the analysis in a separate thread."""
        try:
            self.add_log_message("Starting analysis...")
            self.update_progress(0, "Initializing analysis...")

            # Run the analysis function
            self.analysis_function(*self.analysis_args, **self.analysis_kwargs)

            # Analysis completed successfully
            self.update_progress(100, "Analysis completed successfully!")
            self.add_log_message("Analysis completed successfully!")

            # Call completion callback if provided
            if self.on_complete:
                self.parent.after(100, self.on_complete)

        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            logger.error(error_msg)
            self.add_log_message(error_msg)
            self.update_progress(0, "Analysis failed!")

        finally:
            # Re-enable buttons
            self.parent.after(100, self._analysis_finished)

    def _analysis_finished(self):
        """Handle analysis completion."""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)

    def _cancel_analysis(self):
        """Cancel the running analysis."""
        if self.is_running:
            self.add_log_message("Cancelling analysis...")
            self.is_running = False
            self.update_progress(0, "Analysis cancelled")
            self._analysis_finished()

    def _close_window(self):
        """Close the progress window."""
        if self.is_running:
            response = tk.messagebox.askyesno(
                "Confirm Close",
                "Analysis is still running. Do you want to cancel and close?",
            )
            if response:
                self._cancel_analysis()
            else:
                return

        self.parent.destroy()

    def update_progress(self, value: float, status: str = ""):
        """Update the progress bar and status.

        Args:
            value: Progress value (0-100).
            status: Optional status message.
        """

        def update():
            self.progress_var.set(value)
            if status:
                self.status_var.set(status)
            self.parent.update_idletasks()

        # Schedule update on main thread
        self.parent.after(0, update)

    def add_log_message(self, message: str):
        """Add a message to the log area.

        Args:
            message: Message to add to the log.
        """

        def add_message():
            self.log_text.config(state=tk.NORMAL)

            # Add timestamp
            timestamp = time.strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}\n"

            self.log_text.insert(tk.END, formatted_message)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            self.parent.update_idletasks()

        # Schedule update on main thread
        self.parent.after(0, add_message)
