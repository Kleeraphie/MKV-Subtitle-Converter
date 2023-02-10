from subconverter import SubtitleConverter
from gui import GUI

if __name__ == '__main__':
    sc = SubtitleConverter()
    gui = GUI()
    exit_code, values = gui.run()
    gui.window.close()

    if exit_code == 0:
        diff_langs = values["-diff_langs-"] if values["-diff-"] else ""
        #app.main(gui.selected_paths, values["-edit-"], values["-save-"], values["-keep_old_mkvs-"], values["-keep_subs-"], app.diff_langs_from_text(diff_langs), values["-format-"])
        sc.file_paths = gui.selected_paths
        sc.edit_flag = values["-edit-"]
        sc.keep_imgs = values["-save-"]
        sc.keep_old_mkvs = values["-keep_old_mkvs-"]
        sc.keep_subs = values["-keep_subs-"]
        sc.diff_langs = sc.diff_langs_from_text(diff_langs)
        sc.format = sc.sub_format_extension(values["-format-"])
        
        sc.convert()
    elif exit_code == 1:
        exit(0)