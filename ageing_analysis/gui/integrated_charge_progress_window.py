"""Progress window for integrated charge calculations."""

import logging
import threading
import time
import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class IntegratedChargeProgressWindow:
    """Window to display integrated charge calculation progress."""

    def __init__(self, parent: tk.Tk, on_complete: Optional[Callable] = None):
        """Initialize the integrated charge progress window.

        Args:
            parent: Parent tkinter window.
            on_complete: Optional callback function to call
                when calculation is complete.
        """
        self.parent = parent
        self.on_complete = on_complete
        self.calculation_thread: threading.Thread = None
        self.is_running = False

        # Create new window
        self.window = tk.Toplevel(parent)
        self.window.title("Integrated Charge Calculation Progress")
        self.window.geometry("500x300")
        self.window.resizable(True, True)

        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()

        # Create the UI
        self._create_ui()

        # Center the window
        self._center_window()

        # Configure window close event
        self.window.protocol("WM_DELETE_WINDOW", self._close_window)

    def _create_ui(self):
        """Create the progress window UI."""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header frame for logo and title
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(pady=(0, 10))

        # Title
        title_label = ttk.Label(
            header_frame,
            text="Integrated Charge Calculation",
            font=("TkDefaultFont", 14, "bold"),
        )
        title_label.pack()

        # Warning message
        warning_label = ttk.Label(
            main_frame,
            text=(
                "⚠️ This process may take a long time if data needs to be downloaded "
                "from external sources. Please be patient."
            ),
            font=("TkDefaultFont", 10),
            foreground="orange",
            wraplength=450,
            justify=tk.CENTER,
        )
        warning_label.pack(pady=(0, 15))

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
        self.status_var = tk.StringVar(value="Initializing...")
        self.status_label = ttk.Label(
            main_frame, textvariable=self.status_var, font=("TkDefaultFont", 10)
        )
        self.status_label.pack(pady=(0, 10))

        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Calculation Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, height=8, state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Close button (initially disabled)
        self.close_button = ttk.Button(
            main_frame, text="Close", command=self._close_window, state=tk.DISABLED
        )
        self.close_button.pack(pady=(10, 0))

    def _center_window(self):
        """Center the window on screen."""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def start_calculation(self, calculation_function: Callable, *args, **kwargs):
        """Start the integrated charge calculation in a separate thread.

        Args:
            calculation_function: Function to run for calculation.
            *args: Arguments to pass to the calculation function.
            **kwargs: Keyword arguments to pass to the calculation function.
        """
        if self.is_running:
            logger.warning("Calculation is already running")
            return

        self.calculation_function = calculation_function
        self.calculation_args = args
        self.calculation_kwargs = kwargs

        # Start calculation immediately
        self.is_running = True
        self.add_log_message("Starting integrated charge calculation...")
        self.update_progress(0, "Initializing calculation...")

        # Start calculation in separate thread
        self.calculation_thread = threading.Thread(
            target=self._run_calculation, daemon=True
        )
        self.calculation_thread.start()

    def _run_calculation(self):
        """Run the calculation in a separate thread."""
        try:
            # Run the calculation function
            self.calculation_function(*self.calculation_args, **self.calculation_kwargs)

            # Calculation completed successfully
            self.update_progress(100, "Calculation completed successfully!")
            self.add_log_message(
                "Integrated charge calculation completed successfully!"
            )

            # Call completion callback if provided
            if self.on_complete:
                self.window.after(100, self.on_complete)

        except Exception as e:
            error_msg = f"Calculation failed: {str(e)}"
            logger.error(error_msg)
            self.add_log_message(error_msg)
            self.update_progress(0, "Calculation failed!")

        finally:
            # Re-enable close button
            self.window.after(100, self._calculation_finished)

    def _calculation_finished(self):
        """Handle calculation completion."""
        self.is_running = False
        self.close_button.config(state=tk.NORMAL)

    def _close_window(self):
        """Close the progress window."""
        if self.is_running:
            response = tk.messagebox.askyesno(
                "Confirm Close",
                "Calculation is still running. Do you want to cancel and close?",
            )
            if response:
                self.is_running = False
            else:
                return

        self.window.destroy()

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
            self.window.update_idletasks()

        # Schedule update on main thread
        self.window.after(0, update)

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
            self.window.update_idletasks()

        # Schedule update on main thread
        self.window.after(0, add_message)
