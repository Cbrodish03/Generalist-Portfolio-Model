import tkinter
import tkinter.messagebox
import customtkinter
import os
import visualization
from parser import SIPParser

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title(" SIP Analyzer UI")
        self.geometry(f"{700}x{600}")
        self.minsize(700, 600)

        # configure grid layout (4x4)
        self.grid_columnconfigure((1, 2, 3), weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        # logo
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="| Navigation Menu |", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        # sidebar buttons
        self.sidebar_button_home = customtkinter.CTkButton(self.sidebar_frame, text="Home", command=self.home_button_event)
        self.sidebar_button_home.grid(row=1, column=0, padx=20, pady=10)
        self.sidebar_button_about = customtkinter.CTkButton(self.sidebar_frame, text="About Me", command=self.about_button_event)
        self.sidebar_button_about.grid(row=2, column=0, padx=20, pady=10)
        self.sidebar_button_help = customtkinter.CTkButton(self.sidebar_frame, text="Help", command=self.help_button_event)
        self.sidebar_button_help.grid(row=3, column=0, padx=20, pady=10)
        # appearance menu
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
        # scaling menu
        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))

        # create textbox (hidden by default)
        self.textbox = customtkinter.CTkTextbox(self, width=250)
        self.textbox.insert("0.0",
                            "Description\n\nHere is where we give a quick description of the tool + how to use.\n\n"
                            "This would include a setup guide and a hint at what the user is actually looking at\n\n"
                            "Of course, this only exists when the user clicks the 'about me' button")
        self.textbox.grid(row=0, column=1, rowspan=3, padx=(20, 0), pady=(20, 20), sticky="nsew")
        self.textbox.grid_remove()  # start hidden

        # create tabview (visible by default)
        self.tabview = customtkinter.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=1, rowspan=2, padx=(20, 0), pady=(20, 10), sticky="nsew")
        self.tabview.add("File Details")
        self.tabview.add("Tab 2")
        # self.tabview.add("Tab 3")
        self.tabview.tab("File Details").grid_columnconfigure(0, weight=1)  # configure grid of individual tabs
        self.tabview.tab("File Details").grid_rowconfigure(0, weight=1)  # configure grid of individual tabs
        # self.tabview.tab("Tab 2").grid_columnconfigure(0, weight=1)

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
                    summary_text += f"   {k}: {v}\n"
                trials = inv["trials"]
                summary_text += f"   Trials: {len(trials)} total | First 5: {trials[:5]}\n"

            self.update_file_details(summary_text)
            self.tabview.set("File Details")

        except Exception as e:
            self.update_file_details(f"❌ Error parsing file:\n{e}")

    def update_file_details(self, text):
        """Helper to update the File Details textbox"""
        self.file_details_textbox.configure(state="normal")
        self.file_details_textbox.delete("0.0", "end")
        self.file_details_textbox.insert("0.0", text)
        self.file_details_textbox.configure(state="disabled")

    def run_visualization(self):
        """Run visualization with the given sample count."""
        try:
            count = int(self.sample_entry.get())
            if 1 <= count <= 1000:
                visualization.visualize_portfolios(self.current_investments, count)
            else:
                tkinter.messagebox.showerror("Invalid Input", "Please enter a number between 1 and 1000.")
        except ValueError:
            tkinter.messagebox.showerror("Invalid Input", "Please enter a valid integer.")

    def open_input_dialog_event(self):
        dialog = customtkinter.CTkInputDialog(text="Type in a number:", title="CTkInputDialog")
        print("CTkInputDialog:", dialog.get_input())

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    def home_button_event(self):
        print("sidebar_button click")
        self.textbox.grid_remove()  # remove text
        self.tabview.grid()     # re-add tabs
        self.file_selector.grid()   # re-add file selector

    def about_button_event(self):
        print("about_button click")
        self.tabview.grid_remove()  # remove tabs
        self.file_selector.grid_remove()    # remove file selector
        self.textbox.grid()     # re-add text

    def help_button_event(self):
        print("help_button click")
        tkinter.messagebox.showinfo("Help", "This is where instructions will go.")


if __name__ == "__main__":
    app = App()
    app.mainloop()