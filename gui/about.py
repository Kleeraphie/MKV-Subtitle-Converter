import tkinter as tk
from tkinter import ttk
from config import Config
from gui.licenses import LicensesWindow

class AboutWindow(tk.Toplevel):
    
    def __init__(self, parent):
        super().__init__(parent.window)
        self.translate = parent.config.translate
        
        self.title(self.translate("About"))
        self.geometry("250x250")
        self.resizable(False, False)

        self.wait_visibility()
        x = parent.window.winfo_x() + parent.window.winfo_width()//2 - self.winfo_width()//2
        y = parent.window.winfo_y() + parent.window.winfo_height()//2 - self.winfo_height()//2
        self.geometry(f"+{x}+{y}")
        
        self.config = Config()
        self.parent = parent
        
        name_label = tk.Label(self, text='MKV Subtitle Converter')
        version_label = tk.Label(self, text=self.config.get_version())
        updateButton = ttk.Button(self, text=self.translate("Check for updates"), command=self.check_for_updates)
        licenses_btn = ttk.Button(self, text=self.translate("View Licenses"), command=self.show_licenses)

        # name_label.place(relx=0.5, rely=0.25, anchor='center')
        # version_label.place(relx=0.5, rely=0.5, anchor='center')
        # updateButton.place(relx=0.5, rely=0.75, anchor='center')
        # licenses_btn.place(relx=0.5, rely=1, anchor='center')

        name_label.grid(row=0, column=0, pady=(50, 5), padx=5)
        version_label.grid(row=1, column=0, padx=5, pady=5)
        updateButton.grid(row=2, column=0, padx=5, pady=5)
        licenses_btn.grid(row=4, column=0, padx=5, pady=5)

        self.columnconfigure(0, weight=1)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)  # Falls noch eine Zeile nötig ist
        self.rowconfigure(4, weight=1)


    def check_for_updates(self):
        update_available = self.parent.update_available()[0]

        if update_available:
            self.parent.check_for_updates()
        else:
            no_update_label = tk.Label(self, text=self.translate("You are already up to date."))
            # no_update_label.place(relx=0.5, rely=0.9, anchor='center')
            no_update_label.grid(row=3, column=0, padx=5, pady=5)

    def show_licenses(self):
        LicensesWindow(self.parent)
