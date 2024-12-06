from controller.controller import Controller
from config import Config

if __name__ == '__main__':
    # load settings
    config = Config()

    Controller()

    # set bFirstStart to False
    config.save_settings({Config.Settings.FIRST_START: False})
    config.save_config()
