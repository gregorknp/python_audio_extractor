import yaml
import logging


class Config:
    """
    Class that contains all the logic related to the application's configuration

    Attributes:
    ----------
    config_file: String
        Configuration file path relative to working directory

    config_dict: dict
        Dictionary that represents the information in the configuration file

    lang_dict: dict
        Dictionary which contains

    Methods:
    --------
    __init__: Cosntructor
    load_config_file: Loads configuration into memory
    check_config_params: Checks integrity of configuration params
    load_lang_files: Loads language files into memory
    """

    def __init__(self, config_file):
        """
        Class constructor.

        Initializes class variables, loads configuration from configuration file and loads translation texts
        :return:
        """
        self.config_file = config_file
        self.config_dict = None
        self.lang_dict = {}

        self.load_config_file()
        self.load_lang_files()

    def load_config_file(self):
        """
        Class method to load the configuration file and dump it into a dictionary

        :return: None
        """

        with open(self.config_file) as file:
            self.config_dict = yaml.safe_load(file)

            logging.debug(f"Configuration loaded")
            logging.debug(self.config_dict)

    def check_config_params(self):
        """
        Class method to check if there is any configuration parameter without being assigned

        :return: None
        """
        for key, value in self.config_dict.items():
            if not value:
                print(f"Warning. The parameter {key} is not assigned. Default value will be used")

    def load_lang_files(self):
        """
        Class method to open the files which contain text translation in spanish and english and dump their content
        into dictionary variables

        :return: None
        """
        with open('config/texts_spa.yml') as file:
            self.lang_dict['Castellano'] = yaml.safe_load(file)

        with open('config/texts_eng.yml') as file:
            self.lang_dict['English'] = yaml.safe_load(file)
