__version__ = "v1.2.5"

from subconverter import SubtitleConverter
from gui.gui import GUI
import requests
from packaging.version import Version
from config import Config

if __name__ == '__main__':
    # load settings
    config = Config()

    # check for updates
    if config.check_for_updates():
        try:
            response = requests.get("https://api.github.com/repos/Kleeraphie/MKV-Subtitle-Converter/releases/latest")
            latest_version = response.json()["tag_name"]
            if Version(latest_version) > Version(__version__):
                print("There is a new version available. Please download it from https://github.com/Kleeraphie/MKV-Subtitle-Converter.")
        except: # if there is no internet connection or the request fails
            print("Failed to check for updates.")

    # start the program
    gui = GUI()
    exit_code, values = gui.run()
    gui.window.destroy()

    if exit_code == 0:
        sc = SubtitleConverter()
        sc = SubtitleConverter(values['selected_paths'], values['edit_subs'], values['save_images'], values['keep_old_mkvs'], values['keep_old_subs'],
                               values['keep_new_subs'], sc.diff_langs_from_text(values['diff_langs']), sc.sub_format_extension(values['sub_format']),
                               values['brightness_diff'] / 100)
                
        sc.convert()
    elif exit_code == 1:
        # exit(0)
        pass

    # set bFirstStart to False
    config.save_settings({Config.Settings.FIRST_START: False})
    config.save_config()
