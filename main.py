from controller.controller import Controller
from config import Config

if __name__ == '__main__':

    Controller()

    # set first start variable to False
    config = Config()
    config.save_settings({Config.Settings.FIRST_START: False})
    config.save_config()
