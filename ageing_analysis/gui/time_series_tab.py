"""Time Series Analysis Tab for Ageing Analysis Visualization."""

import logging
import re
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from ..services.integrated_charge_service import IntegratedChargeService

logger = logging.getLogger(__name__)


def _natural_sort_key(text):
    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1))
    return 0


class TimeSeriesTab:
    """Time Series Analysis Tab for Ageing Analysis Visualization."""

    def __init__(
        self,
        parent: tk.Widget,
        results_data: Optional[Dict[str, Any]],
        status_var: tk.StringVar,
    ):
        """Initialize the TimeSeriesTab.

        Args:
            parent: The parent tkinter widget that this tab belongs to
            results_data: The analysis results data to display
            status_var: The tkinter StringVar to display status messages
        """
        self.parent = parent
        self.results_data = results_data
        self.status_var = status_var
        self.frame = ttk.Frame(self.parent)
        self.channel_vars: Dict[str, tk.BooleanVar] = {}
        self.module_vars: Dict[str, tk.BooleanVar] = {}
        self.gaussian_var = tk.BooleanVar(value=True)
        self.weighted_var = tk.BooleanVar(value=False)
        self.x_axis_var = tk.StringVar(value="date")
        self._update_pending = False
        self.plot_data_info: Dict[Tuple[str, int], Dict[str, Any]] = {}
        self.tooltip_annotation = None
        self._create_layout()
        if results_data:
            self._process_data()

    def _create_layout(self):
        paned_window = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.control_frame = ttk.Frame(paned_window, width=350)
        paned_window.add(self.control_frame, weight=0)
        self.plot_frame = ttk.Frame(paned_window)
        paned_window.add(self.plot_frame, weight=1)
        self._create_control_panel()
        self._create_plot_panel()

    def _create_control_panel(self):
        # X-axis selection
        x_axis_frame = ttk.LabelFrame(
            self.control_frame, text="X-Axis Selection", padding="10"
        )
        x_axis_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        # Check if integrated charge is available
        self.integrated_charge_available = (
            IntegratedChargeService.is_integrated_charge_available(self.results_data)
        )

        if self.integrated_charge_available:
            ttk.Radiobutton(
                x_axis_frame,
                text="Date",
                variable=self.x_axis_var,
                value="date",
                command=self._update_plot,
            ).pack(anchor=tk.W)
            ttk.Radiobutton(
                x_axis_frame,
                text="Integrated Charge",
                variable=self.x_axis_var,
                value="integrated_charge",
                command=self._update_plot,
            ).pack(anchor=tk.W)
        else:
            ttk.Label(
                x_axis_frame,
                text="Date (Integrated charge not available)",
                foreground="gray",
            ).pack(anchor=tk.W)

        # Method selection
        method_frame = ttk.LabelFrame(
            self.control_frame, text="Reference Methods", padding="10"
        )
        method_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Checkbutton(
            method_frame,
            text="Gaussian Mean",
            variable=self.gaussian_var,
            command=self._update_plot,
        ).pack(anchor=tk.W)
        ttk.Checkbutton(
            method_frame,
            text="Weighted Mean",
            variable=self.weighted_var,
            command=self._update_plot,
        ).pack(anchor=tk.W)
        self.channel_frame = ttk.LabelFrame(
            self.control_frame, text="Channel Selection", padding="10"
        )
        self.channel_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        button_frame = ttk.Frame(self.channel_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(
            button_frame, text="Select All", command=self._select_all_channels
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            button_frame, text="Deselect All", command=self._deselect_all_channels
        ).pack(side=tk.LEFT, padx=5)
        self._create_scrollable_channel_frame()

    def _create_scrollable_channel_frame(self):
        canvas = tk.Canvas(self.channel_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            self.channel_frame, orient="vertical", command=canvas.yview
        )
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)

    def _create_plot_panel(self):
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()
        self._setup_empty_plot()
        self._setup_hover_events()

    def _setup_hover_events(self):
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("button_press_event", self._on_click)

    def _on_hover(self, event):
        if event.inaxes != self.ax:
            self._hide_tooltip()
            return
        closest_distance = float("inf")
        closest_point_info = None
        closest_x = None
        closest_y = None
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        x_range = xlim[1] - xlim[0]
        y_range = ylim[1] - ylim[0]
        use_integrated_charge = self.x_axis_var.get() == "integrated_charge"

        for line in self.ax.get_lines():
            xdata, ydata = line.get_data()
            if len(xdata) == 0:
                continue

            # Convert x values to numbers for distance calculation
            if use_integrated_charge:
                xdata_num = xdata  # Already numeric
            else:
                xdata_num = [
                    mdates.date2num(x) if hasattr(x, "year") else x for x in xdata
                ]

            event_x_num = event.xdata
            for i, (x_num, y) in enumerate(zip(xdata_num, ydata)):
                norm_x = (x_num - xlim[0]) / x_range if x_range > 0 else 0
                norm_y = (y - ylim[0]) / y_range if y_range > 0 else 0
                norm_event_x = (event_x_num - xlim[0]) / x_range if x_range > 0 else 0
                norm_event_y = (event.ydata - ylim[0]) / y_range if y_range > 0 else 0
                distance = (
                    (norm_x - norm_event_x) ** 2 + (norm_y - norm_event_y) ** 2
                ) ** 0.5
                if distance < closest_distance:
                    closest_distance = distance
                    closest_x = x_num
                    closest_y = y
                    point_key = (line.get_label(), i)
                    if point_key in self.plot_data_info:
                        closest_point_info = self.plot_data_info[point_key]
        proximity_threshold = 0.25
        if closest_distance < proximity_threshold and closest_point_info:
            self._show_tooltip(closest_x, closest_y, closest_point_info)
        else:
            self._hide_tooltip()

    def _on_click(self, event):
        self._hide_tooltip()

    def _show_tooltip(self, x, y, info):
        if self.tooltip_annotation:
            self.tooltip_annotation.remove()
        tooltip_text = (
            f"PM: {info['pm']}\n"
            f"Channel: {info['channel']}\n"
            f"Method: {info['method']}\n"
            f"Date: {info['date']}\n"
            f"Value: {info['value']:.4f}"
        )
        self.tooltip_annotation = self.ax.annotate(
            tooltip_text,
            xy=(x, y),
            xytext=(20, 20),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.8),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
        )
        self.canvas.draw_idle()

    def _hide_tooltip(self):
        if self.tooltip_annotation:
            self.tooltip_annotation.remove()
            self.tooltip_annotation = None
            self.canvas.draw_idle()

    def _setup_empty_plot(self):
        self.ax.clear()
        self.ax.text(
            0.5,
            0.5,
            "Load analysis results to view ageing data\n\nFile → Load Results...",
            horizontalalignment="center",
            verticalalignment="center",
            transform=self.ax.transAxes,
            fontsize=14,
            alpha=0.6,
        )
        self.ax.set_title("Ageing Analysis - Time Series")
        self.fig.subplots_adjust(bottom=0.35, right=0.95, top=0.9, left=0.12)
        self.plot_data_info.clear()
        self._hide_tooltip()
        self.canvas.draw_idle()

    def _process_data(self):
        if not self.results_data:
            return
        try:
            self.channel_vars.clear()
            self.module_vars.clear()
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self._populate_channel_selection()
            self._update_plot()
        except Exception as e:
            error_msg = f"Error processing data: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg, parent=self.frame)

    def _populate_channel_selection(self):
        datasets = self.results_data.get("datasets", [])
        if not datasets:
            return
        modules_channels = {}
        for dataset in datasets:
            for module in dataset.get("modules", []):
                module_id = module.get("identifier", "unknown")
                if module_id not in modules_channels:
                    modules_channels[module_id] = set()
                for channel in module.get("channels", []):
                    channel_name = channel.get("name", "unknown")
                    modules_channels[module_id].add(channel_name)
        for module_id, channels in modules_channels.items():
            sorted_channels = sorted(channels, key=_natural_sort_key)
            self._create_module_section(module_id, sorted_channels)

    def _create_module_section(self, module_id: str, channels: List[str]):
        module_frame = ttk.LabelFrame(
            self.scrollable_frame, text=f"Module {module_id}", padding="5"
        )
        module_frame.pack(fill=tk.X, padx=5, pady=2)
        module_var = tk.BooleanVar()
        self.module_vars[module_id] = module_var

        def toggle_callback(mid: str = module_id) -> None:
            self._toggle_module(mid)

        module_cb = ttk.Checkbutton(
            module_frame,
            text=f"Select All ({module_id})",
            variable=module_var,
            command=toggle_callback,
        )
        module_cb.pack(anchor=tk.W)
        ttk.Separator(module_frame, orient="horizontal").pack(fill=tk.X, pady=2)
        channels_frame = ttk.Frame(module_frame)
        channels_frame.pack(fill=tk.X)
        for i, channel_name in enumerate(channels):
            channel_key = f"{module_id}_{channel_name}"
            channel_var = tk.BooleanVar()
            self.channel_vars[channel_key] = channel_var
            cb = ttk.Checkbutton(
                channels_frame,
                text=channel_name,
                variable=channel_var,
                command=self._on_channel_change,
            )
            cb.grid(row=i // 4, column=i % 4, sticky=tk.W, padx=5, pady=1)

    def _toggle_module(self, module_id: str):
        module_var = self.module_vars[module_id]
        state = module_var.get()
        for channel_key, channel_var in self.channel_vars.items():
            if channel_key.startswith(f"{module_id}_"):
                channel_var.set(state)
        self._update_plot()

    def _on_channel_change(self):
        self._update_module_state()
        self._update_plot()

    def _update_module_state(self):
        for module_id in self.module_vars:
            module_channels = [
                cv
                for ck, cv in self.channel_vars.items()
                if ck.startswith(f"{module_id}_")
            ]
            if not module_channels:
                continue
            all_selected = all(cv.get() for cv in module_channels)
            any_selected = any(cv.get() for cv in module_channels)
            module_var = self.module_vars[module_id]
            if all_selected:
                module_var.set(True)
            elif any_selected:
                pass
            else:
                module_var.set(False)

    def _select_all_channels(self):
        for channel_var in self.channel_vars.values():
            channel_var.set(True)
        for module_var in self.module_vars.values():
            module_var.set(True)
        self._update_plot()

    def _deselect_all_channels(self):
        for channel_var in self.channel_vars.values():
            channel_var.set(False)
        for module_var in self.module_vars.values():
            module_var.set(False)
        self._update_plot()

    def _get_selected_channels(self) -> List[str]:
        return [
            channel_key for channel_key, var in self.channel_vars.items() if var.get()
        ]

    def _update_plot(self):
        if self._update_pending:
            return
        self._update_pending = True
        self.frame.after_idle(self._do_update_plot)

    def _do_update_plot(self):
        self._update_pending = False
        if not self.results_data:
            self._setup_empty_plot()
            return
        try:
            selected_channels = self._get_selected_channels()
            show_gaussian = self.gaussian_var.get()
            show_weighted = self.weighted_var.get()
            use_integrated_charge = self.x_axis_var.get() == "integrated_charge"

            if not selected_channels or (not show_gaussian and not show_weighted):
                self.ax.clear()
                if not selected_channels:
                    message = "Select channels to display data"
                else:
                    message = (
                        "Select at least one reference method\n"
                        "(Gaussian Mean or Weighted Mean)"
                    )
                self.ax.text(
                    0.5,
                    0.5,
                    message,
                    horizontalalignment="center",
                    verticalalignment="center",
                    transform=self.ax.transAxes,
                    fontsize=14,
                    alpha=0.6,
                )
                self.ax.set_title("Ageing Analysis - Time Series")
                self.canvas.draw()
                return
            self.ax.clear()
            if hasattr(self.ax, "legend_") and self.ax.legend_:
                self.ax.legend_.remove()
            self.plot_data_info.clear()
            self._hide_tooltip()
            datasets = self.results_data.get("datasets", [])
            channel_data = {}
            for dataset in datasets:
                date_str = dataset.get("date", "unknown")

                # Get x-axis value based on selection
                if use_integrated_charge:
                    # For integrated charge, we'll use the channel's
                    # integrated charge value
                    # We'll get this from the channel data below
                    pass
                else:
                    try:
                        x_value = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        for fmt in ["%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]:
                            try:
                                x_value = datetime.strptime(date_str, fmt)
                                break
                            except ValueError:
                                continue
                        else:
                            logger.warning(f"Could not parse date: {date_str}")
                            continue

                for module in dataset.get("modules", []):
                    module_id = module.get("identifier", "unknown")
                    for channel in module.get("channels", []):
                        channel_name = channel.get("name", "unknown")
                        channel_key = f"{module_id}_{channel_name}"
                        if channel_key in selected_channels:
                            ageing_factors = channel.get("ageing_factors", {})

                            # Get x-axis value for this specific channel
                            if use_integrated_charge:
                                x_value = channel.get("integratedCharge")
                                if x_value is None:
                                    logger.warning(
                                        "No integrated charge for channel "
                                        f" {channel_key} in dataset {date_str}"
                                    )
                                    continue
                            else:
                                # Use the date value we already parsed
                                pass

                            if show_gaussian:
                                gaussian_value = ageing_factors.get(
                                    "normalized_gauss_ageing_factor", None
                                )
                                if gaussian_value is not None and isinstance(
                                    gaussian_value, (int, float)
                                ):
                                    gaussian_key = f"{channel_key}_gaussian"
                                    if gaussian_key not in channel_data:
                                        channel_data[gaussian_key] = []
                                    channel_data[gaussian_key].append(
                                        (x_value, gaussian_value)
                                    )
                            if show_weighted:
                                weighted_value = ageing_factors.get(
                                    "normalized_weighted_ageing_factor", None
                                )
                                if weighted_value is not None and isinstance(
                                    weighted_value, (int, float)
                                ):
                                    weighted_key = f"{channel_key}_weighted"
                                    if weighted_key not in channel_data:
                                        channel_data[weighted_key] = []
                                    channel_data[weighted_key].append(
                                        (x_value, weighted_value)
                                    )
            colors = plt.cm.tab20(range(len(selected_channels)))
            for channel_key_method, data_points in channel_data.items():
                if data_points:
                    data_points.sort(key=lambda x: x[0])
                    x_values, values = zip(*data_points)
                    if channel_key_method.endswith("_gaussian"):
                        channel_key = channel_key_method[:-9]
                        method_label = "Gaussian"
                        linestyle = "-"
                        marker = "o"
                    elif channel_key_method.endswith("_weighted"):
                        channel_key = channel_key_method[:-9]
                        method_label = "Weighted"
                        linestyle = "--"
                        marker = "s"
                    else:
                        channel_key = channel_key_method
                        method_label = ""
                        linestyle = "-"
                        marker = "o"
                    parts = channel_key.split("_", 1)
                    pm_id = parts[0] if len(parts) > 0 else "Unknown"
                    channel_name = parts[1] if len(parts) > 1 else "Unknown"
                    channel_index = (
                        selected_channels.index(channel_key)
                        if channel_key in selected_channels
                        else 0
                    )
                    color = colors[channel_index % len(colors)]
                    label = f"{channel_key} ({method_label})"
                    self.ax.plot(
                        x_values,
                        values,
                        linestyle=linestyle,
                        marker=marker,
                        label=label,
                        color=color,
                        linewidth=2,
                        markersize=6,
                    )[0]
                    for idx, (x_val, value) in enumerate(zip(x_values, values)):
                        point_key = (label, idx)
                        if use_integrated_charge:
                            x_display = f"{x_val:.0f}"
                        else:
                            x_display = x_val.strftime("%Y-%m-%d")
                        self.plot_data_info[point_key] = {
                            "pm": pm_id,
                            "channel": channel_name,
                            "method": method_label,
                            "date": x_display,
                            "value": value,
                        }

            # Set axis labels and formatting
            if use_integrated_charge:
                self.ax.set_xlabel("Integrated Charge")
                x_title = "Integrated Charge"
            else:
                self.ax.set_xlabel("Date")
                x_title = "Date"
                # Format x-axis for dates
                num_datasets = len(datasets)
                max_ticks = min(8, max(3, num_datasets))
                from matplotlib.ticker import MaxNLocator

                self.ax.xaxis.set_major_locator(
                    MaxNLocator(nbins=max_ticks, prune="both")
                )
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
                plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
                self.ax.tick_params(axis="x", which="major", pad=10)

            self.ax.set_ylabel("Normalized Ageing Factor")
            title_methods = []
            if show_gaussian:
                title_methods.append("Gaussian")
            if show_weighted:
                title_methods.append("Weighted")
            title = (
                f"Ageing Analysis - {' & '.join(title_methods)} Method"
                f"{'s' if len(title_methods) > 1 else ''} vs {x_title}"
            )
            self.ax.set_title(title)
            self.ax.grid(True, alpha=0.3)
            if channel_data:
                handles, labels = self.ax.get_legend_handles_labels()
                if len(handles) <= 20:
                    self.ax.legend(
                        loc="upper right",
                        bbox_to_anchor=(0.98, 0.98),
                        fontsize="small",
                        framealpha=0.9,
                    )
            self.fig.subplots_adjust(bottom=0.35, right=0.95, top=0.9, left=0.12)
            self.canvas.draw_idle()
            method_text = " & ".join(title_methods) if title_methods else "no"
            unique_channels = len(
                {
                    key[:-9] if key.endswith(("_gaussian", "_weighted")) else key
                    for key in channel_data.keys()
                }
            )
            axis_text = "integrated charge" if use_integrated_charge else "date"
            self.status_var.set(
                f"Displaying {unique_channels} channels using {method_text} method"
                f"{'s' if len(title_methods) > 1 else ''} vs {axis_text}"
            )
        except Exception as e:
            error_msg = f"Error updating plot: {str(e)}"
            logger.error(error_msg)
            self.status_var.set("Error updating plot")
        finally:
            self._update_pending = False

    def _reset_zoom(self):
        self.ax.relim()
        self.ax.autoscale()
        self.canvas.draw_idle()
