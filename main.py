__version__ = "v1.2.5"

from subconverter import SubtitleConverter
from gui import GUI
import requests
from packaging.version import Version

if __name__ == '__main__':
    # check for updates
    try:
        response = requests.get("https://api.github.com/repos/Kleeraphie/MKV-Subtitle-Converter/releases/latest")
        latest_version = response.json()["tag_name"]
        if Version(latest_version) > Version(__version__):
            print("There is a new version available. Please download it from https://github.com/Kleeraphie/MKV-Subtitle-Converter.")
    except: # if there is no internet connection or the request fails
        print("Failed to check for updates.")

    # start the program
    gui = GUI()
    sc = SubtitleConverter()
    exit_code, values = gui.run()
    gui.window.close()

    if exit_code == 0:
        diff_langs = values["-diff_langs-"] if values["-diff-"] else ""
        sc = SubtitleConverter(gui.selected_paths, values["-edit-"], values["-save-"], values["-keep_old_mkvs-"], values["-keep_old_subs-"],
                               values["-keep_new_subs-"], sc.diff_langs_from_text(diff_langs), sc.sub_format_extension(values["-format-"]),
                               int(values["-brightness_diff-"]) / 100)
                
        sc.convert()
    elif exit_code == 1:
        exit(0)