import os
import tkinter
import tkinter.messagebox
import customtkinter
import time
import datetime
import numpy as np
import matplotlib.pyplot as plt
import hashlib
import json
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import visualization
from parser import SIPParser

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"

# ========================================
# GETTING FAMILIAR WITH THE APPLICATION UI
# ----------------------------------------
# This class defines the main application window for the Generalist Portfolio Optimization Tool.
# It sets up the layout, navigation, and various interactive components
#
# NOTES REGARDING FUNCTIONS:
# - Each widget is created and placed using grid or pack layout managers.
#   - "grid" is used literally; Think of the window as a grid of rows and columns.
#   - "pack" is used for simpler vertical/horizontal stacking within frames.
# - Don't overcomplicate griding the components!
#   - Use "rowspan"/"columnspan" to have widgets span multiple rows/columns as needed.
#   - Use "sticky" to control alignment within grid cells (n/s/e/w).
# - Configure row/column weights to control how space is allocated when resizing.
#   - "index" refers to the row/column number; a tuple with mulitple indices can be used.
#   - Higher weight means more space is given during expansion.
#   - Using a weight of "0" means the row/column will not expand.
# - When using "grid" , padding is handled both by integer values and tuples
#   - Single integer: uniform padding on all sides.
#   - Tuple of two: (left, right) or (horizontal, vertical) padding.
# - Some buttons may have a "command" parameter that links to a function.
# - Don't be afraid to get your hands dirty and experiment with the layout!
# =========================================================================
class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title(" SIP Analyzer UI")
        self.geometry(f"{1300}x{800}")
        self.minsize(1300, 800)

        self.current_frame = 'home'

        # Investment data storage
        self.original_investments = None  # Original parsed data (immutable)
        self.winds_adjusted_investments = None  # Winds-adjusted data (created on-demand)
        self.winds_loaded = False  # Flag indicating winds files are loaded

        # Visualization cache
        self.visualization_cache = []  # List of (cache_key, cache_data) tuples
        self.max_cache_size = 2  # Max number of cached visualizations (expandable)

        # wind information
        self.sip_file = None  # path to main SIP file
        self.winds_template_file = None  # path to template file
        self.winds_sip_file = None  # path to winds SIP file

        # configure grid layout (4x4)
        self.grid_columnconfigure((1, 2, 3), weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # =========================================================
        # SIDEBAR FRAME - Contains navigation & appearance settings
        # =========================================================
        # Create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=7, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        # Sidebar label
        self.sidebar_label = customtkinter.CTkLabel(self.sidebar_frame, text="| Navigation Menu |",
                                                    font=customtkinter.CTkFont(size=20, weight="bold"))
        self.sidebar_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Sidebar buttons
        self.sidebar_button_home = customtkinter.CTkButton(self.sidebar_frame, text="🏠 Home",
                                                           command=self.home_button_event)
        self.sidebar_button_home.grid(row=1, column=0, padx=20, pady=10)
        self.sidebar_button_about = customtkinter.CTkButton(self.sidebar_frame, text="🔎 About Me",
                                                            command=self.about_button_event)
        self.sidebar_button_about.grid(row=2, column=0, padx=20, pady=10)
        self.sidebar_button_help = customtkinter.CTkButton(self.sidebar_frame, text="❓ Help",
                                                           command=self.help_button_event)
        self.sidebar_button_help.grid(row=3, column=0, padx=20, pady=10)

        # Appearance menu
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame,
                                                                       values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))

        # Scaling menu
        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame,
                                                               values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))

        # ============================================
        # SETTINGS FRAME - Contains portfolio settings
        # ============================================
        self.settings_frame = customtkinter.CTkScrollableFrame(self, label_text="Portfolio Settings",
                                                               label_font=("Segoe UI", 16, "bold"))
        self.settings_frame.grid(row=4, column=2, rowspan=3, columnspan=2, padx=(10, 10), pady=(10, 20), sticky="nsew")
        self.settings_frame.grid_columnconfigure(0, weight=1)

        # Toggleable features (inside scrollable frame)
        customtkinter.CTkLabel(
            self.settings_frame,
            text="─── Toggleable Feature Set ───",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(10, 5), padx=5)

        self.toggle_investment_tethering = customtkinter.CTkCheckBox(self.settings_frame,
                                                                     text="Enable Investment Tethering")
        self.toggle_efficient_frontier = customtkinter.CTkCheckBox(self.settings_frame,
                                                                   text="Toggle Efficient Frontier",
                                                                   command=self.toggle_frontier)
        self.toggle_investment_tethering.pack(anchor="w", pady=3, padx=5)
        self.toggle_efficient_frontier.pack(anchor="w", pady=3, padx=5)
        self.toggle_winds_of_fortune = customtkinter.CTkCheckBox(
            self.settings_frame,
            text="Use Winds of Fortune"
        )
        self.toggle_winds_of_fortune.pack(anchor="w", pady=3, padx=5)

        # Axis scaling controls
        customtkinter.CTkLabel(
            self.settings_frame,
            text="─── Graph Axis Scaling ───",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(10, 5), padx=5)

        self.toggle_fixed_axes = customtkinter.CTkCheckBox(
            self.settings_frame,
            text="Use Fixed Axis Scale"
        )
        self.toggle_fixed_axes.pack(anchor="w", pady=3, padx=5)

        # Frame for axis limit inputs
        axis_frame = customtkinter.CTkFrame(self.settings_frame)
        axis_frame.pack(fill="x", pady=5, padx=5)

        # X-axis limits
        customtkinter.CTkLabel(axis_frame, text="X-axis (Risk):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.x_min_entry = customtkinter.CTkEntry(axis_frame, placeholder_text="Min", width=80)
        self.x_min_entry.grid(row=0, column=1, padx=2, pady=2)
        self.x_max_entry = customtkinter.CTkEntry(axis_frame, placeholder_text="Max", width=80)
        self.x_max_entry.grid(row=0, column=2, padx=2, pady=2)

        # Y-axis limits
        customtkinter.CTkLabel(axis_frame, text="Y-axis (Return):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.y_min_entry = customtkinter.CTkEntry(axis_frame, placeholder_text="Min", width=80)
        self.y_min_entry.grid(row=1, column=1, padx=2, pady=2)
        self.y_max_entry = customtkinter.CTkEntry(axis_frame, placeholder_text="Max", width=80)
        self.y_max_entry.grid(row=1, column=2, padx=2, pady=2)

        # Cache size control
        customtkinter.CTkLabel(
            self.settings_frame,
            text="─── Visualization Cache Size ───",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(10, 5), padx=5)

        self.cache_size_selector = customtkinter.CTkOptionMenu(
            self.settings_frame,
            values=["2", "4", "5", "10", "20", "50"],
            command=lambda v: setattr(self, 'max_cache_size', int(v))
        ).pack(anchor="w", pady=3, padx=5)

        # ===============================================================
        # PORTFOLIO INFO FRAME - Contains generated portfolio information
        # ===============================================================
        # portfolio information frame
        self.portfolio_info_frame = customtkinter.CTkFrame(self)
        self.portfolio_info_frame.grid(row=0, column=3, rowspan=4, padx=(10, 10), pady=(19, 0), sticky="nesw")
        self.portfolio_info_frame.grid_rowconfigure(0, weight=0)    # label
        self.portfolio_info_frame.grid_rowconfigure(1, weight=0)    # search frame
        self.portfolio_info_frame.grid_rowconfigure(2, weight=0)    # spacer
        self.portfolio_info_frame.grid_rowconfigure(3, weight=1)    # textbox + button
        self.portfolio_info_frame.grid_columnconfigure(0, weight=1)
        # portfolio info label
        portfolio_info_label = customtkinter.CTkLabel(self.portfolio_info_frame, text="Portfolio Information",
                                                      font=("Segoe UI", 16, "bold"))
        portfolio_info_label.grid(row=0, column=0, padx=(5, 5), pady=(5, 5), sticky='new')

        # Portfolio search frame
        portfolio_search_frame = customtkinter.CTkFrame(self.portfolio_info_frame)
        portfolio_search_frame.grid(row=1, column=0, padx=(10, 10), pady=(5, 5), sticky='ew')
        portfolio_search_frame.grid_columnconfigure(0, weight=1)

        # Search entry
        self.portfolio_search_entry = customtkinter.CTkEntry(
            portfolio_search_frame,
            placeholder_text="Search Portfolio by ID (e.g., 5)"
        )
        self.portfolio_search_entry.grid(row=0, column=0, padx=(5, 5), pady=5, sticky='ew')
        self.portfolio_search_entry.bind("<Return>", lambda e: self.search_portfolio())

        # Search button
        self.portfolio_search_button = customtkinter.CTkButton(
            portfolio_search_frame,
            text="🔍 Search",
            command=self.search_portfolio,
            width=80
        )
        self.portfolio_search_button.grid(row=0, column=1, padx=(0, 5), pady=5, sticky="e")

        self.portfolio_info_text = customtkinter.CTkTextbox(
            self.portfolio_info_frame,
            wrap="word"
        )
        self.portfolio_info_text.insert(
            "0.0",
            "After running a visualization, click a portfolio to see its details here!\n\n"
            "Alternatively, use the search box above to find a specific portfolio by its ID.\n\n"
            "Click the 'Export Portfolio Info to CSV' button below to save all generated portfolios "
            "in the current visualization"
        )
        self.portfolio_info_text.configure(state="disabled")  # read-only
        self.portfolio_info_text.grid(row=3, column=0, padx=(10, 10), pady=(0, 10), sticky='nesw')

        # Add button to export all portfolio info to CSV
        self.export_button = customtkinter.CTkButton(
            self.portfolio_info_frame,
            text="Export Portfolio Info to CSV",
            command=self.export_current_portfolios
        )
        self.export_button.grid(row=3, column=0, padx=(5, 5), pady=(0, 5), sticky='s')

        # Create tabview (visible by default)
        self.tabview = customtkinter.CTkTabview(self)

        self.tabview.grid(row=0, column=1, rowspan=4, columnspan=2, padx=(20, 0), pady=(0, 0), sticky="nsew")
        self.tabview.add("File Details")
        self.tabview.tab("File Details").grid_columnconfigure(0, weight=1)  # configure grid of individual tabs
        self.tabview.tab("File Details").grid_rowconfigure(0, weight=1)  # configure grid of individual tabs

        self.tabview.add("Graph")
        self.tabview.tab("Graph").grid_columnconfigure(0, weight=1)  # configure grid of individual tabs
        self.tabview.tab("Graph").grid_rowconfigure(0, weight=1)  # configure grid of individual tabs

        self.graph_frame = customtkinter.CTkFrame(self.tabview.tab("Graph"))  # give dedicated tab for Matplotlib fig.
        self.graph_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        # scrollable textbox inside File Details tab
        self.file_details_textbox = customtkinter.CTkTextbox(
            self.tabview.tab("File Details"),
            wrap="word"
        )
        self.file_details_textbox.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        self.file_details_textbox.insert("0.0", "No file selected.")
        self.file_details_textbox.configure(state="disabled")  # read-only

        # ==============================================================
        # CONTROL TABVIEW - Contains the parsing and winds configuration
        # ==============================================================
        self.control_tabview = customtkinter.CTkTabview(
            self,
            height=160
        )
        self.control_tabview.grid(row=4, column=1, padx=(20, 0), pady=(0, 10), sticky="nsew")
        self.control_tabview.add("File Configuration")
        self.control_tabview.add("Winds of Fortune")

        # Configure tab grids
        self.control_tabview.tab("File Configuration").grid_columnconfigure((1, 3), weight=1)
        self.control_tabview.tab("Winds of Fortune").grid_columnconfigure((1, 3), weight=1)

        # -----------------------------------------------------------------------------------------------
        # FILE CONFIGURATION TAB - Contains file selector, parse button, visualize button, and seed entry
        # -----------------------------------------------------------------------------------------------
        file_tab = self.control_tabview.tab("File Configuration")

        # File selector
        self.file_selector = customtkinter.CTkOptionMenu(
            file_tab,
            values=self.get_data_files()
        )
        self.file_selector.grid(row=0, column=0, columnspan=4, pady=(0, 5), sticky="ew")

        # Parse button
        self.parse_button = customtkinter.CTkButton(
            file_tab,
            text="Parse File",
            command=self.parse_selected_file
        )
        self.parse_button.grid(row=1, column=0, padx=(0, 5), pady=(0, 5), sticky="ew")

        # Entry box for sample count
        self.sample_entry = customtkinter.CTkEntry(
            file_tab,
            placeholder_text="Samples (1-1000)"
        )
        self.sample_entry.grid(row=1, column=1, pady=(0, 5), sticky="ew")

        # Visualize button
        self.visualize_button = customtkinter.CTkButton(
            file_tab,
            text="Run Visualization",
            command=self.run_visualization
        )
        self.visualize_button.grid(row=1, column=2, columnspan=2, padx=(5, 0), pady=(0, 5), sticky="ew")

        # Seed label
        self.seed_label = customtkinter.CTkLabel(
            file_tab,
            text="🎲 Random Seed:",
            # anchor="w"
        )
        self.seed_label.grid(row=2, column=0, padx=(0, 10), pady=(0, 0), sticky="ew")

        # Seed entry
        self.seed_entry = customtkinter.CTkEntry(
            file_tab,
            placeholder_text="Optional (leave blank for random)"
        )
        self.seed_entry.grid(row=2, column=1, columnspan=3, padx=(0, 0), pady=(0, 0), sticky="ew")

        # ------------------------------------------------------------------------------------------------
        # WINDS OF FORTUNE TAB - Contains template file selector, winds SIP file selector, and load button
        # ------------------------------------------------------------------------------------------------
        winds_tab = self.control_tabview.tab("Winds of Fortune")

        # Header label
        winds_label = customtkinter.CTkLabel(
            winds_tab,
            text="🌪 Winds of Fortune Configuration",
            font=("Segoe UI", 15, "bold")
        )
        winds_label.grid(row=0, column=0, columnspan=4, padx=10, pady=0, sticky="")  # Empty sticky = centered

        # Template file selector - LEFT SIDE
        self.winds_template_label = customtkinter.CTkLabel(winds_tab, text="Template File:")
        self.winds_template_label.grid(row=1, column=0, padx=(0, 5), pady=0, sticky="e")

        self.winds_template_selector = customtkinter.CTkOptionMenu(
            winds_tab,
            values=self.get_data_files()
        )
        self.winds_template_selector.grid(row=1, column=1, padx=(0, 15), pady=0, sticky="ew")

        # Winds SIP file selector - RIGHT SIDE
        self.winds_sip_label = customtkinter.CTkLabel(winds_tab, text="Winds SIP File:")
        self.winds_sip_label.grid(row=1, column=2, padx=(0, 5), pady=0, sticky="e")

        self.winds_sip_selector = customtkinter.CTkOptionMenu(
            winds_tab,
            values=self.get_data_files()
        )
        self.winds_sip_selector.grid(row=1, column=3, padx=(5, 0), pady=0, sticky="ew")

        # Load Winds button
        self.load_winds_button = customtkinter.CTkButton(
            winds_tab,
            text="Load Winds of Fortune Files",
            command=self.load_wind_files,
        )
        self.load_winds_button.grid(row=2, column=0, columnspan=4, padx=0, pady=(5, 0), sticky="ew")

        # =============================================================
        # Console Frame - Contains console log textbox and clear button
        # =============================================================
        self.console_frame = customtkinter.CTkFrame(self)
        self.console_frame.grid(row=6, column=1, columnspan=1, padx=(20, 0), pady=(0, 20), sticky="ew")
        self.console_frame.grid_rowconfigure(1, weight=1)
        self.console_frame.grid_columnconfigure(0, weight=1)

        # Console label
        console_label = customtkinter.CTkLabel(
            self.console_frame,
            text="📟 Console Log",
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        )
        console_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")

        # Console textbox (read-only, scrollable)
        self.console_textbox = customtkinter.CTkTextbox(
            self.console_frame,
            height=100,
            wrap="word",
            state="disabled",
            font=("Consolas", 11)
        )
        self.console_textbox.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")

        # Clear console button
        self.clear_console_button = customtkinter.CTkButton(
            self.console_frame,
            text="Clear Console",
            width=100,
            height=24,
            command=self.clear_console
        )
        self.clear_console_button.grid(row=0, column=1, padx=(5, 10), pady=(10, 5), sticky="e")

        # ===================================================================
        # ABOUT ME TEXTBOX - Contains information regarding usage and purpose
        # ===================================================================
        # create textbox (hidden by default)
        self.about_textbox = customtkinter.CTkTextbox(self, width=250, wrap="word")
        self.about_textbox.insert("0.0",
                                  "---ABOUT THIS SOFTWARE---\n\n"
                                  "This tool helps users analyze and compare different investment portfolios using "
                                  "probabilistic simulation. It is designed to support decision-making under "
                                  "uncertainty by illustrating how portfolio outcomes behave across many possible "
                                  "market conditions.\n\n"
                                  "---CAPABILITIES---\n\n"
                                  "-  Upload stochastic investment data in SIPmath 2.0 format\n"
                                  "-  Generate multiple portfolios with Dirichlet sampling\n"
                                  "-  Evaluate expected performance and risk\n"
                                  "-  Toggle important financial factors (Winds of Fortune, Investment Tethering, ...)\n"
                                  "-  View detailed portfolio comparison and risk/return statistics\n\n"
                                  "---WHAT MAKES IT DIFFERENT---\n\n"
                                  "1. Uses probabilistic instead of deterministic values.\n"
                                  "2. Avoids oversimplified 'average return' assumptions.\n"
                                  "3. Allows comparison of risk vs. reward visually.\n"
                                  "4. Supports exploration and experimentation, rather than a single 'right' answer.")

        self.about_textbox.configure(state="disabled")
        self.about_textbox.grid(row=0, column=1, rowspan=3, padx=(20, 0), pady=(20, 20), sticky="nsew")
        self.about_textbox.grid_remove()  # start hidden

        # ==================================================
        # Help Textbox - Contains help and about information
        # ==================================================
        # create textbox (hidden by default)
        self.help_textbox = customtkinter.CTkTextbox(self, width=250, wrap="word")
        self.help_textbox.insert("0.0",
                                 "Getting started with the Generalist Portfolio Model\n" +
                                 "-------------------------------------------------------------------------------\n\n" +
                                 "1. Make sure your file adheres to the SIPmath 2.0 Standard and is found within the "
                                 "/data folder. Files are automatically scanned from this folder!\n\n" +
                                 "2. Once your file is selected from the dropdown menu, click parse to load the file "
                                 "and its content into the system.\n\n" +
                                 "3. Enter the number of samples (e.g. 250) and optionally a random seed for "
                                 "reproducibility.\n\n" +
                                 "4. Click 'Visualize' to generate portfolios.\n\n" +
                                 "5. View the efficient frontier and portfolio data in the 'Graph' tab.\n\n" +
                                 "--- Random Seed ---\n"
                                 "The random seed controls the randomness in portfolio generation. Using the same seed "
                                 "will produce identical results, which is useful for:\n"
                                 "  • Reproducible analysis\n"
                                 "  • Comparing different parameter settings\n"
                                 "  • Debugging and validation\n\n"
                                 "Leave the seed field empty for different results each time.\n\n"
                                 "--- Frequently Asked Questions ---\n" +
                                 "NOTE: This section is a WIP.\n\n")

        self.help_textbox.configure(state="disabled")
        self.help_textbox.grid(row=0, column=1, rowspan=3, padx=(20, 0), pady=(20, 20), sticky="nsew")
        self.help_textbox.grid_remove()  # start hidden

        # set default values
        self.appearance_mode_optionemenu.set("Dark")
        self.scaling_optionemenu.set("100%")

    def search_portfolio(self):
        """
        Search for and display a portfolio by its index number
        Simulates clicking the portfolio on the graph
        :return:
        """
        # Validate visualization exists
        if not hasattr(self, "_last_sample_ports") or not hasattr(self, "_last_eff_pts"):
            self.log_to_console("No portfolios available - run visualization first.", "WARNING")
            return

        # Get search input
        search_text = self.portfolio_search_entry.get().strip()
        if not search_text:
            self.log_to_console("Search failed: No portfolio number entered.", "WARNING")
            return

        # Parse portfolio number
        try:
            portfolio_num = int(search_text)
        except ValueError:
            self.log_to_console(f"Search failed: '{search_text}' is not a valid number.", "ERROR")
            return

        # Determine portfolio type based on index
        total_random = len(self._last_sample_ports)
        total_efficient = len(self._last_eff_pts)

        # Check if number is in random portfolios range (1-indexed)
        if 1 <= portfolio_num <= total_random:
            idx = portfolio_num - 1  # Convert to 0-indexed
            port = self._last_sample_ports[idx]
            port_type = "Random"

            # Format display (matches on_pick behavior)
            risk = np.around(np.sqrt(port['metadata']['Variance']), 2)
            avreturn = np.around(port['metadata']['AverageReturn'], 2)
            weights = port['weights']

            # Get asset names from tooltip manager if available
            if hasattr(self, "_last_tooltip_manager"):
                weight_text = self._last_tooltip_manager.format_weights(weights)
            else:
                weight_text = f"Weights: {weights}"

            display_text = (
                f"Random Portfolio #{portfolio_num}\n"
                f"Average Return: {visualization.format_currency(avreturn)}\n"
                f"Risk (Std Dev): {risk}\n\n"
                f"{weight_text}"
            )

            # Update info textbox
            self.portfolio_info_text.configure(state="normal")
            self.portfolio_info_text.delete("1.0", "end")
            self.portfolio_info_text.insert("end", display_text)
            self.portfolio_info_text.configure(state="disabled")

            self.log_to_console(f"Found Random Portfolio #{portfolio_num}", "SUCCESS")
        else:
            # Portfolio number out of range
            self.log_to_console(
                f"Search failed: Portfolio #{portfolio_num} not found. "
                f"Valid range: 1-{total_random} "
                f"({total_random} random portfolios)",
                "ERROR"
            )

    def get_data_files(self):
        """Return list of files from the data directory"""
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        data_dir = os.path.join(base_dir, "data")

        if not os.path.exists(data_dir):
            return []

        files = [f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f))]
        return files if files else ["No files found"]

    def parse_selected_file(self):
        """Parse the selected file and display its details"""
        filename = self.file_selector.get()
        if filename == "No files found":
            self.update_file_details("⚠️ No files available in data/ directory.")
            return

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        full_path = os.path.join(base_dir, "data", filename)

        try:
            parser = SIPParser(full_path)
            investments = parser.investments
            self.original_investments = investments

            # clear any previous loaded winds data (stale data protection)
            self.winds_adjusted_investments = None
            self.winds_loaded = False

            summary_text = f"📂 File: {filename}\n\nTotal investments: {len(investments)}\n"
            for idx, inv in enumerate(investments, start=1):
                summary_text += f"\nInvestment {idx}:\n"
                meta = inv["metadata"]
                # dynamically add metadata fields
                for k, v in meta.items():
                    try:
                        if "revenue" in k.lower() or "cost" in k.lower():
                            display_value = visualization.format_currency(v)
                        else:
                            display_value = v
                    except Exception:
                        display_value = v
                    summary_text += f"   {k}: {display_value}\n"

                trials = inv["trials"]
                summary_text += f"   Trials: {len(trials)} total | First 5: {trials[:5]}\n"

            self.update_file_details(summary_text)
            self.tabview.set("File Details")
            self.log_to_console(f"Successfully parsed file: {filename}", "SUCCESS")

        except Exception as e:
            self.update_file_details(f"❌ Error parsing file:\n{e}")

    def load_wind_files(self):
        try:
            # 0 (Init) validate original data exists
            if self.original_investments is None:
                tkinter.messagebox.showerror(
                    "No Data Error",
                    "Please parse a SIP file before loading Winds of Fortune files")
                self.log_to_console("Winds of Fortune load failed: No original investment data", "ERROR")
                return

            # 1 Get filenames from dropdowns
            sip_filename = self.file_selector.get()
            template_filename = self.winds_template_selector.get()
            winds_filename = self.winds_sip_selector.get()

            if "No files found" in (template_filename, winds_filename):
                tkinter.messagebox.showerror(
                    "File Error",
                    "Please select valid template and winds SIP files.")
                return

            # 2  Build full file paths
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            data_dir = os.path.join(base_dir, "data")

            template_path = os.path.join(data_dir, template_filename)
            winds_path = os.path.join(data_dir, winds_filename)

            # 3 Create SIPParser instances
            template_parser = SIPParser(template_path)
            winds_parser = SIPParser(winds_path)

            sip_path = os.path.join(data_dir, sip_filename)
            temp_parser = SIPParser(sip_path)  # The main simulation file

            # 4  Apply Winds of Fortune transformation
            adjusted_groups = temp_parser.apply_winds(
                simulated_groups=self.original_investments,  # use original data
                template_groups=template_parser.investments,
                wind_groups=winds_parser.investments
            )

            # store data separately (to not overwrite original)
            self.winds_adjusted_investments = adjusted_groups
            self.winds_loaded = True

            tkinter.messagebox.showinfo(
                "Success",
                "Winds of Fortune applied successfully!\n\n"
                "Toggle 'Use Winds of Fortune' in customization options to enable/disable.")

        except Exception as e:
            tkinter.messagebox.showerror(
                "Error", f"Failed to load files:\n{e}")
            self.winds_adjusted_investments = None
            self.winds_loaded = False

    def update_file_details(self, text):
        """
        Helper to update the File Details textbox
        :param text: Text to add to the file details textbox
        """
        self.file_details_textbox.configure(state="normal")
        self.file_details_textbox.delete("0.0", "end")
        self.file_details_textbox.insert("0.0", text)
        self.file_details_textbox.configure(state="disabled")

    def toggle_frontier(self):
        """Show / hide the efficient frontier line on the graph."""
        is_checked = self.toggle_efficient_frontier.get()  # True or False

        if hasattr(self, "_frontier_line"):
            self._frontier_line.set_visible(is_checked)

        if hasattr(self, "_eff_scatter"):
            self._eff_scatter.set_visible(is_checked)

        if hasattr(self, "_last_canvas"):
            self._last_canvas.draw()

    def run_visualization(self):
        """
        Attempts to run a portfolio visualization based on user settings.
        Validates inputs, manages caching, and updates the graph display.
        1. Validates sample count input (1-1000).
        2. Retrieves seed value (or generates random seed if empty).
        3. Determines data source (original or Winds-adjusted).
        4. Clears old plot from graph frame.
        5. Retrieves axis limits if fixed scaling is enabled.
        6. Checks visualization cache for existing data.
            - If cached data exists, regenerates plot from cache.
            - If no cache, generates new visualization and caches the data.
        7. Embeds the Matplotlib figure into the GUI.
        8. Logs progress and errors to the console.
        """
        try:
            self.log_to_console("Starting visualization...", "INFO")
            start_time = time.time()

            count = int(self.sample_entry.get())
            if self.original_investments is None:
                tkinter.messagebox.showerror("Error", "Please parse a file first.")
                return
            if not (1 <= count <= 1000):
                tkinter.messagebox.showerror("Invalid Input", "Please enter a number between 1 and 1000.")
                return

            # Get seed value (None if empty or invalid)
            seed = None
            seed_text = self.seed_entry.get().strip()
            if seed_text:
                try:
                    seed = int(seed_text)
                except ValueError:
                    tkinter.messagebox.showerror("Invalid Seed", "Seed must be an integer. Using random seed instead.")
                    return
            else:
                seed = np.random.randint(0, 2 ** 31 - 1)  # generate random seed for logging purposes
                self.log_to_console(f"Generated random seed: {seed}", "INFO")

            # Get initial frontier visibility state from checkbox
            show_frontier = self.toggle_efficient_frontier.get()

            # select data source based on Winds of Fortune toggle
            use_winds = self.toggle_winds_of_fortune.get()

            if use_winds:
                if not self.winds_loaded or self.winds_adjusted_investments is None:
                    self.log_to_console("Visualization failed: Winds of Fortune files not loaded", "ERROR")
                    return
                data_to_use = self.winds_adjusted_investments
                self.log_to_console("Using Winds of Fortune adjusted data for visualization.", "INFO")
            else:
                # user is requesting original data
                data_to_use = self.original_investments
                self.log_to_console("Using original investment data for visualization.", "INFO")

            # Clear old plot if it exists
            for widget in self.graph_frame.winfo_children():
                widget.pack_forget()  # unpack before destroying
                widget.destroy()

            # Force frame update to avoid embedding issues
            self.graph_frame.update_idletasks()

            # Get axis limits if fixed scaling is enabled
            axis_limits = None
            if self.toggle_fixed_axes.get():
                try:
                    x_min = float(self.x_min_entry.get()) if self.x_min_entry.get().strip() else None
                    x_max = float(self.x_max_entry.get()) if self.x_max_entry.get().strip() else None
                    y_min = float(self.y_min_entry.get()) if self.y_min_entry.get().strip() else None
                    y_max = float(self.y_max_entry.get()) if self.y_max_entry.get().strip() else None

                    axis_limits = {
                        'x_min': x_min,
                        'x_max': x_max,
                        'y_min': y_min,
                        'y_max': y_max
                    }
                    self.log_to_console("Using fixed axis scale", "INFO")
                except ValueError:
                    tkinter.messagebox.showerror("Invalid Input", "Axis limits must be numeric values.")
                    self.log_to_console("Visualization failed: Invalid axis limits", "ERROR")
                    return

            # Cache Integration - check if we have a cached version
            cache_key = self.generate_viz_cache_key(use_winds, count, seed)
            cached = self.get_cached_visualization(cache_key)

            if cached is not None:
                # Cache hit - retrieve cached data
                self.log_to_console("Using cached visualization data.", "INFO")
                sample_ports = cached['sample_ports']
                effpts = cached['effpts']
                asset_names = cached['asset_names']

                # Regenerate figure from cached data
                plt.close('all')
                fig, ax = plt.subplots(dpi=200)

                # Create TooltipManager
                tm = visualization.TooltipManager(ax, self.portfolio_info_text)
                tm.asset_names = asset_names

                # Extract plot coordinates from cached portfolio data
                rx = [np.sqrt(p['metadata']['Variance']) for p in sample_ports]
                ry = [p['metadata']['AverageReturn'] for p in sample_ports]
                ex = [np.sqrt(p['metadata']['Variance']) for p in effpts]
                ey = [p['metadata']['AverageReturn'] for p in effpts]

                # Plot data
                random_scatter = tm.add_scatter(rx, ry, c='b', s=15, picker=True, pickradius=5)
                eff_scatter = tm.add_scatter(ex, ey, c='r', marker='*', picker=True, pickradius=5)
                eff_scatter.set_visible(show_frontier)

                frontier_line, = ax.plot(ex, ey, c='r', ls='--', visible=show_frontier)

                # Store portfolio data in TooltipManager
                tm.randpts = sample_ports
                tm.effpts = effpts
                tm.eff_scatter = eff_scatter
                tm.frontier_line = frontier_line

                # Configure axes
                ax.set_xlabel("Risk (Std Dev)")
                ax.set_ylabel("Average Return ($)")
                ax.set_title(f"Random portfolios ({count} samples) & Efficient Frontier")
                ax.grid(ls="--")

            else:
                # Cache miss - proceed to generate visualization normally
                self.log_to_console("No cached data found. Generating new visualization...", "INFO")
                fig, tm, sample_ports, effpts, frontier_line, eff_scatter = visualization.visualize_portfolios(
                    data_to_use, count, self.portfolio_info_text, show_frontier=show_frontier, seed=seed
                )

                # store data in cache
                asset_names = [item['metadata']['Name'] for item in data_to_use]
                cache_data = {
                    'sample_ports': sample_ports,
                    'effpts': effpts,
                    'asset_names': asset_names
                }

                self.cache_visualization(cache_key, cache_data)
                self.log_to_console("Visualization data cached for future use.", "INFO")

            # Apply axis limits if specified
            if axis_limits:
                ax = fig.axes[0]
                if axis_limits['x_min'] is not None or axis_limits['x_max'] is not None:
                    ax.set_xlim(left=axis_limits['x_min'], right=axis_limits['x_max'])
                if axis_limits['y_min'] is not None or axis_limits['y_max'] is not None:
                    ax.set_ylim(bottom=axis_limits['y_min'], top=axis_limits['y_max'])

            self._frontier_line = frontier_line
            self._eff_scatter = eff_scatter

            # Embed figure in the Tkinter tab
            fig.tight_layout()  # adjust layout before embedding
            canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
            canvas.draw()
            widget = canvas.get_tk_widget()
            widget.pack(fill="both", expand=True)
            widget.configure(width=1, height=1)  # allow resizing
            self.graph_frame.update_idletasks()

            # add toolbar to graph
            toolbar = NavigationToolbar2Tk(canvas, self.graph_frame)
            toolbar.update()
            toolbar.pack(fill="x")

            # IMPORTANT: re-bind the tooltip manager's canvas to the Tk canvas so events route correctly
            # For TooltipManager implementation above we can set tm.canvas to the FigureCanvasTkAgg object
            # and re-connect event handlers (we re-bind to ensure the correct canvas is used).
            try:
                # disconnect old connections if necessary (not strictly necessary here)
                tm.canvas = canvas  # use the mpl-capable canvas (FigureCanvasTkAgg)
                # re-register the event handlers on the Tk canvas
                tm.canvas.mpl_connect("motion_notify_event", tm.hover)
                tm.canvas.mpl_connect("pick_event", tm.on_pick)
            except Exception as e:
                # fallback: attach handlers to fig.canvas
                fig.canvas.mpl_connect("motion_notify_event", tm.hover)
                fig.canvas.mpl_connect("pick_event", tm.on_pick)

            # store references so garbage collection doesn't remove them
            self._last_fig = fig
            self._last_canvas = canvas
            self._last_tooltip_manager = tm
            self._last_sample_ports = sample_ports
            self._last_eff_pts = effpts
            self._last_seed = seed  # store seed used
            self._last_used_winds = use_winds  # store winds usage

            # Switch to graph tab
            self.tabview.set("Graph")

            end_time = time.time()
            duration = end_time - start_time

            # Calculate generation speed if not cached
            if cached is None:
                portfolios_per_second = count / duration if duration > 0 else 0
                self.log_to_console(f"Seed used: {seed}", "INFO")

                self.log_to_console(
                    f"Visualization completed: {count} portfolios generated in {duration:.2f} seconds "
                    f"({portfolios_per_second:.1f} portfolios/sec).",
                    "SUCCESS"
                )
            else:
                # Cached - log retrieval time only
                self.log_to_console(
                    f"Visualization completed using cached data in {duration:.2f} seconds.", "SUCCESS")

        except ValueError:
            tkinter.messagebox.showerror("Invalid Input", "Please enter a valid integer.")
        except Exception as e:
            tkinter.messagebox.showerror("Visualization Error", f"An error occurred:\n{e}")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)
        if self.current_frame == "home":
            self.home_button_event()
        elif self.current_frame == "about":
            self.about_button_event()
        elif self.current_frame == "help":
            self.about_button_event()

    def home_button_event(self):
        """Return to the main home view with all controls visible."""
        self.help_textbox.grid_remove()  # remove help text
        self.about_textbox.grid_remove()  # remove about text
        self.tabview.grid()  # re-add tabs
        self.file_selector.grid()  # re-add file selector
        self.portfolio_info_frame.grid()  # re-add portfolio frame
        self.control_tabview.grid()  # re-add control tabview
        self.console_frame.grid()  # re-add console log frame
        self.settings_frame.grid()  # re-add settings

        self.current_frame = "home"

    def about_button_event(self):
        """Show the about me information frame."""
        self.tabview.grid_remove()  # remove tabs
        self.file_selector.grid_remove()  # remove file selector
        self.help_textbox.grid_remove()  # remove help text
        self.settings_frame.grid_remove()  # remove settings
        self.portfolio_info_frame.grid_remove()  # remove portfolio frame
        self.control_tabview.grid_remove()  # remove control tabview
        self.console_frame.grid_remove()  # remove console log frame
        self.about_textbox.grid()  # re-add about text

        self.current_frame = "about"

    def help_button_event(self):
        """Show the help information frame."""
        self.tabview.grid_remove()  # remove tabs
        self.file_selector.grid_remove()  # remove file selector
        self.settings_frame.grid_remove()  # remove settings
        self.portfolio_info_frame.grid_remove()  # remove portfolio frame
        self.control_tabview.grid_remove()  # remove control tabview
        self.about_textbox.grid_remove()  # remove about text
        self.console_frame.grid_remove()  # remove console log frame
        self.help_textbox.grid()  # re-add text

        self.current_frame = "help"

    def export_current_portfolios(self):
        """
        Export the currently visualized portfolios to a CSV file.
        Prompts user for filename, then saves
        """
        if not hasattr(self, "_last_sample_ports"):
            self.log_to_console("No portfolios to export.", "WARNING")
            return

        # ask user for filename
        dialog = customtkinter.CTkInputDialog(
            title="Export Portfolios",
            text="Enter filename for the CSV (without extension):"
        )
        filename = dialog.get_input()
        if not filename:
            self.log_to_console("Export cancelled - no filename specified.", "WARNING")
            return

        # build full path
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        export_path = os.path.join(base_dir, "data", f"{filename}.csv")

        success = visualization.export_portfolios_to_csv(
            export_path,
            self._last_sample_ports,
            self._last_eff_pts
        )

        if success:
            tkinter.messagebox.showinfo("Success", f"Portfolios exported to {export_path}")
        else:
            tkinter.messagebox.showerror("Error", "Failed to export portfolios.")

    def log_to_console(self, message, level="INFO"):
        """
        Routes messages to the console textbox with timestamp and level
        :param message: Message text to display
        :param level: Message level (INFO, SUCCESS, WARNING, ERROR)
        """
        # enable write to textbox
        self.console_textbox.configure(state="normal")
        # format timestamp
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # color code based on level
        level_colors = {
            "INFO": "",  # default color
            "SUCCESS": " ✓ ",
            "WARNING": " ⚠",
            "ERROR": " ❌"
        }
        icon = level_colors.get(level.upper(), "")
        formatted_message = f"[{timestamp}] {icon} {message}\n"

        # #insert message
        self.console_textbox.insert("end", formatted_message)
        # auto-scroll to end
        self.console_textbox.see("end")
        # disable write to textbox
        self.console_textbox.configure(state="disabled")

    def clear_console(self):
        """Clear all messages from the console"""
        self.console_textbox.configure(state="normal")
        self.console_textbox.delete("1.0", "end")
        self.console_textbox.configure(state="disabled")
        self.log_to_console("Console cleared.", "INFO")

    def generate_viz_cache_key(self, use_winds, count, seed):
        """
        Generate a unique cache key for the visualization parameters.
        :param use_winds: Whether Winds of Fortune is used
        :param count: Number of portfolios
        :param seed: Random seed
        :return: String cache key
        """

        cache_dict = {
            'use_winds': use_winds,
            'count': count,
            'seed': seed,
        }

        # convert to JSON string and hash for key
        cache_str = json.dumps(cache_dict, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()

    def get_cached_visualization(self, cache_key):
        """
        Retrieve cached visualization if it exists.
        :param cache_key: Cache key string
        :return: Cached visualization data or None
        """
        for key, data in self.visualization_cache:
            if key == cache_key:
                return data
        return None

    def cache_visualization(self, cache_key, cache_data):
        """
        Cache the visualization data with LRU (Least Recently Used) eviction
        :param cache_key: Cache key string
        :param cache_data: Visualization data to cache
        """

        # remove if already exists (to front for LRU)
        self.visualization_cache = [(k, d) for (k, d) in self.visualization_cache if k != cache_key]

        # add to front of cache
        self.visualization_cache.insert(0, (cache_key, cache_data))

        # trim cache if exceeds max size (evicting the oldest entry)
        if len(self.visualization_cache) > self.max_cache_size:
            self.visualization_cache = self.visualization_cache[:self.max_cache_size]
            self.log_to_console("Visualization cache full - evicting oldest entry.", "INFO")


if __name__ == "__main__":
    """Main entry point for the application. Simply creates and runs the App."""
    app = App()
    app.mainloop()
