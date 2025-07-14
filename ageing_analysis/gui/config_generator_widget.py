"""Config generator widget for FIT detector ageing analysis."""

import logging
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional, Union

from ageing_analysis.services.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class ConfigGeneratorWidget:
    """GUI widget for generating configuration files."""

    def __init__(
        self, parent: Union[tk.Tk, tk.Toplevel], root_path: Optional[str] = None
    ):
        """Initialize the config generator widget.

        Args:
            parent: Parent window (Tk or Toplevel).
            root_path: Root path for the project.
        """
        self.parent = parent
        self.root_path = root_path
        self.config_manager = ConfigManager(root_path)

        # Create main frame
        self.main_frame = ttk.Frame(parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Initialize UI components
        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """Create all GUI widgets."""
        # Title
        self.title_label = ttk.Label(
            self.main_frame, text="Configuration Generator", font=("Arial", 14, "bold")
        )

        # Input groups section
        self.inputs_frame = ttk.LabelFrame(self.main_frame, text="Input Groups")

        # Buttons frame
        self.buttons_frame = ttk.Frame(self.inputs_frame)

        self.add_group_btn = ttk.Button(
            self.buttons_frame, text="Add Input Group", command=self._add_input_group
        )

        self.remove_group_btn = ttk.Button(
            self.buttons_frame,
            text="Remove Selected",
            command=self._remove_selected_group,
        )

        self.clear_all_btn = ttk.Button(
            self.buttons_frame, text="Clear All", command=self._clear_all_groups
        )

        # Input groups list
        self.list_frame = ttk.Frame(self.inputs_frame)

        # Scrollable listbox for input groups
        self.groups_listbox = tk.Listbox(self.list_frame, height=10)
        self.scrollbar = ttk.Scrollbar(self.list_frame, orient=tk.VERTICAL)
        self.groups_listbox.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.configure(command=self.groups_listbox.yview)

        # Configuration section
        self.config_frame = ttk.LabelFrame(self.main_frame, text="Configuration")

        # Config buttons
        self.config_buttons_frame = ttk.Frame(self.config_frame)

        self.preview_btn = ttk.Button(
            self.config_buttons_frame,
            text="Preview Config",
            command=self._preview_config,
        )

        self.save_btn = ttk.Button(
            self.config_buttons_frame, text="Save Config", command=self._save_config
        )

        self.load_btn = ttk.Button(
            self.config_buttons_frame, text="Load Config", command=self._load_config
        )

        # Status section
        self.status_frame = ttk.LabelFrame(self.main_frame, text="Status")

        self.status_text = tk.Text(
            self.status_frame, height=8, width=80, state=tk.DISABLED, wrap=tk.WORD
        )

        self.status_scrollbar = ttk.Scrollbar(self.status_frame, orient=tk.VERTICAL)
        self.status_text.configure(yscrollcommand=self.status_scrollbar.set)
        self.status_scrollbar.configure(command=self.status_text.yview)

    def _setup_layout(self):
        """Set up the widget layout."""
        # Title
        self.title_label.pack(pady=(0, 10))

        # Input groups section
        self.inputs_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Buttons frame
        self.buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        self.add_group_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.remove_group_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.clear_all_btn.pack(side=tk.LEFT)

        # List frame
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.groups_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configuration section
        self.config_frame.pack(fill=tk.X, pady=(0, 10))

        # Config buttons
        self.config_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        self.preview_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.save_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.load_btn.pack(side=tk.LEFT)

        # Status section
        self.status_frame.pack(fill=tk.BOTH, expand=True)
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)

    def _add_input_group(self):
        """Add a new input group by selecting folder and files."""
        try:
            # Temporarily release grab for file dialogs
            self.parent.grab_release()

            # Select folder containing files
            folder_path = filedialog.askdirectory(
                title="Select Folder Containing Files"
            )
            if not folder_path:
                self.parent.grab_set()
                return

            # Select CSV files
            file_paths = filedialog.askopenfilenames(
                title="Select CSV Files (max 20)",
                filetypes=[("CSV Files", "*.csv")],
                initialdir=folder_path,
            )

            # Restore grab
            self.parent.grab_set()

            if not file_paths:
                return

            # Check file count
            if len(file_paths) > 20:
                messagebox.showerror(
                    "Too Many Files", "Please select a maximum of 20 files."
                )
                return

            # Extract PM identifiers to offer reference selection
            pm_identifiers = []
            for file_path in file_paths:
                filename = os.path.basename(file_path)
                import re

                pm_match = re.search(r"(PM[AC][0-9])", filename)
                if pm_match:
                    pm_identifiers.append(pm_match.group(0))

            # Ask for reference PM if more than one PM
            reference_pm = None
            if len(pm_identifiers) > 1:
                reference_pm = self._ask_reference_pm(pm_identifiers)

            # Add the input group
            success, message = self.config_manager.add_input_group(
                folder_path, file_paths, reference_pm
            )

            if success:
                self._update_groups_display()
                self._log_status(f"✓ {message}")
            else:
                self._log_status(f"✗ Error: {message}")
                messagebox.showerror("Error", message)

        except Exception as e:
            # Ensure grab is restored even if there's an error
            self.parent.grab_set()
            error_msg = f"Error adding input group: {str(e)}"
            self._log_status(f"✗ {error_msg}")
            messagebox.showerror("Error", error_msg)

    def _ask_reference_pm(self, pm_identifiers: List[str]) -> Optional[str]:
        """Ask user to select a reference PM from available options.

        Args:
            pm_identifiers: List of available PM identifiers.

        Returns:
            Selected PM identifier or None if cancelled.
        """
        # Default to PMC9 if available
        if "PMC9" in pm_identifiers:
            return "PMC9"

        # Create dialog for PM selection
        dialog = tk.Toplevel()  # Create without parent to avoid type error
        dialog.title("Select Reference PM")
        dialog.geometry("300x250")
        dialog.transient(
            self.parent
        )  # Still set transient parent for proper window behavior
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        ttk.Label(dialog, text="Select a reference PM:").pack(pady=10)

        # Create listbox for PM selection
        pm_listbox = tk.Listbox(dialog, height=8)
        pm_listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        for pm in sorted(pm_identifiers):
            pm_listbox.insert(tk.END, pm)

        # Select first item by default
        pm_listbox.selection_set(0)

        selected_pm = [None]  # Use list to store result

        def on_select():
            selection = pm_listbox.curselection()
            if selection:
                selected_pm[0] = pm_identifiers[selection[0]]
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Select", command=on_select).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(
            side=tk.LEFT, padx=5
        )

        # Wait for dialog to close
        self.parent.wait_window(dialog)
        return selected_pm[0]

    def _remove_selected_group(self):
        """Remove the selected input group."""
        selection = self.groups_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a group to remove.")
            return

        # Remove from config manager
        index = selection[0]
        if 0 <= index < len(self.config_manager.inputs):
            removed_group = self.config_manager.inputs.pop(index)
            self._update_groups_display()
            self._log_status(f"✓ Removed group: {removed_group.get('date', 'Unknown')}")

    def _clear_all_groups(self):
        """Clear all input groups."""
        if self.config_manager.get_input_count() == 0:
            messagebox.showinfo("No Groups", "No input groups to clear.")
            return

        result = messagebox.askyesno(
            "Clear All", "Are you sure you want to clear all input groups?"
        )

        if result:
            self.config_manager.clear_inputs()
            self._update_groups_display()
            self._log_status("✓ All input groups cleared")

    def _update_groups_display(self):
        """Update the input groups display."""
        self.groups_listbox.delete(0, tk.END)

        summaries = self.config_manager.get_inputs_summary()
        for summary in summaries:
            display_text = (
                f"{summary['date']} - {summary['file_count']} files - "
                f"Ref: {summary['reference_pm']}"
            )
            self.groups_listbox.insert(tk.END, display_text)

    def _preview_config(self):
        """Preview the generated configuration."""
        if self.config_manager.get_input_count() == 0:
            messagebox.showinfo("No Data", "No input groups to preview.")
            return

        try:
            config = self.config_manager.generate_config()

            # Create preview window
            preview_window = tk.Toplevel(self.parent)
            preview_window.title("Configuration Preview")
            preview_window.geometry("800x600")
            preview_window.minsize(600, 400)

            # Center the window relative to parent
            preview_window.update_idletasks()
            parent_x = self.parent.winfo_rootx()
            parent_y = self.parent.winfo_rooty()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()

            x = parent_x + (parent_width // 2) - (preview_window.winfo_width() // 2)
            y = parent_y + (parent_height // 2) - (preview_window.winfo_height() // 2)
            preview_window.geometry(f"+{x}+{y}")

            # Make window modal relative to parent
            preview_window.transient(self.parent)
            preview_window.grab_set()

            # Create text widget with scrollbar
            text_frame = ttk.Frame(preview_window)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            text_widget = tk.Text(text_frame, wrap=tk.WORD)
            text_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)

            text_widget.configure(yscrollcommand=text_scrollbar.set)
            text_scrollbar.configure(command=text_widget.yview)

            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Insert configuration JSON
            import json

            config_json = json.dumps(config, indent=4)
            text_widget.insert(tk.END, config_json)
            text_widget.configure(state=tk.DISABLED)

            # Button frame
            button_frame = ttk.Frame(preview_window)
            button_frame.pack(fill=tk.X, padx=10, pady=10)

            # Close button
            close_button = ttk.Button(
                button_frame, text="Close", command=preview_window.destroy
            )
            close_button.pack(side=tk.RIGHT)

            # Handle window closing
            def on_preview_close():
                preview_window.grab_release()
                preview_window.destroy()

            preview_window.protocol("WM_DELETE_WINDOW", on_preview_close)

            # Focus on the preview window
            preview_window.focus_set()

        except Exception as e:
            error_msg = f"Error generating preview: {str(e)}"
            self._log_status(f"✗ {error_msg}")
            messagebox.showerror("Error", error_msg)

    def _save_config(self):
        """Save the configuration to a file."""
        if self.config_manager.get_input_count() == 0:
            messagebox.showinfo("No Data", "No input groups to save.")
            return

        try:
            # Temporarily release grab for file dialog
            self.parent.grab_release()

            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                title="Save Configuration",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                initialfile="config.json",
            )

            # Restore grab
            self.parent.grab_set()

            if not file_path:
                return

            success, result = self.config_manager.save_config(file_path)

            if success:
                self._log_status(f"✓ Configuration saved to: {result}")
                messagebox.showinfo(
                    "Success", f"Configuration saved successfully to:\n{result}"
                )
            else:
                self._log_status(f"✗ Error saving: {result}")
                messagebox.showerror(
                    "Error", f"Failed to save configuration:\n{result}"
                )

        except Exception as e:
            # Ensure grab is restored even if there's an error
            self.parent.grab_set()
            error_msg = f"Error saving configuration: {str(e)}"
            self._log_status(f"✗ {error_msg}")
            messagebox.showerror("Error", error_msg)

    def _load_config(self):
        """Load a configuration from a file."""
        try:
            # Temporarily release grab for file dialog
            self.parent.grab_release()

            file_path = filedialog.askopenfilename(
                title="Load Configuration", filetypes=[("JSON files", "*.json")]
            )

            # Restore grab
            self.parent.grab_set()

            if not file_path:
                return

            success, message = self.config_manager.load_config(file_path)

            if success:
                self._update_groups_display()
                self._log_status(f"✓ Configuration loaded: {message}")
                messagebox.showinfo(
                    "Success", f"Configuration loaded successfully:\n{message}"
                )
            else:
                self._log_status(f"✗ Error loading: {message}")
                messagebox.showerror(
                    "Error", f"Failed to load configuration:\n{message}"
                )

        except Exception as e:
            # Ensure grab is restored even if there's an error
            self.parent.grab_set()
            error_msg = f"Error loading configuration: {str(e)}"
            self._log_status(f"✗ {error_msg}")
            messagebox.showerror("Error", error_msg)

    def _log_status(self, message: str):
        """Log a status message to the status text widget.

        Args:
            message: Message to log.
        """
        self.status_text.configure(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.configure(state=tk.DISABLED)
        self.status_text.see(tk.END)

        # Log to logger as well
        if "✓" in message:
            logger.info(message.replace("✓ ", ""))
        elif "✗" in message:
            logger.error(message.replace("✗ ", ""))
        else:
            logger.debug(message)

    def get_frame(self) -> ttk.Frame:
        """Get the main frame of the widget.

        Returns:
            Main frame widget.
        """
        return self.main_frame
