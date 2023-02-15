from subconverter import SubtitleConverter
from gui import GUI

if __name__ == '__main__':
    gui = GUI()
    sc = SubtitleConverter()
    exit_code, values = gui.run()
    gui.window.close()

    if exit_code == 0:
        diff_langs = values["-diff_langs-"] if values["-diff-"] else ""
        sc = SubtitleConverter(gui.selected_paths, values["-edit-"], values["-save-"], values["-keep_old_mkvs-"], values["-keep_subs-"],
                               sc.diff_langs_from_text(diff_langs), sc.sub_format_extension(values["-format-"]))
                
        sc.convert()
    elif exit_code == 1:
        exit(0)