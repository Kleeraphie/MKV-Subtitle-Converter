__version__ = "v1.2.5"

import configparser
from enum import Enum
import gettext
import os
from babel import Locale

class Config:
    class Settings(Enum):
        CHECK_FOR_UPDATES = 'bUpdates'
        LANGUAGE = 'sLanguage'
        FIRST_START = 'bFirstStart'

    
    config = None
    _new_config = None

    def __new__(cls, *args, **kwargs):
        if not cls.config:
            cls.config = super(Config, cls).__new__(cls, *args, **kwargs)
            cls.config._initialize_config()
        return cls.config

    def _initialize_config(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.create_default_config()
        self._new_config.read('config.ini')
        self.save_config()

        language: str = self.get_value(self.Settings.LANGUAGE) # get the language set in the config
        self.translation = gettext.translation('messages', 'languages', [language, 'en_US'], fallback=True)
        self.translation.install()
        
    def create_default_config(self):
        settings = {}
        settings[self.Settings.CHECK_FOR_UPDATES] = True
        settings[self.Settings.LANGUAGE] = 'en_US'
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

        # check if there are any changes
        if all(self.get_value(setting) == settings[setting] for setting in settings):
            return
        
        for setting in settings:
            section = self._get_section(setting)
            value = self._convert_value_to_config_value(setting, settings[setting])
            self._new_config.set(section, setting.value, value)

    def save_config(self):
        # Return if there are no changes
        if self._new_config is None:
            return
        
        # Save the config file with all the new changes
        with open('config.ini', 'w') as configfile:
            self._new_config.write(configfile, False)

        # read the new config
        # TODO: just do _initialize_config() but there is currently a bug
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

        language: str = self.get_value(self.Settings.LANGUAGE) # get the language set in the config
        self.translation = gettext.translation('messages', 'languages', [language, 'en_US'], fallback=True)
        self.translation.install()

        self._new_config = None

    def _convert_value_to_config_value(self, setting: Settings, value) -> str:
        match setting.value[0]:
            case 'b':
                return '1' if value else '0'
            case 's':
                return str(value)
            
    def _get_section(self, setting: Settings):
        config = {
            'General': ['bUpdates', 'sLanguage'],
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
            case 's':
                return value

    def get_version(self):
        return __version__
    
    def translate(self, text: str):
        return self.translation.gettext(text)
    
    def get_language(self):
        lang_code = self.get_value(self.Settings.LANGUAGE)
        return Locale.parse(lang_code).get_display_name()
    
    def get_languages(self):
        lang_codes = [code.name for code in os.scandir('languages') if code.is_dir()]
        languages = [Locale.parse(code).get_display_name() for code in lang_codes]

        return languages

    def convert_language_to_code(self, language: str):
        if language.strip() == '':
            return 'en_US'
        
        lang_codes = [code.name for code in os.scandir('languages') if code.is_dir()]
        languages = [Locale.parse(code).get_display_name() for code in lang_codes]
        return lang_codes[languages.index(language)]
