"""
Re-exports from ageing_visualization_tkinter.py for backward compatibility.
"""


def run_visualization(results_file=None):
    """
    Run the visualization dashboard with the given results file.

    Args:
        results_file: Path to a JSON file containing analysis results
    """
    import tkinter as tk

    from visualization.tkinter_dashboard import TkinterDashboard

    # Create a new Tkinter root window
    root = tk.Tk()

    # Create the dashboard
    dashboard = TkinterDashboard(root)

    # If a results file is specified, load it
    if results_file:
        print(f"Loading data from {results_file}")
        if not dashboard.load_from_json_file(results_file):
            print(f"Error loading JSON file: {results_file}")
            return 1

    # Start the Tkinter main loop
    dashboard.run()

    return 0
