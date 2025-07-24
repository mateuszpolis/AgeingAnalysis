#!/usr/bin/env python3
"""Main entry point for the AgeingAnalysis module.

This module provides a complete ageing analysis pipeline for FIT detector data,
including data processing, statistical analysis, and interactive visualization.
"""

import argparse
import datetime
import logging
import sys
import tkinter as tk
from pathlib import Path
from tkinter import TclError, filedialog, messagebox, ttk

from .entities import Config
from .gui import AgeingVisualizationWindow, ConfigGeneratorWidget, ProgressWindow
from .services import (
    AgeingCalculationService,
    DataNormalizer,
    DataParser,
    GaussianFitService,
    ReferenceChannelService,
)
from .utils import load_results, save_results

# Set up basic logging (will be reconfigured in AgeingAnalysisApp)
logger = logging.getLogger(__name__)


class AgeingAnalysisApp:
    """Main application class for the AgeingAnalysis module."""

    def __init__(
        self,
        parent=None,
        headless=False,
        config_path=None,
        debug_mode=False,
        prominence_percent=None,
        peak_merge_threshold=5,
    ):
        """Initialize the AgeingAnalysis application.

        Args:
            parent: Parent window (optional, for integration with launcher)
            headless: If True, run without GUI (default: False)
            config_path: Path to configuration file (optional)
            debug_mode: If True, enable debug logging and debug plots (default: False)
            prominence_percent: Prominence percentage for peak detection (optional)
            peak_merge_threshold: Threshold for merging peaks when bases are this close
        """
        self.parent = parent
        self.root = None
        self.is_standalone = parent is None
        self.headless = headless
        self.config = None
        self.results_path = None
        self.debug_mode = debug_mode
        self.prominence_percent = prominence_percent
        self.peak_merge_threshold = peak_merge_threshold
        self.visualization_window = None

        # Configure logging based on debug mode
        self._configure_logging()

        # Module configuration
        self.module_path = Path(__file__).parent

        # Load config if provided
        if config_path:
            self._load_config(config_path)

        logger.info(
            f"AgeingAnalysis application initialized "
            f"(headless: {headless}, debug_mode: {debug_mode}, "
            f"prominence_percent: {prominence_percent}, "
            f"peak_merge_threshold: {peak_merge_threshold})"
        )

    def _configure_logging(self):
        """Configure logging based on debug mode."""
        log_level = logging.DEBUG if self.debug_mode else logging.INFO
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        # Configure the root logger
        logging.basicConfig(
            level=log_level,
            format=log_format,
            force=True,  # Override any existing configuration
        )

        # Also set the level for specific loggers we care about
        logging.getLogger("ageing_analysis").setLevel(log_level)

        if self.debug_mode:
            logger.info(
                "Debug mode enabled - verbose logging and debug plots will be generated"
            )
        else:
            logger.info("Standard logging mode")

    def _load_config(self, config_path):
        """Load configuration from file.

        Args:
            config_path: Path to configuration file
        """
        try:
            self.config = Config(config_path)
            logger.info(
                f"Configuration loaded from {config_path}: "
                f"{len(self.config.datasets)} datasets"
            )

            if not self.headless and hasattr(self, "config_status_var"):
                self.config_status_var.set(
                    f"Configuration loaded: {len(self.config.datasets)} datasets"
                )
                self.run_analysis_btn.config(state=tk.NORMAL)
                self._add_result_text(f"Configuration loaded from {config_path}")
                self.status_var.set("Configuration loaded successfully")

                # Update integrated charge information
                self._update_integrated_charge_info()

        except Exception as e:
            error_msg = f"Failed to load configuration: {str(e)}"
            logger.error(error_msg)
            if not self.headless and hasattr(self, "status_var"):
                messagebox.showerror("Error", error_msg)
                self.status_var.set("Error loading configuration")
            else:
                raise

    def _create_gui(self):
        """Create the main GUI interface."""
        if self.is_standalone:
            self.root = tk.Tk()
        else:
            self.root = tk.Toplevel(self.parent)

        # Create the BooleanVar after root exists
        self.save_total_signal_data = tk.BooleanVar(value=False)

        # Configure window
        self.root.title("AgeingAnalysis - FIT Detector Toolkit")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)

        # Create menu bar
        self._create_menu_bar()

        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create analysis tab
        self._create_analysis_tab()

        # Create status bar
        self._create_status_bar()

        # Set up window closing
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        logger.info("GUI interface created")

    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Config...", command=self._load_config_file)
        file_menu.add_command(
            label="Config Generator...", command=self._open_config_generator
        )
        file_menu.add_separator()
        file_menu.add_command(label="Load Results...", command=self._load_results_file)
        file_menu.add_separator()
        file_menu.add_command(label="Save Results...", command=self._save_results)
        file_menu.add_command(label="Export to CSV...", command=self._export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)

        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(
            label="Run Full Analysis", command=self._run_full_analysis
        )
        analysis_menu.add_separator()
        analysis_menu.add_command(
            label="Parse Data Only", command=self._parse_data_only
        )
        analysis_menu.add_command(
            label="Fit Gaussians Only", command=self._fit_gaussians_only
        )

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _create_analysis_tab(self):
        """Create the analysis tab."""
        self.analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_frame, text="Analysis")

        # Main content frame
        main_frame = ttk.Frame(self.analysis_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="FIT Detector Ageing Analysis",
            font=("TkDefaultFont", 20, "bold"),
        )
        title_label.pack(pady=(0, 20))

        # Configuration section
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 20))

        # Configuration buttons frame
        config_buttons_frame = ttk.Frame(config_frame)
        config_buttons_frame.pack(pady=5)

        ttk.Button(
            config_buttons_frame,
            text="Load Configuration File",
            command=self._load_config_file,
            style="Large.TButton",
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            config_buttons_frame,
            text="Config Generator",
            command=self._open_config_generator,
            style="Large.TButton",
        ).pack(side=tk.LEFT)

        self.config_status_var = tk.StringVar(value="No configuration loaded")
        ttk.Label(config_frame, textvariable=self.config_status_var).pack(pady=5)

        # Integrated charge information frame
        self.integrated_charge_frame = ttk.LabelFrame(
            config_frame, text="Integrated Charge", padding="10"
        )
        self.integrated_charge_frame.pack(fill=tk.X, pady=(10, 0))

        self.integrated_charge_status_var = tk.StringVar(
            value="No configuration loaded"
        )
        ttk.Label(
            self.integrated_charge_frame, textvariable=self.integrated_charge_status_var
        ).pack(side=tk.LEFT, pady=5)

        self.get_integrated_charge_btn = ttk.Button(
            self.integrated_charge_frame,
            text="Get Integrated Charge",
            command=self._get_integrated_charge,
            state=tk.DISABLED,
        )
        self.get_integrated_charge_btn.pack(side=tk.RIGHT, pady=5)

        # Analysis section
        analysis_frame = ttk.LabelFrame(main_frame, text="Analysis", padding="10")
        analysis_frame.pack(fill=tk.X, pady=(0, 20))

        # Analysis options frame
        options_frame = ttk.Frame(analysis_frame)
        options_frame.pack(fill=tk.X, pady=(0, 10))

        # Checkbox for saving total signal data
        self.save_total_signal_checkbox = ttk.Checkbutton(
            options_frame,
            text="Save total signal data in results",
            variable=self.save_total_signal_data,
            onvalue=True,
            offvalue=False,
        )
        self.save_total_signal_checkbox.pack(anchor=tk.W, pady=2)

        # Help text for the checkbox
        help_text = ttk.Label(
            options_frame,
            text="When checked, total signal will be included in the results file. "
            "This allows to analyse histograms in the visualization window.",
            font=("TkDefaultFont", 10),
            foreground="gray",
        )
        help_text.pack(anchor=tk.W, pady=(0, 5))

        button_frame = ttk.Frame(analysis_frame)
        button_frame.pack(pady=10)

        self.run_analysis_btn = ttk.Button(
            button_frame,
            text="Run Full Analysis",
            command=self._run_full_analysis,
            state=tk.DISABLED,
            style="Large.TButton",
        )
        self.run_analysis_btn.pack(side=tk.LEFT, padx=10)

        ttk.Button(
            button_frame,
            text="Load Existing Results",
            command=self._load_results_file,
            style="Large.TButton",
        ).pack(side=tk.LEFT, padx=10)

        self.viz_btn = ttk.Button(
            button_frame,
            text="Open Visualization",
            command=self._open_visualization,
            state=tk.DISABLED,
            style="Large.TButton",
        )
        self.viz_btn.pack(side=tk.LEFT, padx=10)

        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True)

        self.results_text = tk.Text(results_frame, height=10, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(
            results_frame, orient=tk.VERTICAL, command=self.results_text.yview
        )
        self.results_text.configure(yscrollcommand=scrollbar.set)

        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _open_visualization(self):
        """Open the visualization window."""
        try:
            if (
                self.visualization_window is None
                or not hasattr(self.visualization_window, "window")
                or not self.visualization_window.window.winfo_exists()
            ):
                # Create new visualization window
                results_data = None
                if self.results_path:
                    # Load results from file
                    results_data = load_results(self.results_path)
                elif self.config:
                    # Use current config data with checkbox setting
                    results_data = self.config.to_dict(
                        include_total_signal_data=self.save_total_signal_data.get()
                    )

                self.visualization_window = AgeingVisualizationWindow(
                    self.root, results_data
                )
                self.status_var.set("Visualization window opened")
            else:
                # Window exists, just bring it to front
                self.visualization_window.show()
                self.status_var.set("Visualization window brought to front")

        except Exception as e:
            error_msg = f"Failed to open visualization: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)

    def _enable_visualization_button(self):
        """Enable the visualization button."""
        if hasattr(self, "viz_btn"):
            self.viz_btn.config(state=tk.NORMAL)

    def _update_integrated_charge_info(self):
        """Update the integrated charge information display."""
        if not self.config or not hasattr(self, "integrated_charge_status_var"):
            return

        # Check if integrated charge is available in the config
        has_integrated_charge = self._check_integrated_charge_availability()

        if has_integrated_charge:
            self.integrated_charge_status_var.set(
                "✅ Integrated charge data is available"
            )
            self.get_integrated_charge_btn.config(state=tk.DISABLED)
        else:
            self.integrated_charge_status_var.set(
                "❌ Integrated charge data is not available"
            )
            self.get_integrated_charge_btn.config(state=tk.NORMAL)

    def _check_integrated_charge_availability(self) -> bool:
        """Check if integrated charge is available in the current config.

        Returns:
            True if integrated charge is available for all datasets, False otherwise.
        """
        if not self.config or not self.config.datasets:
            return False

        # Check if all datasets have integrated charge data
        for dataset in self.config.datasets:
            # Check if any module in the dataset has integrated charge data
            has_integrated_charge = False
            for module in dataset.modules:
                if (
                    hasattr(module, "integrated_charge_data")
                    and module.integrated_charge_data is not None
                ):
                    has_integrated_charge = True
                    break

            if not has_integrated_charge:
                return False

        return True

    def _get_integrated_charge(self):
        """Handle the Get Integrated Charge button click."""
        # TODO: Implement integrated charge calculation for
        # configs without integrated charge data

        messagebox.showinfo(
            "Get Integrated Charge",
            "Integrated charge calculation feature is not yet implemented.\n\n"
            "This feature will allow you to calculate integrated charge values "
            "for configurations that don't have integrated charge data available.",
        )

    def _create_status_bar(self):
        """Create status bar at the bottom."""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2),
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _load_config_file(self):
        """Load a configuration file via file dialog."""
        try:
            file_path = filedialog.askopenfilename(
                title="Load Configuration File",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )

            if file_path:
                self._load_config(file_path)

        except Exception as e:
            error_msg = f"Failed to load configuration: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
            self.status_var.set("Error loading configuration")

    def _open_config_generator(self):
        """Open the configuration generator in a new window."""
        try:
            # Create new window for config generator
            config_window = tk.Toplevel(self.root)
            config_window.title("Configuration Generator")
            config_window.geometry("1000x800")
            config_window.minsize(800, 600)

            # Center the window
            config_window.update_idletasks()
            x = (config_window.winfo_screenwidth() // 2) - (
                config_window.winfo_width() // 2
            )
            y = (config_window.winfo_screenheight() // 2) - (
                config_window.winfo_height() // 2
            )
            config_window.geometry(f"+{x}+{y}")

            # Set window icon (if available)
            if hasattr(self.root, "iconbitmap"):
                try:
                    config_window.iconbitmap(self.root.iconbitmap())
                except TclError:
                    pass  # Icon not available, continue without it

            # Create the config generator widget
            ConfigGeneratorWidget(config_window)

            # Handle window closing
            def on_config_window_close():
                config_window.destroy()

            config_window.protocol("WM_DELETE_WINDOW", on_config_window_close)

            # Make window modal
            config_window.transient(self.root)
            config_window.grab_set()

            # Focus on the new window
            config_window.focus_set()

            logger.info("Config generator window opened")

        except Exception as e:
            error_msg = f"Failed to open config generator: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
            self.status_var.set("Error opening config generator")

    def _load_results_file(self):
        """Load an existing results file."""
        try:
            file_path = filedialog.askopenfilename(
                title="Load Results File",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )

            if file_path:
                results = load_results(file_path)
                self._display_results(results)
                self.results_path = file_path

                # Enable visualization button
                self._enable_visualization_button()

                self.status_var.set("Results loaded successfully")

        except Exception as e:
            error_msg = f"Failed to load results: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
            self.status_var.set("Error loading results")

    def _prompt_save_results(self):
        """Prompt user to save analysis results."""
        try:
            # Ask user if they want to save results
            response = messagebox.askyesno(
                "Save Results",
                "Analysis completed successfully!\n\n"
                "Would you like to save the results?",
                icon=messagebox.QUESTION,
            )

            if response:
                self._save_results()
            else:
                self.status_var.set("Analysis completed - Results not saved")

        except Exception as e:
            error_msg = f"Error prompting for save: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)

    def _save_results(self):
        """Save current results to file."""
        if not self.config:
            messagebox.showwarning("Warning", "No analysis results to save")
            return

        try:
            # Generate default filename with timestamp
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"ageing_analysis_results_{timestamp}.json"

            # Propose default path in ageing_analysis_results directory
            default_path = Path("ageing_analysis_results") / default_filename

            file_path = filedialog.asksaveasfilename(
                title="Save Results",
                defaultextension=".json",
                initialfile=default_filename,
                initialdir=str(default_path.parent),
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )

            if file_path:
                saved_path = save_results(self.config, file_path)
                self.results_path = saved_path
                self._add_result_text(f"Results saved to {saved_path}")
                self.status_var.set("Results saved successfully")

        except Exception as e:
            error_msg = f"Failed to save results: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)

    def _export_csv(self):
        """Export results to CSV format."""
        if not self.config:
            messagebox.showwarning("Warning", "No analysis results to export")
            return

        try:
            from .utils import export_results_csv

            file_path = filedialog.asksaveasfilename(
                title="Export to CSV",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            )

            if file_path:
                results_dict = self.config.to_dict()
                export_results_csv(results_dict, file_path)
                self._add_result_text(f"Results exported to {file_path}")
                self.status_var.set("Results exported successfully")

        except Exception as e:
            error_msg = f"Failed to export to CSV: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)

    def _run_full_analysis(self):
        """Run the complete analysis pipeline."""
        if not self.config:
            messagebox.showwarning("Warning", "Please load a configuration file first")
            return

        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress = ProgressWindow(progress_window, on_complete=self._analysis_complete)

        # Start analysis
        progress.start_analysis(self._perform_analysis, progress)

    def _perform_analysis(self, progress):
        """Perform the actual analysis with progress reporting."""
        try:
            progress.add_log_message("Starting FIT detector ageing analysis...")
            progress.update_progress(10, "Parsing data files...")

            # Step 1: Parse data for all datasets
            for i, dataset in enumerate(self.config.datasets):
                progress.add_log_message(f"Parsing data for dataset {dataset.date}...")
                parser = DataParser(
                    dataset,
                    debug_mode=self.debug_mode,
                    prominence_percent=self.prominence_percent,
                    peak_merge_threshold=self.peak_merge_threshold,
                )
                parser.process_all_files()
                progress.update_progress(
                    10 + (i + 1) / len(self.config.datasets) * 29,
                    f"Parsed dataset {dataset.date}",
                )

            progress.update_progress(40, "Fitting Gaussian distributions...")

            # Step 2: Fit Gaussians for all datasets
            for i, dataset in enumerate(self.config.datasets):
                progress.add_log_message(
                    f"Fitting Gaussians for dataset {dataset.date}..."
                )
                gaussian_service = GaussianFitService(
                    dataset, debug_mode=self.debug_mode
                )
                gaussian_service.process_all_modules()
                progress.update_progress(
                    40 + (i + 1) / len(self.config.datasets) * 19,
                    f"Fitted Gaussians for {dataset.date}",
                )

            progress.update_progress(60, "Calculating reference means...")

            # Step 3: Calculate reference means for all datasets
            progress.add_log_message("Calculating reference means...")
            for i, dataset in enumerate(self.config.datasets):
                progress.add_log_message(
                    f"Calculating reference means for {dataset.date}..."
                )
                ref_service = ReferenceChannelService(dataset)
                ref_service.calculate_reference_means()
                progress.add_log_message(f"Reference means for {dataset.date} set")
                progress.update_progress(
                    60 + (i + 1) / len(self.config.datasets) * 9,
                    f"Calculated reference means for {dataset.date}",
                )

            progress.update_progress(70, "Calculating ageing factors...")

            # Step 4: Calculate ageing factors for all datasets
            for i, dataset in enumerate(self.config.datasets):
                progress.add_log_message(
                    f"Calculating ageing factors for {dataset.date}..."
                )
                ageing_service = AgeingCalculationService(dataset)
                ageing_service.calculate_ageing_factors()
                progress.update_progress(
                    70 + (i + 1) / len(self.config.datasets) * 19,
                    f"Calculated ageing factors for {dataset.date}",
                )

            progress.update_progress(90, "Normalizing data...")

            # Step 5: Normalize data
            progress.add_log_message("Normalizing ageing factors...")
            normalizer = DataNormalizer(self.config)
            normalizer.normalize_data()

            progress.update_progress(100, "Analysis completed!")
            progress.add_log_message("Analysis completed successfully!")

        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            logger.error(error_msg)
            progress.add_log_message(error_msg)
            raise

    def run_headless_analysis(self, output_path=None):
        """Run analysis in headless mode without GUI.

        Args:
            output_path: Optional path to save results (default: auto-generated)

        Returns:
            str: Path to the saved results file
        """
        if not self.config:
            raise ValueError("No configuration loaded. Please provide a config file.")

        if not self.config.datasets:
            raise ValueError(
                "No valid datasets found in configuration. "
                "Please check your config file and data paths."
            )

        logger.info("Starting headless analysis...")

        try:
            # Step 1: Parse data for all datasets
            logger.info("Parsing data files...")
            for i, dataset in enumerate(self.config.datasets):
                logger.info(f"Parsing data for dataset {dataset.date}...")
                parser = DataParser(
                    dataset,
                    debug_mode=self.debug_mode,
                    prominence_percent=self.prominence_percent,
                    peak_merge_threshold=self.peak_merge_threshold,
                )
                parser.process_all_files()
                logger.info(
                    f"Parsed dataset {dataset.date} ({i+1}/{len(self.config.datasets)})"
                )

            # Step 2: Fit Gaussians for all datasets
            logger.info("Fitting Gaussian distributions...")
            for i, dataset in enumerate(self.config.datasets):
                logger.info(f"Fitting Gaussians for dataset {dataset.date}...")
                gaussian_service = GaussianFitService(
                    dataset, debug_mode=self.debug_mode
                )
                gaussian_service.process_all_modules()
                logger.info(
                    f"Fitted Gaussians for {dataset.date} "
                    f"({i+1}/{len(self.config.datasets)})"
                )

            # Step 3: Calculate reference means for all datasets
            logger.info("Calculating reference means...")
            for i, dataset in enumerate(self.config.datasets):
                logger.info(
                    f"Calculating reference means for dataset {dataset.date}..."
                )
                ref_service = ReferenceChannelService(dataset)
                (
                    ref_gaussian_mean,
                    ref_weighted_mean,
                ) = ref_service.calculate_reference_means()
                dataset.set_reference_means(ref_gaussian_mean, ref_weighted_mean)
                logger.info(
                    f"Calculated reference means for {dataset.date} "
                    f"({i+1}/{len(self.config.datasets)})"
                )

            # Step 4: Calculate ageing factors for all datasets
            logger.info("Calculating ageing factors...")
            for i, dataset in enumerate(self.config.datasets):
                logger.info(f"Calculating ageing factors for dataset {dataset.date}...")
                ageing_service = AgeingCalculationService(dataset)
                ageing_service.calculate_ageing_factors()
                logger.info(
                    f"Calculated ageing factors for {dataset.date} "
                    f"({i+1}/{len(self.config.datasets)})"
                )

            # Step 5: Normalize ageing factors
            logger.info("Normalizing ageing factors...")
            normalizer = DataNormalizer(self.config)
            normalizer.normalize_all_ageing_factors()

            # Step 6: Save results
            logger.info("Saving results...")
            if output_path is None:
                # Generate default filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_filename = f"ageing_analysis_results_{timestamp}.json"
                output_path = f"ageing_analysis_results/{default_filename}"

            results_path = save_results(
                self.config,
                output_path=output_path,
                include_total_signal_data=True,  # Default to True for headless mode
            )

            # Print summary
            self._print_analysis_summary()

            logger.info(
                f"Analysis completed successfully. Results saved to: {results_path}"
            )
            return results_path

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise

    def _print_analysis_summary(self):
        """Print analysis summary to console."""
        if not self.config:
            return

        print("\n" + "=" * 60)
        print("ANALYSIS RESULTS SUMMARY")
        print("=" * 60)

        datasets = self.config.datasets
        print(f"Number of datasets processed: {len(datasets)}")

        for i, dataset in enumerate(datasets):
            print(f"\nDataset {i+1}: {dataset.date}")
            print(f"  Modules: {len(dataset.modules)}")

            total_channels = sum(len(module.channels) for module in dataset.modules)
            print(f"  Total channels: {total_channels}")

            # Print some statistics if available
            if dataset.modules:
                module = dataset.modules[0]
                if module.channels:
                    channel = module.channels[0]
                    if (
                        hasattr(channel, "ageing_factor")
                        and channel.ageing_factor is not None
                    ):
                        ageing_factors = [
                            ch.ageing_factor
                            for mod in dataset.modules
                            for ch in mod.channels
                            if hasattr(ch, "ageing_factor")
                            and ch.ageing_factor is not None
                        ]
                        if ageing_factors:
                            avg_ageing = sum(ageing_factors) / len(ageing_factors)
                            print(f"  Average ageing factor: {avg_ageing: .4f}")

        print(f"\nResults saved to: {self.results_path}")
        print("=" * 60)

    def _analysis_complete(self):
        """Handle analysis completion."""
        try:
            # Display results first
            results_dict = self.config.to_dict(
                include_total_signal_data=self.save_total_signal_data.get()
            )
            self._display_results(results_dict)

            # Enable visualization button
            self._enable_visualization_button()

            # Prompt user to save results
            self._prompt_save_results()

            self.status_var.set("Analysis completed successfully")

        except Exception as e:
            error_msg = f"Error handling analysis completion: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)

    def _parse_data_only(self):
        """Parse data files only."""
        if not self.config:
            messagebox.showwarning("Warning", "Please load a configuration file first")
            return

        try:
            for dataset in self.config.datasets:
                parser = DataParser(
                    dataset,
                    debug_mode=self.debug_mode,
                    prominence_percent=self.prominence_percent,
                    peak_merge_threshold=self.peak_merge_threshold,
                )
                parser.process_all_files()

            self._add_result_text("Data parsing completed successfully")
            self.status_var.set("Data parsing completed")

        except Exception as e:
            error_msg = f"Data parsing failed: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)

    def _fit_gaussians_only(self):
        """Fit Gaussians only."""
        if not self.config:
            messagebox.showwarning("Warning", "Please load a configuration file first")
            return

        try:
            for dataset in self.config.datasets:
                gaussian_service = GaussianFitService(
                    dataset, debug_mode=self.debug_mode
                )
                gaussian_service.process_all_modules()

            self._add_result_text("Gaussian fitting completed successfully")
            self.status_var.set("Gaussian fitting completed")

        except Exception as e:
            error_msg = f"Gaussian fitting failed: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)

    def _display_results(self, results_dict):
        """Display analysis results in the results text area."""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)

        # Summary information
        datasets = results_dict.get("datasets", [])
        self.results_text.insert(tk.END, "Analysis Results Summary\n")
        self.results_text.insert(tk.END, "========================\n\n")
        self.results_text.insert(tk.END, f"Number of datasets: {len(datasets)}\n\n")

        for dataset in datasets:
            date = dataset.get("date", "unknown")
            modules = dataset.get("modules", [])
            self.results_text.insert(tk.END, f"Dataset: {date}\n")
            self.results_text.insert(tk.END, f"  Modules: {len(modules)}\n")

            total_channels = sum(len(m.get("channels", [])) for m in modules)
            self.results_text.insert(tk.END, f"  Total channels: {total_channels}\n\n")

        self.results_text.config(state=tk.DISABLED)

    def _add_result_text(self, text):
        """Add text to the results area."""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.insert(tk.END, f"{text}\n")
        self.results_text.see(tk.END)
        self.results_text.config(state=tk.DISABLED)

    def _show_about(self):
        """Show about dialog."""
        about_text = """
FIT Detector Ageing Analysis Module

A comprehensive tool for analyzing ageing effects in FIT detector data.

Features:
• Data parsing and preprocessing
• Gaussian fitting and statistical analysis
• Reference channel calculations
• Ageing factor computation and normalization
• Interactive visualization and plotting

Version: 1.0.0
"""
        messagebox.showinfo("About", about_text)

    def _on_closing(self):
        """Handle window closing."""
        logger.info("AgeingAnalysis application closing")
        if self.root:
            self.root.destroy()
        if self.is_standalone:
            sys.exit(0)

    def run(self, output_path=None):
        """Run the application.

        Args:
            output_path: Optional path to save results (for headless mode)
        """
        try:
            logger.info("Starting AgeingAnalysis application...")

            if self.headless:
                # Run in headless mode
                return self.run_headless_analysis(output_path)
            else:
                # Create GUI
                self._create_gui()

                # Start main loop
                if self.is_standalone:
                    self.root.mainloop()
                else:
                    # For integration with launcher, just show the window
                    self.root.focus_set()

        except Exception as e:
            logger.error(f"Error running AgeingAnalysis application: {e}")
            raise


def main():
    """Execute the application in standalone mode."""
    parser = argparse.ArgumentParser(
        description="FIT Detector Ageing Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with GUI (default)
  python -m ageing_analysis.main

  # Run headless analysis with config file
  python -m ageing_analysis.main --headless --config config.json

  # Run headless analysis with custom output path
  python -m ageing_analysis.main --headless --config config.json --output results.json
        """,
    )

    parser.add_argument(
        "--headless", action="store_true", help="Run without GUI (headless mode)"
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to configuration file (required for headless mode)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output path for results (optional, auto-generated if not provided)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug mode - plots debug plots in various stages of the analysis",
    )

    parser.add_argument(
        "--prominence-percent",
        "-p",
        type=float,
        help="The prominence percentage to use for peak detection",
        default=15,
    )

    parser.add_argument(
        "--peak-merge-threshold",
        "-m",
        type=int,
        help="The threshold for merging peaks when the bases are this close",
        default=5,
    )

    args = parser.parse_args()

    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate arguments
    if args.headless and not args.config:
        parser.error("--config is required when running in headless mode")

    try:
        app = AgeingAnalysisApp(
            headless=args.headless,
            config_path=args.config,
            debug_mode=args.debug,
            prominence_percent=args.prominence_percent,
            peak_merge_threshold=args.peak_merge_threshold,
        )

        if args.headless:
            result_path = app.run(output_path=args.output)
            print("\nAnalysis completed successfully!")
            print(f"Results saved to: {result_path}")
        else:
            app.run()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
