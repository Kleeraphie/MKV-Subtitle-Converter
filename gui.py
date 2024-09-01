from subconverter import SubtitleConverter
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os

class GUI:
    
    def __init__(self):
        self.__nothing_selected = "Select a file from the left list"
        self.__selected = [self.__nothing_selected] # names of the selected files
        self.__fnames = []
        self.selected_paths = [] # paths of the selected files
        self.old_path = ""

        self.window = tk.Tk()
        self.window.geometry(newGeometry="500x650+0+0")
        self.window.title("MKV Subtitle Converter")

        self.values = {}

        self.window.eval("tk::PlaceWindow . center")
        self.window.resizable(True, True)
        ttk.Style().theme_use("default")

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

        settings_label = tk.Label(master=self.window, text="Settings", font=("Helvetica", 12, "bold"))
        window_separator = ttk.Separator(master=self.window, orient="horizontal")
        settings_label.pack(padx=5, pady=(15, 0), anchor="w")
        window_separator.pack(fill=tk.X, padx=5, pady=5)

        # =====Settings window===== #
        # TODO: there is extra space between use_diff_langs and brightness_diff_label
        settings_window = tk.Frame(master=self.window)
        subtitle_format_label = tk.Label(master=settings_window, text="Format of the new subtitles:")
        self.subtitle_format = ttk.Combobox(master=settings_window, values=SubtitleConverter.sub_formats(None), state="readonly")
        edit_subtitles = tk.Checkbutton(master=settings_window, text="Edit subtitles before muxing", variable=self.add_variable('edit_subs'))
        save_images = tk.Checkbutton(master=settings_window, text="Save images of PGS subtitles", variable=self.add_variable('save_images'))
        keep_old_mkvs = tk.Checkbutton(master=settings_window, text="Keep original MKV files", variable=self.add_variable('keep_old_mkvs'))
        keep_old_subs = tk.Checkbutton(master=settings_window, text="Keep a copy of the old subtitle files", variable=self.add_variable('keep_old_subs'))
        keep_new_subs = tk.Checkbutton(master=settings_window, text="Keep a copy of the new subtitle files", variable=self.add_variable('keep_new_subs'))
        use_diff_langs = tk.Checkbutton(master=settings_window, text="Use different languages for some subtitles", variable=self.add_variable('use_diff_langs'), command=lambda: self.change_visibility(self.diff_langs, self.values.get('use_diff_langs').get()))
        self.diff_langs = tk.Text(master=settings_window, height=5, width=24)
        brightness_diff_label = tk.Label(master=settings_window, text="Allowed text color brightness deviation:")
        self.brightness_diff = tk.Scale(master=settings_window, from_=0, to=100, orient=tk.HORIZONTAL, showvalue=False, command=lambda _: brightness_value_label.config(text=f'{self.brightness_diff.get()}%'))
        brightness_value_label = tk.Label(master=settings_window)

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

        settings_window.grid_rowconfigure(0, weight=1)
        settings_window.grid_rowconfigure(1, weight=1)
        settings_window.grid_rowconfigure(2, weight=1)
        settings_window.grid_rowconfigure(3, weight=1)
        settings_window.grid_rowconfigure(4, weight=1)
        settings_window.grid_rowconfigure(5, weight=1)
        settings_window.grid_rowconfigure(6, weight=1)
        settings_window.grid_rowconfigure(7, weight=1)
        settings_window.grid_rowconfigure(8, weight=1)
        
        settings_window.pack(fill=tk.BOTH, expand=True)

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
