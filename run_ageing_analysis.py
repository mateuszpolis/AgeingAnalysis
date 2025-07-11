#!/usr/bin/env python3
"""Launcher script for AgeingAnalysis application."""

if __name__ == "__main__":
    try:
        from ageing_analysis import AgeingAnalysisApp

        print("Starting AgeingAnalysis application...")
        app = AgeingAnalysisApp()
        app.run()

    except ImportError as e:
        print(f"Error: Could not import AgeingAnalysis module: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r requirements.txt")

    except Exception as e:
        print(f"Error starting application: {e}")
