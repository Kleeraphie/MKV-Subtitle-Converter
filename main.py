import app
from gui import GUI

if __name__ == '__main__':
    gui = GUI()
    exit_code, values = gui.run()
    gui.window.close()

    if exit_code == 0:
        diff_langs = values["-diff_langs-"] if values["-diff-"] else ""
        app.main(gui.selected_paths, values["-edit-"], values["-save-"], values["-keep_old_mkvs-"], values["-keep_srt-"], app.diff_langs_from_text(diff_langs))
    elif exit_code == 1:
        exit(0)