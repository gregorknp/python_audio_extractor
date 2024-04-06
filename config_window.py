from PyQt5 import QtWidgets, QtCore, uic
import yaml
from config import Config

# TODO AL inicio las rutas a archivos tienen que estar vacias y que sea el usuario quien las rellene para que las rutas
# tengan formato windows o linux
# TODO La primera vez que se configure el programa, se tiene que indicar que hay que configurar las rutas
# TODO Añadir esta info en el manual de usuario

import logging


class ConfigWindow(QtWidgets.QDialog):
    """
    Attributes:
    -----------
    configuracion: Config
        Object to manage configuration

    cambio_idioma_signal: pyqtSignal
        Signal emitted when changes in configuration are saved


    Class methods:
    --------------
    save_changes:


    """

    # Signal to emit when
    cambio_idioma_signal = QtCore.pyqtSignal()

    def __init__(self, configuracion: Config):
        """
        Constructor method. It initializes class elements and connects class methods as event handlers of interface
        elements.

        :param configuracion:

        :returns None
        """
        super(ConfigWindow, self).__init__()
        uic.loadUi('pantalla_config.ui', self)  # Loads the .ui file that contains the user interface

        self.configuracion = configuracion

        # Connect class methods to graphical element events
        self.cambiar_path_button.clicked.connect(self.change_ffmpeg_path)
        self.acept_config_button.clicked.connect(self.save_changes)
        self.cancel_config_button.clicked.connect(self.cancel_changes)
        self.combobox_lang.currentIndexChanged.connect(self.change_language)

        # Se visualiza la configuracion del fichero
        self.label.setText(configuracion.config_dict["path_ffmpeg"])
        if self.label.text() is None:
            self.label.setText("Es necesario establecer un path")
            # TODO poner el texto en rojo y negrita

        # Adapt window size and prevent it from resizing
        self.setFixedSize(430, 444)

        # Translates all texts into the selected language
        self.change_texts(self.configuracion.config_dict['idioma'])
        logging.info("Configuration window creation")

    def save_changes(self):
        """
        Class method executed when the user clicks on "Acept" button to save changes in configuration.

        It updates both configuration file and dictionary with the changes the user made.
        Notifies the main thread that there has been a change.

        :return: None
        """
        self.configuracion.config_dict['path_ffmpeg'] = self.label.text()
        self.configuracion.config_dict['idioma'] = self.combobox_lang.currentText()

        self.cambio_idioma_signal.emit()

        # Save configuration dictionary to file
        with open(self.configuracion.config_file, 'w') as outfile:
            yaml.dump(self.configuracion.config_dict, outfile, default_flow_style=False)

        logging.info("There have been some changes in configuration")

        self.close()

    def cancel_changes(self):
        """
        Class method executed when the user clicks on "Cancel" button.

        Closes configuration window without making any changes in configuration.

        :return: None
        """

        logging.info("Leaving configuration window without making any changes")
        self.close()

    def change_ffmpeg_path(self):
        """
        Class method executed when the user clicks on the button to look for ffmepg executable file

        Shows a QFileDialog to select the ffmpeg executable file. If the path is not empty, shows the full path in a
        label.

        :return: None
        """
        try:
            caption = self.configuracion.lang_dict[self.configuracion.config_dict["idioma"]]["select_ffmpeg_path_capt"]
            fname = QtWidgets.QFileDialog.getExistingDirectory(self, caption, "")

            # Se pone la ruta del archivo en el cuadro de texto
            if fname:
                self.label.setText(str(fname))
                logging.info(f"ffmpeg full path selected: {str(fname)}")
        except Exception as e:
            error_logger = logging.getLogger("error_logger")
            error_logger.critical(f"An error has occurred: {e}", stack_info=True)

    def change_language(self):
        """
        Class method executed when a is selected in the combobox.

        Sets the current language and translates texts on the fly.

        :return: None
        """

        idioma_actual = str(self.combobox_lang.currentText())
        logging.info(f"Language selected: {idioma_actual}")
        self.change_texts(idioma_actual)

    def change_texts(self, idioma):
        """
        Class method executed when a language is selected in the combobox

        Changes the texts on the configuration window using the current language dictionary

        :return: None
        """
        self.lbl_sel_lang.setText(self.configuracion.lang_dict[idioma]['lbl_sel_lang'])
        self.cambiar_path_button.setText(self.configuracion.lang_dict[idioma]['cambiar_path_button'])
        self.setWindowTitle(self.configuracion.lang_dict[idioma]['window_title'])
        self.groupbox_lang.setTitle(self.configuracion.lang_dict[idioma]['groupbox_lang'])
        self.groupbox_ffmpeg_path.setTitle(self.configuracion.lang_dict[idioma]['groupbox_ffmpeg_path'])
        self.acept_config_button.setText(self.configuracion.lang_dict[idioma]['acept_config_button'])
        self.cancel_config_button.setText(self.configuracion.lang_dict[idioma]['cancel_config_button'])

        logging.info(f"Configuration window texts changed")

    def closeEvent(self, event):
        """
        Class method executed when the window is closed.

        :param event:

        :return: None
        """
        self.cancel_changes()
