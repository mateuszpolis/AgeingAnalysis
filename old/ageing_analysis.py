#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import time
import tkinter as tk

from configs.logger_config import logger, temp_log_file
from fit_detector.apps.ageing.entities.config import Config
from fit_detector.apps.ageing.services.ageing_calculator import AgeingCalculationService
from fit_detector.apps.ageing.services.data_normalizer import DataNormalizer
from fit_detector.apps.ageing.services.data_parser import DataParser
from fit_detector.apps.ageing.services.gaussian_fit import GaussianFitService
from fit_detector.apps.ageing.services.reference_channel import ReferenceChannelService
from gui.components import FITAgeingAnalysisApp, ProgressWindow
from utils.save_results import save_results


def run_analysis(config, progress_window=None):
    """Run the analysis process using the provided configuration.

    Args:
        config (Config): The configuration object containing the datasets to analyze.
        progress_window (ProgressWindow, optional): The progress window to update. Defaults to None.
    """
    logger.info("Starting analysis process...")

    # Check if the config has datasets
    if not hasattr(config, "datasets") or not config.datasets:
        error_msg = "No datasets found in the configuration. Cannot run analysis. "
        error_msg += (
            "This may be because the data directories specified in the configuration do not exist. "
        )
        error_msg += "Please check that the paths in your configuration "
        error_msg += "file are correct and that the data files exist."
        logger.error(error_msg)
        if progress_window:
            progress_window.add_log_message(error_msg)
            progress_window.update_progress(0, "Analysis failed: No datasets found")
        return

    # Create a list of steps to process
    analysis_steps = []

    # Add dataset-specific steps
    for dataset_index, dataset in enumerate(config.datasets):
        dataset_name = f"Dataset {dataset_index+1} ({dataset.date})"

        # Step 1: Parse data files
        analysis_steps.append(
            (
                f"Parsing data files for {dataset_name}",
                lambda d=dataset, name=dataset_name: parse_data_files(d, progress_window, name),
            )
        )

        # Step 2: Gaussian Fit and Weighted Mean Calculation
        analysis_steps.append(
            (
                f"Calculating Gaussian fits for {dataset_name}",
                lambda d=dataset, name=dataset_name: calculate_gaussian_fits(
                    d, progress_window, name
                ),
            )
        )

        # Step 3: Calculate Reference Means from the Reference Module
        analysis_steps.append(
            (
                f"Calculating reference means for {dataset_name}",
                lambda d=dataset, name=dataset_name: calculate_reference_means(
                    d, progress_window, name
                ),
            )
        )

        # Step 4: Ageing Factor Calculation
        analysis_steps.append(
            (
                f"Calculating ageing factors for {dataset_name}",
                lambda d=dataset, name=dataset_name: calculate_ageing_factors(
                    d, progress_window, name
                ),
            )
        )

    # Add final steps
    analysis_steps.append(
        ("Normalizing ageing factors", lambda: normalize_data(config, progress_window))
    )

    analysis_steps.append(("Saving results to file", lambda: save_data(config, progress_window)))

    # Process all steps with progress tracking
    for step_index, (step_description, step_function) in enumerate(analysis_steps):
        # Calculate progress as a percentage (0-100)
        progress = ((step_index) / len(analysis_steps)) * 100

        # Update progress window with current step
        if progress_window:
            progress_window.update_progress(progress, step_description)
            # Small delay to allow UI to update
            time.sleep(0.01)

        try:
            # Execute the step function
            step_function()
        except Exception as e:
            error_msg = f"Error during {step_description.lower()}: {e}"
            logger.error(error_msg)
            if progress_window:
                progress_window.add_log_message(error_msg)
            sys.exit(1)

    # Final step: Complete the analysis
    if progress_window:
        # Ensure we reach 100% at the end
        progress_window.update_progress(100, "Analysis completed successfully!")
        # Small delay to allow UI to update
        time.sleep(0.01)

    logger.info("Analysis completed successfully!")


def parse_data_files(dataset, progress_window, dataset_name):
    """Parse data files for a dataset."""
    data_parser = DataParser(dataset)
    data_parser.process_all_files()
    if progress_window:
        progress_window.add_log_message(f"Successfully parsed data files for {dataset_name}")
        # Small delay to allow UI to update
        time.sleep(0.01)


def calculate_gaussian_fits(dataset, progress_window, dataset_name):
    """Calculate Gaussian fits for a dataset."""
    gaussian_fit_service = GaussianFitService(dataset)
    gaussian_fit_service.process_all_modules()
    if progress_window:
        progress_window.add_log_message(f"Successfully calculated means for {dataset_name}")
        # Small delay to allow UI to update
        time.sleep(0.01)


def calculate_reference_means(dataset, progress_window, dataset_name):
    """Calculate reference means for a dataset."""
    reference_channel_service = ReferenceChannelService(dataset)
    reference_channel_service.calculate_reference_means()
    if progress_window:
        progress_window.add_log_message(
            f"Successfully calculated reference means for {dataset_name}"
        )
        # Small delay to allow UI to update
        time.sleep(0.01)


def calculate_ageing_factors(dataset, progress_window, dataset_name):
    """Calculate ageing factors for a dataset."""
    ageing_calculator = AgeingCalculationService(
        dataset,
        dataset.get_reference_gaussian_mean(),
        dataset.get_reference_weighted_mean(),
    )
    ageing_calculator.calculate_ageing_factors()
    if progress_window:
        progress_window.add_log_message(
            f"Successfully calculated ageing factors for {dataset_name}"
        )
        # Small delay to allow UI to update
        time.sleep(0.01)


def normalize_data(config, progress_window):
    """Normalize the data across all datasets."""
    data_normalizer = DataNormalizer(config=config)
    data_normalizer.normalize_data()
    if progress_window:
        progress_window.add_log_message("Successfully normalized ageing factors")
        # Small delay to allow UI to update
        time.sleep(0.01)


def save_data(config, progress_window):
    """Save the results to a file."""
    output_file = save_results(config)
    if progress_window:
        progress_window.add_log_message(f"Successfully saved results to {output_file}")
        # Small delay to allow UI to update
        time.sleep(0.01)


def on_analysis_complete():
    """Callback function to run when the analysis is complete."""
    logger.info("Analysis completed. You can close the progress window.")


def main():
    """Main entry point for the FIT Detector Ageing Analysis application."""
    parser = argparse.ArgumentParser(description="FIT Detector Ageing Analysis Program.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    # Setup the logger
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel("DEBUG")
    else:
        logger.setLevel("INFO")

    try:
        root_path = os.path.dirname(os.path.abspath(__file__))

        # Start the GUI for configuration generation
        def start_analysis():
            """Start the analysis process after configuration generation."""
            try:
                # Load the config
                config = Config()
                logger.info("Configuration loaded successfully.")

                # Create and show the progress window
                progress_root = tk.Tk()
                progress_window = ProgressWindow(progress_root, on_complete=on_analysis_complete)

                # Start the analysis
                progress_window.start_analysis(run_analysis, config)

                # Start the main loop
                progress_root.mainloop()
            except Exception as e:
                logger.error(f"Error during analysis: {e}")
                sys.exit(1)

        # Create and show the main application
        root = tk.Tk()
        # Initialize the main application
        FITAgeingAnalysisApp(
            root,
            generate_only=False,  # Always allow running analysis
            root_path=root_path,
            on_run_analysis=start_analysis,
        )
        root.mainloop()

        # The program will exit when the GUI is closed
        logger.info("Application closed. Exiting.")

    finally:
        print(f"Logs are saved in: {temp_log_file}")


if __name__ == "__main__":
    main()
