import yaml


class Config:
    """
    Clase que encapsula la configuracion de la aplicacion
    """

    def __init__(self, config_file):
        """
        Constructor de la clase
        :return:
        """
        # Inicializacion de atributos de clase
        self.config_file = config_file
        self.config_dict = None
        self.lang_dict = {}

        self.cargar_config()
        self.carga_fichero_idiomas()

    def cargar_config(self):
        """
        Abre y carga en memoria la informacion del fichero de configuracion
        :return:
        """

        with open(self.config_file) as file:
            self.config_dict = yaml.safe_load(file)

            print(self.config_dict)

    def check_config(self):
        """
        Verifica si tenemos que visualizar algun aviso por la configuracion, por ejemplo, si el path a los archivos
        ffmpeg no está configurado
        :return:
        """
        for key, value in self.config_dict.items():
            if not value:
                print(f"Aviso. El campo {key} no esta asignado. Se aplicara valor por defecto")

    def carga_fichero_idiomas(self):
        """
        Metodo que abre los ficheros de idiomas y los carga en diccionarios
        :return:
        """
        with open('config/texts_spa.yml') as file:
            self.lang_dict['Castellano'] = yaml.safe_load(file)

        with open('config/texts_eng.yml') as file:
            self.lang_dict['English'] = yaml.safe_load(file)
