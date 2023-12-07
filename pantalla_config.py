from PyQt5 import QtWidgets, QtCore, uic
import yaml
from config import Config

# TODO AL inicio las rutas a archivos tienen que estar vacias y que sea el usuario quien las rellene para que las rutas
# tengan formato windows o linux
# TODO La primera vez que se configure el programa, se tiene que indicar que hay que configurar las rutas


class PantallaConfig(QtWidgets.QDialog):

    cambio_idioma_signal = QtCore.pyqtSignal()

    def __init__(self, configuracion: Config):
        super(PantallaConfig, self).__init__()
        uic.loadUi('pantalla_config.ui', self)  # Se carga el fichero .ui que contiene los elementos graficos

        self.configuracion = configuracion

        # Se establecen los disparadores de eventos para los componentes
        self.cambiar_path_button.clicked.connect(self.cambiar_path)

        # Manejadores de los botones
        self.acept_config_button.clicked.connect(self.guardar_cambios)
        self.cancel_config_button.clicked.connect(self.cancelar_cambios)

        # Se mapea el evento de cambio de elemento seleccionado en el combo box
        self.combobox_lang.currentIndexChanged.connect(self.cambio_idioma)

        # Se visualiza la configuracion del fichero
        self.label.setText(configuracion.config_dict["path_ffmpeg"])
        if self.label.text() is None:
            self.label.setText("Es necesario establecer un path")
            # TODO poner el texto en rojo y negrita

        # Se establece el texto de los elementos graficos en funcion del idioma
        self.cambio_textos(self.configuracion.config_dict['idioma'])

    def guardar_cambios(self):
        """
        Se recoge la informacion de los campos y se guardan en el fichero de configuracion
        :return:
        """
        print("[guardar_cambios]")
        self.configuracion.config_dict['path_ffmpeg'] = self.label.text()
        self.configuracion.config_dict['idioma'] = self.combobox_lang.currentText()

        self.cambio_idioma_signal.emit()

        # Se abre el fichero para escritura y se vuelca el contenido de self.configuracion
        with open(self.configuracion.config_file, 'w') as outfile:
            yaml.dump(self.configuracion.config_dict, outfile, default_flow_style=False)

        # Se cierre la ventana
        self.close()

    def cancelar_cambios(self):
        """
        No se tienen en cuenta los cambios en la configuracion
        :return:
        """
        print("[cancelar_cambios]")

        # Se cierra la ventana sin hacer ningun cambio
        # Se cierre la ventana
        self.close()

    def cambiar_path(self):
        """
        Metodo que se ejecuta cuando se pincha en el boton de busqueda de fichero

        Muestra un dialogo para seleccionar el fichero de video.
        :return:
        """
        try:
            fname = QtWidgets.QFileDialog.getExistingDirectory(self, ('Seleccionar archivo de video'), "")

            print(f"DEBUG. Carpeta seleccionada: {fname}")

            # Se pone la ruta del archivo en el cuadro de texto
            self.label.setText(str(fname))
        except Exception as e:
            print(e)

    def cambio_idioma(self):
        """
        Metodo que se ejecuta cuando se cambia el idioma en el combo box de seleccion de idiomas

        Modifica los textos de la ventana de configuracion en caliente
        :return:
        """

        idioma_actual = str(self.combobox_lang.currentText())

        self.cambio_textos(idioma_actual)

    def cambio_textos(self, idioma):
        """
        Metodo que cambia los textos
        :return:
        """
        self.lbl_sel_lang.setText(self.configuracion.lang_dict[idioma]['lbl_sel_lang'])
        self.cambiar_path_button.setText(self.configuracion.lang_dict[idioma]['cambiar_path_button'])
        self.setWindowTitle(self.configuracion.lang_dict[idioma]['window_title'])
        self.groupbox_lang.setTitle(self.configuracion.lang_dict[idioma]['groupbox_lang'])
        self.groupbox_ffmpeg_path.setTitle(self.configuracion.lang_dict[idioma]['groupbox_ffmpeg_path'])
        self.acept_config_button.setText(self.configuracion.lang_dict[idioma]['acept_config_button'])
        self.cancel_config_button.setText(self.configuracion.lang_dict[idioma]['cancel_config_button'])

