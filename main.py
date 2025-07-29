from controller.controller import Controller
from config import Config
from gui.gui import GUI
import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()

    # start the program
    controller = Controller()
    gui = GUI()
    controller.register_gui(gui)
    controller.start_program()

    # set first start variable to False
    config = Config()
    config.save_settings({Config.Settings.FIRST_START: False})
    config.save_config()
