import os
import tkinter
import tkinter.messagebox
import customtkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import visualization
from parser import SIPParser

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title(" SIP Analyzer UI")
        self.geometry(f"{1000}x{600}")
        self.minsize(1000, 600)

        self.current_frame = 'home'

        # wind information
        self.sip_file = None                # path to main SIP file
        self.winds_template_file = None     # path to template file
        self.winds_sip_file = None          # path to winds SIP file


        # configure grid layout (4x4)
        self.grid_columnconfigure((1, 2, 3), weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=5, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        # logo
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="| Navigation Menu |",
                                                 font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        # sidebar buttons
        self.sidebar_button_home = customtkinter.CTkButton(self.sidebar_frame, text="🏠 Home",
                                                           command=self.home_button_event)
        self.sidebar_button_home.grid(row=1, column=0, padx=20, pady=10)
        self.sidebar_button_about = customtkinter.CTkButton(self.sidebar_frame, text="🔎 About Me",
                                                            command=self.about_button_event)
        self.sidebar_button_about.grid(row=2, column=0, padx=20, pady=10)
        self.sidebar_button_help = customtkinter.CTkButton(self.sidebar_frame, text="❔ Help",
                                                           command=self.help_button_event)
        self.sidebar_button_help.grid(row=3, column=0, padx=20, pady=10)
        # appearance menu
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame,
                                                                       values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
        # scaling menu
        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame,
                                                               values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))

        # settings frame
        self.settings_frame = customtkinter.CTkFrame(self)
        self.settings_frame.grid(row=0, column=2, padx=(10, 10), pady=(38, 5), sticky="nsew")
        self.settings_frame.grid_columnconfigure(2, weight=1)

        settings_label = customtkinter.CTkLabel(self.settings_frame, text="Portfolio Customization Options",
                                                font=("Segoe UI", 16, "bold"))
        settings_label.pack(pady=(5, 5))

        # Togglable features (no functionality yet)
        self.toggle_negative_weights = customtkinter.CTkCheckBox(self.settings_frame,
                                                                 text="Allow Negative Weights (Short Selling)")
        self.toggle_investment_tethering = customtkinter.CTkCheckBox(self.settings_frame,
                                                                     text="Enable Investment Tethering")
        self.toggle_high_risk_mode = customtkinter.CTkCheckBox(self.settings_frame,
                                                               text="Allow High-Risk Portfolio Region")
        self.toggle_efficient_frontier = customtkinter.CTkCheckBox(self.settings_frame,
                                                                   text="Toggle Efficient Frontier",
                                                                   command=self.toggle_frontier)

        self.toggle_negative_weights.pack(anchor="w", pady=3)
        self.toggle_investment_tethering.pack(anchor="w", pady=3)
        self.toggle_high_risk_mode.pack(anchor="w", pady=3)
        self.toggle_efficient_frontier.pack(anchor="w", pady=3)
        self.toggle_efficient_frontier.select()
        self.toggle_winds_of_fortune = customtkinter.CTkCheckBox(
            self.settings_frame,
            text="Use Winds of Fortune"
        )
        self.toggle_winds_of_fortune.pack(anchor="w", pady=3)

        # Winds of Fortune Configuration Section
        self.winds_frame = customtkinter.CTkFrame(self)
        self.winds_frame.grid(row=4, column=1, padx=(20, 0), pady=(0, 20), sticky="ew")

        winds_label = customtkinter.CTkLabel(
            self.winds_frame,
            text="🌪 Winds of Fortune Configuration",
            font=("Segoe UI", 15, "bold")
        )
        winds_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")

        # Winds Template File selector
        self.winds_template_label = customtkinter.CTkLabel(self.winds_frame, text="Template File:")
        self.winds_template_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.winds_template_selector = customtkinter.CTkOptionMenu(
            self.winds_frame, values=self.get_data_files()
        )
        self.winds_template_selector.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Winds SIP File selector
        self.winds_sip_label = customtkinter.CTkLabel(self.winds_frame, text="Winds SIP File:")
        self.winds_sip_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.winds_sip_selector = customtkinter.CTkOptionMenu(
            self.winds_frame, values=self.get_data_files()
        )
        self.winds_sip_selector.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Apply Winds Button
        self.load_winds_button = customtkinter.CTkButton(
            self.winds_frame,
            text="Load Winds of Fortune Files",
            command=self.load_wind_files
        )
        self.load_winds_button.grid(row=3, column=0, columnspan=2, padx=10, pady=(10, 15), sticky="ew")

        # portfolio information frame
        self.portfolio_info_frame = customtkinter.CTkFrame(self)
        self.portfolio_info_frame.grid(row=1, column=2, rowspan=4, padx=(10, 10), pady=(5, 10), sticky="nesw")
        self.portfolio_info_frame.grid_rowconfigure(0, weight=0)
        self.portfolio_info_frame.grid_rowconfigure(2, weight=1)
        self.portfolio_info_frame.grid_columnconfigure(0, weight=1)
        # portfolio info label
        portfolio_info_label = customtkinter.CTkLabel(self.portfolio_info_frame, text="Portfolio Information",
                                                      font=("Segoe UI", 16, "bold"))
        portfolio_info_label.grid(rowspan=2, padx=(5, 5), pady=(5, 5), sticky='new')

        # portfolio info text
        # portfolio_info_text = customtkinter.CTkTextbox(self.portfolio_info_frame, wrap="word", state="disabled")
        # portfolio_info_text.pack(pady=(5, 5))

        self.portfolio_info_text = customtkinter.CTkTextbox(
            self.portfolio_info_frame,
            wrap="word",
            state="disabled"
        )
        self.portfolio_info_text.grid(row=2, column=0, padx=(10, 10), pady=(0, 10), sticky='nesw')

        # add button to export all portfolio info to CSV
        self.export_button = customtkinter.CTkButton(
            self.portfolio_info_frame,
            text="Export Portfolio Info to CSV",
            command=self.export_current_portfolios
        )
        self.export_button.grid(row=2, column=0, padx=(5, 5), pady=(0, 5), sticky='s')

        # create textbox (hidden by default)
        self.help_textbox = customtkinter.CTkTextbox(self, width=250, wrap="word")
        self.help_textbox.insert("0.0",
                                 "Getting started with the Generalist Portfolio Model\n" +
                                 "-------------------------------------------------------------------------------\n\n" +
                                 "1. Make sure your file adheres to the SIPmath 2.0 Standard and is found within the "
                                 "/data folder. Files are automatically scanned from this folder!\n\n" +
                                 "2. Once your file is selected from the dropdown menu, click parse to load the file "
                                 "and its content into the system.\n\n" +
                                 "3. Enter the number of samples (e.g. 250) and click 'Visualize'.\n\n" +
                                 "4. View the efficient frontier and portfolio data in the 'Graph' tab.\n\n" +
                                 "--- Frequently Asked Questions ---\n" +
                                 "NOTE: This section is a WIP.\n\n")

        self.help_textbox.configure(state="disabled")
        self.help_textbox.grid(row=0, column=1, rowspan=3, padx=(20, 0), pady=(20, 20), sticky="nsew")
        self.help_textbox.grid_remove()  # start hidden

        # about me textbox
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

        # create tabview (visible by default)
        self.tabview = customtkinter.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=1, rowspan=2, padx=(20, 0), pady=(20, 10), sticky="nsew")
        self.tabview.add("File Details")
        self.tabview.tab("File Details").grid_columnconfigure(0, weight=1)  # configure grid of individual tabs
        self.tabview.tab("File Details").grid_rowconfigure(0, weight=1)  # configure grid of individual tabs

        self.tabview.add("Graph")
        self.tabview.tab("Graph").grid_columnconfigure(0, weight=1)  # configure grid of individual tabs
        self.tabview.tab("Graph").grid_rowconfigure(0, weight=1)  # configure grid of individual tabs

        self.graph_frame = customtkinter.CTkFrame(self.tabview.tab("Graph"))  # give dedicated tab for Matplotlib fig.
        self.graph_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # scrollable textbox inside File Details tab
        self.file_details_textbox = customtkinter.CTkTextbox(
            self.tabview.tab("File Details"),
            wrap="word"
        )
        self.file_details_textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.file_details_textbox.insert("0.0", "No file selected.")
        self.file_details_textbox.configure(state="disabled")  # read-only

        # file selector underneath tabview
        self.file_selector = customtkinter.CTkOptionMenu(self, values=self.get_data_files())
        self.file_selector.grid(row=2, column=1, padx=(20, 0), pady=(0, 5), sticky="ew")

        self.parse_frame = customtkinter.CTkFrame(self)
        self.parse_frame.grid(row=3, column=1, padx=(20, 0), pady=(0, 20), sticky="ew")
        self.parse_frame.grid_columnconfigure(0, weight=1)  # Parse button expands
        self.parse_frame.grid_columnconfigure(1, weight=0)  # Entry fixed
        self.parse_frame.grid_columnconfigure(2, weight=0)  # Visualize button fixed

        # Parse button inside frame
        self.parse_button = customtkinter.CTkButton(
            self.parse_frame, text="Parse File", command=self.parse_selected_file
        )
        self.parse_button.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="ew")

        # Entry box for sample count
        self.sample_entry = customtkinter.CTkEntry(
            self.parse_frame, placeholder_text="Samples (1-1000)"
        )
        self.sample_entry.grid(row=0, column=1, padx=(5, 5), pady=0, sticky="e")

        # Visualize button
        self.visualize_button = customtkinter.CTkButton(
            self.parse_frame, text="Visualize", command=self.run_visualization
        )
        self.visualize_button.grid(row=0, column=2, padx=(5, 0), pady=0, sticky="e")

        # Seed label - ROW 1
        self.seed_label = customtkinter.CTkLabel(
            self.parse_frame,
            text="🎲 Random Seed:",
            anchor="center"
        )
        self.seed_label.grid(row=1, column=0, padx=(0, 5), pady=(0, 0), sticky="ew")

        # Seed entry box - ROW 1
        self.seed_entry = customtkinter.CTkEntry(
            self.parse_frame,
            placeholder_text="Optional Seed (leave blank for random)",
            width=200
        )
        self.seed_entry.grid(row=1, column=1, columnspan=2, padx=(5, 0), pady=(5, 0), sticky="ew")

        # set default values
        self.appearance_mode_optionemenu.set("Dark")
        self.scaling_optionemenu.set("100%")

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
            self.current_investments = investments

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

        except Exception as e:
            self.update_file_details(f"❌ Error parsing file:\n{e}")

    def load_wind_files(self):
        try:
            # 1 Get filenames from dropdowns
            sip_filename = self.file_selector.get()
            template_filename = self.winds_template_selector.get()
            winds_filename = self.winds_sip_selector.get()

            if "No files found" in (template_filename, winds_filename):
                tkinter.messagebox.showerror("File Error", "Please select valid template and winds SIP files.")
                return

            # 2  Build full file paths
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            data_dir = os.path.join(base_dir, "data")

            sip_path = os.path.join(data_dir, sip_filename)
            template_path = os.path.join(data_dir, template_filename)
            winds_path = os.path.join(data_dir, winds_filename)

            # 3 Create SIPParser instances
            parser = SIPParser(sip_path)  # The main simulation file
            template_parser = SIPParser(template_path)
            winds_parser = SIPParser(winds_path)

            # 4  Apply Winds of Fortune transformation
            adjusted_groups = parser.apply_winds(
                simulated_groups=parser.investments,
                template_groups=template_parser.investments,
                wind_groups=winds_parser.investments
            )

            # 5 Save the updated data for later visualization
            self.current_investments = adjusted_groups
            tkinter.messagebox.showinfo("Success", "Winds of Fortune applied successfully!")

        except Exception as e:
            tkinter.messagebox.showerror("Error", f"Failed to load files:\n{e}")


    def update_file_details(self, text):
        """Helper to update the File Details textbox"""
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
        """Run visualization with the given sample count and show it in graph tab."""
        try:
            count = int(self.sample_entry.get())
            if not hasattr(self, "current_investments"):
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

            # Get initial frontier visibility state from checkbox
            show_frontier = self.toggle_efficient_frontier.get()

            # Clear old plot if it exists
            for widget in self.graph_frame.winfo_children():
                widget.destroy()

            # Get figure and tooltip manager from visualization module
            # Check if Winds of Fortune is enabled and loaded
            use_winds = hasattr(self, "toggle_winds_of_fortune") and self.toggle_winds_of_fortune.get()

            if use_winds and hasattr(self, "wind_mappings") and hasattr(self, "wind_sip_values"):
                self.load_wind_files()
            else:
                data_to_use = self.current_investments

            fig, tm, sample_ports, effpts, frontier_line, eff_scatter = visualization.visualize_portfolios(
                data_to_use, count, self.portfolio_info_text, show_frontier=show_frontier, seed=seed
            )

            self._frontier_line = frontier_line
            self._eff_scatter = eff_scatter

            # Embed figure in the Tkinter tab
            canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
            canvas.draw()
            widget = canvas.get_tk_widget()
            widget.pack(fill="both", expand=True)

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

            # Switch to graph tab
            self.tabview.set("Graph")

            # show confirmation message if seed was used
            if seed is not None:
                tkinter.messagebox.showinfo("Visualization Complete", f"Visualization complete using seed {seed}.")

        except ValueError:
            tkinter.messagebox.showerror("Invalid Input", "Please enter a valid integer.")
        except Exception as e:
            tkinter.messagebox.showerror("Visualization Error", f"An error occurred:\n{e}")

    def open_input_dialog_event(self):
        dialog = customtkinter.CTkInputDialog(text="Type in a number:", title="CTkInputDialog")
        print("CTkInputDialog:", dialog.get_input())

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
        # print("sidebar_button click")
        self.help_textbox.grid_remove()  # remove help text
        self.about_textbox.grid_remove()  # remove about text
        self.tabview.grid()  # re-add tabs
        self.file_selector.grid()  # re-add file selector
        self.settings_frame.grid()  # re-add settings for portfolio generation
        self.parse_frame.grid()  # re-add parsing information
        self.portfolio_info_frame.grid()  # re-add portfolio frame
        self.winds_frame.grid()  # re-add winds of fortune frame

        self.current_frame = "home"

    def about_button_event(self):
        # print("about_button click")
        self.tabview.grid_remove()  # remove tabs
        self.file_selector.grid_remove()  # remove file selector
        self.help_textbox.grid_remove()  # remove help text
        self.settings_frame.grid_remove()  # remove settings
        self.parse_frame.grid_remove()  # remove parsing information
        self.portfolio_info_frame.grid_remove()  # remove portfolio frame
        self.winds_frame.grid_remove()  # remove winds of fortune frame
        self.about_textbox.grid()  # re-add about text

        self.current_frame = "about"

    def help_button_event(self):
        self.tabview.grid_remove()  # remove tabs
        self.file_selector.grid_remove()  # remove file selector
        self.settings_frame.grid_remove()  # remove settings
        self.parse_frame.grid_remove()  # remove parsing information
        self.portfolio_info_frame.grid_remove()  # remove portfolio frame
        self.about_textbox.grid_remove()  # remove about text
        self.winds_frame.grid_remove()  # remove winds of fortune frame
        self.help_textbox.grid()  # re-add text

        self.current_frame = "help"

    def export_current_portfolios(self):
        """
        Export the currently visualized portfolios to a CSV file.
        Prompts user for filename, then saves
        :return:
        """
        if not hasattr(self, "_last_sample_ports"):
            tkinter.messagebox.showerror("Error", "No portfolios to export.")
            return

        # ask user for filename
        dialog = customtkinter.CTkInputDialog(
            title="Export Portfolios",
            text="Enter filename for the CSV (without extension):"
        )
        filename = dialog.get_input()
        if not filename:
            tkinter.messagebox.showwarning("Cancelled", "Export cancelled - no filename specified.")
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


if __name__ == "__main__":
    app = App()
    app.mainloop()
