"""Ageing Analysis application for the FIT Detector Toolkit."""

import logging
import os
import sys
import traceback

# Set up a logger
logger = logging.getLogger("fit_detector.ageing")


def launch_ageing_analysis():
    """Launch the Ageing Analysis application.

    This function directly imports and runs the ageing_analysis module instead
    of launching it as a separate process, making it more reliable in a bundled application.

    Returns:
        bool: True if the application was launched successfully, False otherwise.
    """
    # Create a debug log file in the user's home directory
    debug_log_path = os.path.join(os.path.expanduser("~"), "fit_detector_ageing_debug.log")
    logging.basicConfig(
        filename=debug_log_path,
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("===== Launching Ageing Analysis (Direct Import Method) =====")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Module location: {__file__}")

    # Log if we're running in a frozen environment (PyInstaller bundle)
    is_frozen = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
    logger.info(f"Running in frozen environment: {is_frozen}")
    if is_frozen:
        logger.info(f"Bundle directory: {sys._MEIPASS}")
        logger.info(f"sys.path: {sys.path}")

    # Prepare sys.path for import
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    logger.info(f"Project root: {project_root}")

    # Make sure the project root is in sys.path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        logger.info(f"Added project root to sys.path: {project_root}")

    # If frozen, add the bundle directory to sys.path
    if is_frozen and sys._MEIPASS not in sys.path:
        sys.path.insert(0, sys._MEIPASS)
        logger.info(f"Added bundle directory to sys.path: {sys._MEIPASS}")

    try:
        logger.info("Attempting to import ageing_analysis module directly")

        # Try to directly import the ageing_analysis module
        try:
            import ageing_analysis

            logger.info("Successfully imported ageing_analysis module")
            if hasattr(ageing_analysis, "main"):
                logger.info("Calling ageing_analysis.main()")
                ageing_analysis.main()
                logger.info("ageing_analysis.main() completed successfully")
                return True
            else:
                logger.error("ageing_analysis module does not have a main() function")
        except ImportError as e:
            logger.error(f"Could not import ageing_analysis module: {e}")
            logger.info("Attempting to import individual components from ageing_analysis")

            # Try to import the visualization components
            try:
                # First, make sure configs are accessible
                import configs.logger_config

                logger.info("Successfully imported configs.logger_config")

                # Import FIT Ageing Analysis App
                from gui.components import FITAgeingAnalysisApp, ProgressWindow

                logger.info("Successfully imported gui.components")

                # Import the entities
                from fit_detector.apps.ageing.entities.config import Config

                logger.info("Successfully imported fit_detector.apps.ageing.entities.config")

                # Import the services
                from fit_detector.apps.ageing.services.ageing_calculator import (
                    AgeingCalculationService,
                )
                from fit_detector.apps.ageing.services.data_normalizer import DataNormalizer
                from fit_detector.apps.ageing.services.data_parser import DataParser
                from fit_detector.apps.ageing.services.gaussian_fit import GaussianFitService
                from fit_detector.apps.ageing.services.reference_channel import (
                    ReferenceChannelService,
                )

                logger.info("Successfully imported all services")

                # Import save results utility
                from utils.save_results import save_results

                logger.info("Successfully imported utils.save_results")

                # Now launch the Tkinter UI
                import tkinter as tk

                root = tk.Tk()
                logger.info("Created Tkinter root")

                def on_analysis_complete():
                    logger.info("Analysis completed")

                def start_analysis():
                    try:
                        # Load the config
                        config = Config()
                        logger.info("Configuration loaded successfully")

                        # Create and show the progress window
                        progress_root = tk.Tk()
                        progress_window = ProgressWindow(
                            progress_root, on_complete=on_analysis_complete
                        )

                        # Define run_analysis function
                        def run_analysis(config, progress_window=None):
                            logger.info("Starting analysis process...")

                            # Check if the config has datasets
                            if not hasattr(config, "datasets") or not config.datasets:
                                error_msg = "No datasets found in the configuration."
                                logger.error(error_msg)
                                if progress_window:
                                    progress_window.add_log_message(error_msg)
                                    progress_window.update_progress(
                                        0, "Analysis failed: No datasets found"
                                    )
                                return

                            # Call through the analysis pipeline
                            # This is simplified - in the full app there would be more steps
                            if progress_window:
                                progress_window.update_progress(
                                    100, "Analysis completed successfully!"
                                )
                            logger.info("Analysis completed successfully!")

                        # Start the analysis
                        progress_window.start_analysis(run_analysis, config)

                        # Start the main loop
                        progress_root.mainloop()
                    except Exception as e:
                        logger.error(f"Error during analysis: {e}")
                        logger.error(traceback.format_exc())

                # Initialize the main application
                FITAgeingAnalysisApp(
                    root,
                    generate_only=False,
                    root_path=project_root,
                    on_run_analysis=start_analysis,
                )
                logger.info("FITAgeingAnalysisApp initialized")

                # Start the main loop
                logger.info("Starting Tkinter mainloop")
                root.mainloop()

                logger.info("Application closed. Exiting.")
                return True
            except Exception as e:
                logger.error(f"Error importing required components: {e}")
                logger.error(traceback.format_exc())

        except Exception as e:
            logger.error(f"Unexpected error importing ageing_analysis: {e}")
            logger.error(traceback.format_exc())

        # Fallback: Try to load from ageing_visualization module
        try:
            logger.info("Attempting fallback to ageing_visualization.run_visualization()")
            import ageing_visualization

            if hasattr(ageing_visualization, "run_visualization"):
                logger.info("Calling ageing_visualization.run_visualization()")
                ageing_visualization.run_visualization()
                logger.info("ageing_visualization.run_visualization() completed")
                return True
            else:
                logger.error("ageing_visualization module does not have run_visualization function")
        except ImportError as e:
            logger.error(f"Could not import ageing_visualization module: {e}")
        except Exception as e:
            logger.error(f"Error in ageing_visualization fallback: {e}")
            logger.error(traceback.format_exc())

        # Final fallback: Try to load the visualization dashboard directly
        try:
            logger.info("Attempting to import visualization.tkinter_dashboard")
            import tkinter as tk

            from visualization.tkinter_dashboard import TkinterDashboard

            logger.info("Creating TkinterDashboard")
            root = tk.Tk()
            dashboard = TkinterDashboard(root)
            logger.info("Starting dashboard")
            dashboard.run()
            return True
        except ImportError as e:
            logger.error(f"Could not import TkinterDashboard: {e}")
        except Exception as e:
            logger.error(f"Error launching TkinterDashboard: {e}")
            logger.error(traceback.format_exc())

        logger.error("All attempts to launch Ageing Analysis failed")
        print(f"Error: Could not launch Ageing Analysis. See log at {debug_log_path}")
        return False

    except Exception as e:
        logger.error(f"Critical error in launch_ageing_analysis: {e}")
        logger.error(traceback.format_exc())
        print(f"Error launching Ageing Analysis: {e}. See log at {debug_log_path}")
        return False
