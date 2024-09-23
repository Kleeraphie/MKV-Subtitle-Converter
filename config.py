import configparser
from enum import Enum

class Config:
    class Settings(Enum):
        CHECK_FOR_UPDATES = 'bUpdates'
        FIRST_START = 'bFirstStart'

    
    config = None
    _new_config = None

    def __new__(cls, *args, **kwargs):
        if not cls.config:
            cls.config = super(Config, cls).__new__(cls, *args, **kwargs)
            cls.config._initialize_config()
        return cls.config

    def _initialize_config(self):
        self.create_default_config()
        self._new_config.read('config.ini')
        self.save_config()
        
    def create_default_config(self):
        settings = {}
        settings[self.Settings.CHECK_FOR_UPDATES] = True
        settings[self.Settings.FIRST_START] = True

        self.save_settings(settings)


    def check_for_updates(self):        
        if self.get_value(self.Settings.FIRST_START):
            return False
        
        return self.get_value(self.Settings.CHECK_FOR_UPDATES)

    def save_settings(self, settings: dict[Settings]):
        # Make changes to the config without saving the file
        if self._new_config is None:
            self._new_config = configparser.ConfigParser()
            self._new_config.optionxform = str
            self._new_config.read('config.ini')

        for setting in settings:
            section = self._get_section(setting)
            value = self._convert_value_to_config_value(setting, settings[setting])
            self._new_config.set(section, setting.value, value)

    def save_config(self):
        # Save the config file with all the new changes
        if self._new_config is None:
            return
        
        with open('config.ini', 'w') as configfile:
            self._new_config.write(configfile, False)

        # read the new config
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

        self._new_config = None

    def _convert_value_to_config_value(self, setting: Settings, value) -> str:
        match setting.value[0]:
            case 'b':
                return '1' if value else '0'
            
    def _get_section(self, setting: Settings):
        config = {
            'General': ['bUpdates'],
            'Misc': ['bFirstStart']
        }

        for section, settings in config.items():
            if setting.value in settings:
                return section
            
    def get_value(self, setting: Settings):
        value = self.config.get(self._get_section(setting), setting.value)

        match setting.value[0]:
            case 'b':
                return value == '1'
