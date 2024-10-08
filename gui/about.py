import tkinter as tk
from config import Config

class AboutWindow(tk.Toplevel):
    
    def __init__(self, parent):
        super().__init__(parent.window)
        self.translate = parent.config.translate
        
        self.title(self.translate("About"))
        self.geometry("250x250")
        self.resizable(False, False)

        self.config = Config()
        self.parent = parent
        
        name_label = tk.Label(self, text='MKV Subtitle Converter')
        version_label = tk.Label(self, text=self.config.get_version())
        updateButton = tk.Button(self, text=self.translate("Check for updates"), command=self.check_for_updates)

        name_label.place(relx=0.5, rely=0.25, anchor='center')
        version_label.place(relx=0.5, rely=0.5, anchor='center')
        updateButton.place(relx=0.5, rely=0.75, anchor='center')

    def check_for_updates(self):
        update_available = self.parent.update_available()[0]

        if update_available:
            self.parent.check_for_updates()
        else:
            no_update_label = tk.Label(self, text=self.translate("You are already up to date."))
            no_update_label.place(relx=0.5, rely=0.9, anchor='center')
