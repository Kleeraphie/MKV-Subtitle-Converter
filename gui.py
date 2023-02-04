import app
import PySimpleGUI as sg
import os

class GUI:
    nothing_selected = "Select a file from the left list"
    selected = [nothing_selected] # names of the selected files
    fnames = []
    selected_paths = [] # paths of the selected files

    def __init__(self):
        # list of not selected MKV files
        self.unselected_list_column = [
            [
                sg.Text("Directory:"),
                sg.In(size=(25, 1), enable_events=True, key="-FOLDER-"),
                sg.FolderBrowse(),
            ],
            [sg.Listbox(values=[self.fnames], enable_events=True, size=(40, 20), key="-unselected-")],
            [sg.Button("Select all", enable_events=True, key="-select_all-")]
        ]

        # list of selected MKV files
        self.selected_column = [
            [sg.Text("Selected files:")],
            [sg.Listbox(values=[self.nothing_selected], enable_events=True, size=(40, 20), key="-selected-")],
            [sg.Button("Unselect all", enable_events=True, key="-unselect_all-")]
        ]

        self.settings_column = [
            [
                sg.Text("Format of the new subtitles:"),
                sg.DropDown(app.sub_formats(), default_value=app.sub_formats()[0], key="-format-", readonly=True)
            ],
            [sg.Checkbox("Edit subtitles before muxing", key="-edit-")],
            [sg.Checkbox("Save images of PGS subtitles", key="-save-")],
            [sg.Checkbox("Keep original MKV files", key="-keep_old_mkvs-")],
            [sg.Checkbox("Keep a copy of the new subtitle files", key="-keep_subs-")],
            [sg.Checkbox("Use different language for some subtitles", enable_events=True, key="-diff-")],
            [sg.Text(text="Usage: one change per line; old language code -> new language code, example: ger -> eng", visible=False, key="-diff_langs_text-")],
            [sg.Multiline(enable_events=True, size=(89, 20), key="-diff_langs-", visible=False)]
        ]

        self.layout = [
            [
                sg.Column(self.unselected_list_column),
                sg.VSeperator(),
                sg.Column(self.selected_column),   
            ],
            [sg.HSeparator()],
            [sg.Column(self.settings_column)],
            [sg.HSeparator()],
            [sg.Button("Start", enable_events=True, key="-start-"), sg.Button("Exit")]
        ]

        self.window = sg.Window("MKV Subtitle Converter", self.layout)
        self.old_path = ""

    def update_selections(self, selected):
        self.window["-selected-"].update(selected)
        self.window["-unselected-"].update(self.fnames)

    def select_folder(self, dir_path: str):

        if not os.path.isdir(dir_path) or dir_path == self.old_path:
            return

        file_list = os.listdir(dir_path) # get list of files in selected folder

        # show only MKV files in the left list that are not already selected
        self.fnames = [f for f in file_list if f.lower().endswith((".mkv")) and os.path.join(dir_path, f) not in self.selected_paths]
        self.window["-unselected-"].update(self.fnames)

    def select_file(self, file_name: str, dir_path: str):
        try:
            self.fnames.remove(file_name)
            self.selected.append(file_name)
            self.selected_paths.append(os.path.join(dir_path, file_name))

            if self.nothing_selected in self.selected:
                self.selected.remove(self.nothing_selected)

            self.update_selections(self.selected)
        except ValueError:
            pass

    def unselect_file(self, file_name: str, dir_path: str):
        try:
            if file_name == self.nothing_selected:
                return

            self.selected.remove(file_name)
            self.selected_paths.remove(os.path.join(dir_path, file_name))
            self.fnames.append(file_name)

            if len(self.selected) == 0:
                self.selected.append(self.nothing_selected)

            self.update_selections(self.selected)
        except ValueError:
            pass

    def change_visibility(self, key: str, visibility: bool):
        self.window[key].update(visible=visibility)
        self.window.refresh()

    def run(self) -> tuple[int, dict]:
        while True: # Run the Event Loop
            event, values = self.window.read()
            
            if event == "Exit" or event == sg.WIN_CLOSED:
                return 1, None

            elif event == "-FOLDER-": # Folder name was filled in, make a list of files in the folder
                self.select_folder(values["-FOLDER-"])
                self.old_path = values["-FOLDER-"]

            elif event == "-unselected-":  # A file was chosen from the left box
                self.select_file(values["-unselected-"][0], values["-FOLDER-"])

            elif event == "-selected-":  # A file was chosen from the right box
                self.unselect_file(values["-selected-"][0], values["-FOLDER-"])

            elif event == "-diff-":  # checkbox for different languages was clicked
                self.change_visibility("-diff_langs-", values["-diff-"])
                self.change_visibility("-diff_langs_text-", values["-diff-"])

            elif event == "-select_all-":  # select all button was clicked
                for fname in self.fnames.copy():
                    self.select_file(fname, values["-FOLDER-"])

            elif event == "-unselect_all-":  # unselect all button was clicked
                for fname in self.selected.copy():
                    self.unselect_file(fname, values["-FOLDER-"])

            elif event == "-start-":  # start button was clicked
                # self.start(values)
                return 0, values
