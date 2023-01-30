import app
import PySimpleGUI as sg
import os

def update_selections(window, selected, fnames):
    window["-selected-"].update(selected)
    window["-unselected-"].update(fnames)

nothing_selected = "Select a file from the left list"
selected = [nothing_selected] # names of the selected files
selected_paths = [] # paths of the selected files with names
fnames = []
diff_langs = ""

# list of not selected MKV files
unselected_list_column = [
    [
        sg.Text("Directory:"),
        sg.In(size=(25, 1), enable_events=True, key="-FOLDER-"),
        sg.FolderBrowse(),
    ],
    [sg.Listbox(values=[fnames], enable_events=True, size=(40, 20), key="-unselected-")],
    [sg.Button("Select all", enable_events=True, key="-select_all-")]
]

# list of selected MKV files
selected_column = [
    [sg.Text("Selected files:")],
    [sg.Listbox(values=[nothing_selected], enable_events=True, size=(40, 20), key="-selected-")],
    [sg.Button("Unselect all", enable_events=True, key="-unselect_all-")]
]

settings_column = [
    [sg.Checkbox("Edit subtitles before muxing", key="-edit-")],
    [sg.Checkbox("Save images of PGS subtitles", key="-save-")],
    [sg.Checkbox("Use different language for some subtitles", enable_events=True, key="-diff-")],
    [sg.Text(text="Usage: one change per line; old language code -> new language code, example: ger -> eng", visible=False, key="-diff_langs_text-")],
    [sg.Multiline(enable_events=True, size=(89, 20), key="-diff_langs-", visible=False)],
    [sg.Checkbox("Keep original MKV files", key="-keep-")]
]

layout = [
    [
        sg.Column(unselected_list_column),
        sg.VSeperator(),
        sg.Column(selected_column),   
    ],
    [sg.HSeparator()],
    [sg.Column(settings_column)],
    [sg.HSeparator()],
    [sg.Button("Start", enable_events=True, key="-start-"), sg.Button("Exit")]
]

window = sg.Window("MKV Subtitle Changer", layout)
old_path = ""

while True: # Run the Event Loop
    event, values = window.read()
    
    if event == "Exit" or event == sg.WIN_CLOSED:
        break

    elif event == "-FOLDER-": # Folder name was filled in, make a list of files in the folder
        if not os.path.isdir(values["-FOLDER-"]):
            continue

        if values["-FOLDER-"] == old_path:
            continue

        old_path = values["-FOLDER-"]

        file_list = os.listdir(values["-FOLDER-"]) # get list of files in selected folder

        # show only MKV files in the left list that are not already selected
        fnames = [f for f in file_list.copy() if f.lower().endswith((".mkv")) and os.path.join(values["-FOLDER-"], f) not in selected_paths]
        window["-unselected-"].update(fnames)

    elif event == "-unselected-":  # A file was chosen from the left box
        try:
            filename =  values["-unselected-"][0]

            fnames.remove(filename)
            selected.append(filename)
            selected_paths.append(os.path.join(values["-FOLDER-"], filename))

            if nothing_selected in selected:
                selected.remove(nothing_selected)

            update_selections(window, selected, fnames)
        except ValueError:
            pass

    elif event == "-selected-":  # A file was chosen from the right box
        try:
            filename =  values["-selected-"][0]

            if filename == nothing_selected:
                continue

            selected.remove(filename)
            selected_paths.remove(os.path.join(values["-FOLDER-"], filename))
            if len(selected) == 0:
                selected.append(nothing_selected)

            fnames.append(filename)

            update_selections(window, selected, fnames)
        except ValueError:
            pass

    elif event == "-diff-":  # checkbox for different languages was clicked
        window["-diff_langs-"].update(visible=values["-diff-"])
        window["-diff_langs_text-"].update(visible=values["-diff-"])
        window.refresh()

    elif event == "-select_all-":  # select all button was clicked
        if len(fnames) == 0:
            continue

        if nothing_selected in selected:
                selected.remove(nothing_selected)

        selected += fnames

        for fname in fnames:
            selected_paths.append(os.path.join(values["-FOLDER-"], fname))

        fnames = []

        update_selections(window, selected, fnames)

    elif event == "-unselect_all-":  # unselect all button was clicked
        if nothing_selected in selected:
            continue

        fnames += selected

        for fname in selected:
            selected_paths.remove(os.path.join(values["-FOLDER-"], fname))

        selected = [nothing_selected]

        update_selections(window, selected, fnames)

    elif event == "-start-":  # start button was clicked
        if values["-diff-"]:
            diff_langs = values["-diff_langs-"]
        
        window.close()
        app.main(selected_paths, values["-edit-"], values["-save-"], values["-keep-"], app.diff_langs_from_text(diff_langs))