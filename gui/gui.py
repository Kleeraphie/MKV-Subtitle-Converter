from subconverter import SubtitleConverter
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os
from gui.settings import SettingsWindow
from gui.about import AboutWindow
import math
import requests
from packaging.version import Version
from config import Config
import webbrowser

class GUI:
    
    def __init__(self):
        self.__nothing_selected = "Select a file from the left list"
        self.__selected = [self.__nothing_selected] # names of the selected files
        self.__fnames = []
        self.selected_paths = [] # paths of the selected files
        self.old_path = ""
        self.config = Config()

        self.window = tk.Tk()
        self.window.geometry(newGeometry="500x650+0+0")
        self.window.title("MKV Subtitle Converter")
        self.create_menu()

        self.values = {}

        self.run_settings_help_window_row = 1

        self.window.eval("tk::PlaceWindow . center")
        self.window.resizable(True, True)

        # =====Selection window===== #
        selection_window = tk.Frame(master=self.window)
        dir_label = tk.Label(master=selection_window, text="Directory:")
        self.dir_entry = tk.Entry(master=selection_window)
        self.dir_entry.config(state="readonly")
        dir_button = tk.Button(master=selection_window, text="Browse", command=lambda: self.choose_dir())
        unselected_files_label = tk.Label(master=selection_window, text="Unselected files:")
        selected_files_label = tk.Label(master=selection_window, text="Selected files:")
        self.unselected_files_listbox = tk.Listbox(master=selection_window)
        self.selected_files_listbox = tk.Listbox(master=selection_window)
        separator = ttk.Separator(master=selection_window, orient="vertical")
        

        # TODO: put these three widgets on the left side of the window
        # and not over the whole width (like in the GUI up to v1.2.5)
        dir_label.grid(row=0, column=0, sticky="we", padx=5, pady=5)
        self.dir_entry.grid(row=0, column=1, sticky="we", columnspan=5, padx=5, pady=5)
        dir_button.grid(row=0, column=6, sticky="we", padx=5, pady=5)

        unselected_files_label.grid(row=1, column=0, sticky="w", columnspan=3)
        selected_files_label.grid(row=1, column=4, sticky="w", columnspan=3)
        self.unselected_files_listbox.grid(row=2, column=0, sticky="nsew", columnspan=3, padx=(5, 0))
        separator.grid(row=2, column=3, sticky="ns", padx=5, pady=5)
        self.selected_files_listbox.grid(row=2, column=4, sticky="nsew", columnspan=3, padx=(0, 5))

        self.unselected_files_listbox.bind("<Double-Button-1>", lambda _: self.select_file(self.unselected_files_listbox.get(self.unselected_files_listbox.curselection())))
        self.unselected_files_listbox.bind("<Return>", lambda _: self.select_file(self.unselected_files_listbox.get(self.unselected_files_listbox.curselection())))
        self.selected_files_listbox.bind("<Double-Button-1>", lambda _: self.unselect_file(self.selected_files_listbox.get(self.selected_files_listbox.curselection())))
        self.selected_files_listbox.bind("<Return>", lambda _: self.unselect_file(self.selected_files_listbox.get(self.selected_files_listbox.curselection())))

        # Set up row and column configurations for responsive layout
        selection_window.grid_rowconfigure(0, weight=0)
        selection_window.grid_rowconfigure(1, weight=0)
        selection_window.grid_rowconfigure(2, weight=1)

        selection_window.grid_columnconfigure(0, weight=1)
        selection_window.grid_columnconfigure(1, weight=2)
        selection_window.grid_columnconfigure(2, weight=1)
        selection_window.grid_columnconfigure(3, weight=0) # separator has no weight
        selection_window.grid_columnconfigure(4, weight=1)
        selection_window.grid_columnconfigure(5, weight=2)
        selection_window.grid_columnconfigure(6, weight=1)

        selection_window.pack(fill=tk.BOTH, expand=True)

        settings_seperator_window = tk.Frame(master=self.window)
        settings_label = tk.Label(master=settings_seperator_window, text="Settings", font=("Helvetica", 12, "bold"))
        settings_help_button = tk.Button(master=settings_seperator_window, text="?", command=lambda: self.show_run_settings_help_window())
        window_separator = ttk.Separator(master=self.window, orient="horizontal")
        settings_label.grid(row=0, column=0, sticky="w", padx=5, pady=(15, 0))
        settings_help_button.grid(row=0, column=1, sticky="e", padx=5, pady=(15, 0))
        settings_seperator_window.pack(fill=tk.X, padx=5, pady=5)
        window_separator.pack(fill=tk.X, padx=5, pady=5)  # TODO: put this in the settings_seperator_window

        # =====Settings window===== #
        # TODO: there is extra space between use_diff_langs and brightness_diff_label
        job_settings_window = tk.Frame(master=self.window)
        subtitle_format_label = tk.Label(master=job_settings_window, text="Format of the new subtitles:")
        self.subtitle_format = ttk.Combobox(master=job_settings_window, values=SubtitleConverter.sub_formats(None), state="readonly")
        edit_subtitles = tk.Checkbutton(master=job_settings_window, text="Edit subtitles before muxing", variable=self.add_variable('edit_subs'))
        save_images = tk.Checkbutton(master=job_settings_window, text="Save images of PGS subtitles", variable=self.add_variable('save_images'))
        keep_old_mkvs = tk.Checkbutton(master=job_settings_window, text="Keep original MKV files", variable=self.add_variable('keep_old_mkvs'))
        keep_old_subs = tk.Checkbutton(master=job_settings_window, text="Keep a copy of the old subtitle files", variable=self.add_variable('keep_old_subs'))
        keep_new_subs = tk.Checkbutton(master=job_settings_window, text="Keep a copy of the new subtitle files", variable=self.add_variable('keep_new_subs'))
        use_diff_langs = tk.Checkbutton(master=job_settings_window, text="Use different languages for some subtitles", variable=self.add_variable('use_diff_langs'), command=lambda: self.change_visibility(self.diff_langs, self.values.get('use_diff_langs').get()))
        self.diff_langs = tk.Text(master=job_settings_window, height=5, width=24)
        brightness_diff_label = tk.Label(master=job_settings_window, text="Allowed text color brightness deviation:")
        self.brightness_diff = tk.Scale(master=job_settings_window, from_=0, to=100, orient=tk.HORIZONTAL, showvalue=False, command=lambda _: brightness_value_label.config(text=f'{self.brightness_diff.get()}%'))
        brightness_value_label = tk.Label(master=job_settings_window)

        self.values.get('keep_old_subs').set(True)
        self.subtitle_format.set(self.subtitle_format["values"][0])
        self.brightness_diff.set(3)

        subtitle_format_label.grid(row=0, column=0, sticky="w")
        self.subtitle_format.grid(row=0, column=1, sticky="w", padx=5)
        edit_subtitles.grid(row=1, column=0, sticky="w", columnspan=3)
        save_images.grid(row=2, column=0, sticky="w", columnspan=3)
        keep_old_mkvs.grid(row=3, column=0, sticky="w", columnspan=3)
        keep_old_subs.grid(row=4, column=0, sticky="w", columnspan=3)
        keep_new_subs.grid(row=5, column=0, sticky="w", columnspan=3)
        use_diff_langs.grid(row=6, column=0, sticky="w", columnspan=3)
        self.diff_langs.grid(row=7, column=0, sticky="w", padx=24, columnspan=3)
        self.change_visibility(self.diff_langs, self.values.get('use_diff_langs').get())
        brightness_diff_label.grid(row=8, column=0, sticky="w", columnspan=3)
        self.brightness_diff.grid(row=8, column=1, sticky="w", padx=((len(brightness_diff_label.cget("text"))+24), 0))
        brightness_value_label.grid(row=8, column=2, sticky="w")

        job_settings_window.grid_rowconfigure(0, weight=1)
        job_settings_window.grid_rowconfigure(1, weight=1)
        job_settings_window.grid_rowconfigure(2, weight=1)
        job_settings_window.grid_rowconfigure(3, weight=1)
        job_settings_window.grid_rowconfigure(4, weight=1)
        job_settings_window.grid_rowconfigure(5, weight=1)
        job_settings_window.grid_rowconfigure(6, weight=1)
        job_settings_window.grid_rowconfigure(7, weight=1)
        job_settings_window.grid_rowconfigure(8, weight=1)
        
        job_settings_window.pack(fill=tk.BOTH, expand=True)

        # =====Buttons window===== #
        self.wait_var = tk.IntVar()
        buttons_window = tk.Frame(master=self.window)
        start_button = tk.Button(master=buttons_window, text="Start", command=lambda: self.wait_var.set(0), width=20, height=4)
        exit_button = tk.Button(master=buttons_window, text="Exit", command=lambda: self.wait_var.set(1), width=20, height=4)
        self.window.protocol('WM_DELETE_WINDOW', lambda: self.wait_var.set(1))

        window_separator = ttk.Separator(master=buttons_window, orient="horizontal")
        window_separator.pack(fill=tk.X, padx=5, pady=15)
        start_button.pack(side=tk.LEFT, expand=True, padx=5, pady=5)
        exit_button.pack(side=tk.LEFT, expand=True, padx=5, pady=5)

        buttons_window.pack(fill=tk.BOTH, expand=True)

    def add_variable(self, name):
        self.values[name] = tk.BooleanVar()
        return self.values[name]

    def choose_dir(self):
        dir_path = filedialog.askdirectory()
        
        if dir_path:
            self.dir_entry.config(state="normal")
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, dir_path)
            self.dir_entry.config(state="readonly")

        if not os.path.isdir(dir_path) or dir_path == self.old_path:
            return

        self.old_path = dir_path

        file_list = os.listdir(dir_path) # get list of files in selected folder
        # show only MKV files in the left list that are not already selected
        self.__fnames = [f for f in file_list if f.lower().endswith((".mkv")) and os.path.join(dir_path, f) not in self.selected_paths]
        self.update_selections(self.__selected)

    def update_selections(self, selected):
        self.selected_files_listbox.delete(0,tk.END)
        self.selected_files_listbox.insert(tk.END, *selected)
        
        self.unselected_files_listbox.delete(0,tk.END)
        self.unselected_files_listbox.insert(tk.END, *self.__fnames)

    def select_file(self, file_name: str):
        try:
            self.__fnames.remove(file_name)
            if self.__nothing_selected in self.__selected:
                self.__selected.remove(self.__nothing_selected)

            self.__selected.append(file_name)
            self.selected_paths.append(os.path.join(self.old_path, file_name))

            self.update_selections(self.__selected)
        except ValueError:
            pass

    def unselect_file(self, file_name: str):
        try:
            if file_name == self.__nothing_selected:
                return

            index = self.__selected.index(file_name)
            unselected_file_path = self.selected_paths[index][:self.selected_paths[index].rfind(os.sep)]

            self.__selected.pop(index)
            self.selected_paths.pop(index)

            if (unselected_file_path == self.old_path):
                self.__fnames.append(file_name)

            if len(self.__selected) == 0:
                self.__selected.append(self.__nothing_selected)

            self.update_selections(self.__selected)
        except ValueError:
            pass

    def change_visibility(self, widget, visible: bool):
        if visible:
            widget.grid(row=7, column=0, sticky="w", padx=24, columnspan=3) # TODO: move padding to the widget
        else:
            widget.grid_forget()

    def exit_gui(self):
        self.wait_var.set(1)

    def run(self) -> tuple[int, dict]:
        self.window.tkraise()
        self.window.wait_variable(self.wait_var)

        # convert booleanvars to bools
        for key in self.values:
            self.values[key] = self.values[key].get()

        # add diff_langs to values if use_diff_langs is True
        self.values['diff_langs'] = ''
        if self.values.get('use_diff_langs'):
            self.values['diff_langs'] = self.diff_langs.get('1.0', tk.END)
            # self.values['diff_langs'] = self.values['diff_langs'].split('\n')
            # self.values['diff_langs'] = [s for s in self.diff_langs if s.strip() != '']

        self.values['selected_paths'] = self.selected_paths
        self.values['brightness_diff'] = self.brightness_diff.get()
        self.values['sub_format'] = self.subtitle_format.get()
        
        self.window.quit()
        return self.wait_var.get(), self.values
    
    def create_menu(self):
        self.menu = tk.Menu(self.window)
        self.menu.add_command(label="Settings", command=lambda: SettingsWindow())

        help_menu = tk.Menu(self.menu, tearoff=0)
        help_menu.add_command(label="About...", command=lambda: AboutWindow(self))
        self.menu.add_cascade(label="Help", menu=help_menu)

        self.window.config(menu=self.menu)

    def show_run_settings_help_window(self):
        help_window = tk.Toplevel(self.window)
        help_window.title("Help")
        help_window.geometry("500x500")
        help_window.transient(self.window)
        help_window.resizable(False, False)


        help_text = tk.Label(help_window, text='Help for choosing the right settings', font=("Helvetica", 12))
        help_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.run_settings_help_window_add_text('Format of the new subtitles: ', 'The format of your new subtitles. SRT is the most common format and is supported by most video players.', help_window)
        self.run_settings_help_window_add_text('Edit subtitles before muxing: ', 'Before exchanging the subtitles with the new ones, the program will pause so that you can edit them. The program continues after pressing <Enter> in the console.', help_window)
        self.run_settings_help_window_add_text('Save images of PGS subtitles: ', 'You can save the images that make up the old subtitles. This can be useful if you want to compare the old and new subtitles. They are stored in a directory where this program is installed.', help_window)
        self.run_settings_help_window_add_text('Keep original MKV files: ', 'You can keep the original video files. This way you can test different settings.', help_window)
        self.run_settings_help_window_add_text('Keep a copy of the old subtitle files: ', 'You can save the original subtitle files. This way the program does not need to extract them again if you run the program again.', help_window)
        self.run_settings_help_window_add_text('Keep a copy of the new subtitle files: ', 'You can save the new subtitle files. This way you can easily edit them later.', help_window)
        self.run_settings_help_window_add_text('Use different languages for some subtitles: ', 
                                                ('Here you can tell the program to use a different language for some languages.'
                                                'This can be useful if the English subtitles contain letters like ä, ö or ü. Then you could use'
                                                'the German language because it contains all letters of the English language + these special letters.'
                                                'Changes are seperated by a new line and follow this format: "old language" -> "new language"'
                                                ' (e.g. eng -> ger).'), help_window)
        self.run_settings_help_window_add_text('Allowed text color brightness deviation: ',
                                                    ('You can change the maximum allowed difference in brightness in the text color.'
                                                    'This can be useful because some subtitle images are more noisy than others.'
                                                    'The value should be as low as possible but the text in the images should not be too thin.'), help_window)

        help_window.grid_columnconfigure(0, weight=1)

    def run_settings_help_window_add_text(self, name: str, description: str, parent: tk.Toplevel):
        h = math.ceil((len(name) + len(description)) / 85) + 1
        subtitle_format_help = tk.Text(parent, wrap=tk.WORD, font=("Arial", 10), height=h, width=50)
        subtitle_format_help.insert(tk.END, name)
        subtitle_format_help.insert(tk.END, description)
        subtitle_format_help.tag_add('setting_name', '1.0', f'1.{len(name)}')
        subtitle_format_help.tag_config('setting_name', font='Arial 10 bold')
        subtitle_format_help.tag_add('setting_description', f'1.{len(description)}', '1.end')
        subtitle_format_help.tag_config('setting_description', font='Arial 10 normal')
        subtitle_format_help.config(state="disabled")
        subtitle_format_help.grid(row=self.run_settings_help_window_row, column=0, sticky="we")
        parent.grid_rowconfigure(self.run_settings_help_window_row, weight=1)
        self.run_settings_help_window_row += 1

    def update_available(self):
        try:
            response = requests.get("https://api.github.com/repos/Kleeraphie/MKV-Subtitle-Converter/releases/latest")
            latest_version = response.json()["tag_name"]

            return (Version(latest_version) >= Version(self.config.get_version()), latest_version)
        except: # if there is no internet connection or the request fails
            return (False, self.config.get_version())

    def check_for_updates(self):
        update_available, latest_version = self.update_available()

        if update_available:
            update = tk.messagebox.askyesno("Update available", f"Version {latest_version} is available. Do you want to download it?")
            if update:
                webbrowser.open('https://github.com/Kleeraphie/MKV-Subtitle-Converter/releases/latest')
