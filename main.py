from controller.controller import Controller
from config import Config
import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()

    Controller()

    # set first start variable to False
    config = Config()
    config.save_settings({Config.Settings.FIRST_START: False})
    config.save_config()
