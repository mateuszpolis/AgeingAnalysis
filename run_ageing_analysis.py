#!/usr/bin/env python3
"""Launcher script for AgeingAnalysis application."""

import argparse
import sys


def main():
    """Launch the main application."""
    parser = argparse.ArgumentParser(
        description="FIT Detector Ageing Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with GUI (default)
  python run_ageing_analysis.py

  # Run headless analysis with config file
  python run_ageing_analysis.py --headless --config config.json

  # Run headless analysis with custom output path
  python run_ageing_analysis.py --headless --config config.json --output results.json
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

    # Validate arguments
    if args.headless and not args.config:
        parser.error("--config is required when running in headless mode")

    try:
        from ageing_analysis import AgeingAnalysisApp

        if not args.headless:
            print("Starting AgeingAnalysis application...")

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

    except ImportError as e:
        print(f"Error: Could not import AgeingAnalysis module: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)

    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
