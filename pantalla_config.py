from PyQt5 import QtWidgets, uic
import yaml

# TODO AL inicio las rutas a archivos tienen que estar vacias y que sea el usuario quien las rellene para que las rutas
# tengan formato windows o linux
# TODO La primera vez que se configure el programa, se tiene que indicar que hay que configurar las rutas



class PantallaConfig(QtWidgets.QDialog):
    def __init__(self, configuracion):
        super(PantallaConfig, self).__init__()
        uic.loadUi('pantalla_config.ui', self)  # Se carga el fichero .ui que contiene los elementos graficos

        self.configuracion = configuracion

        # Se establecen los disparadores de eventos para los componentes
        (self.cambiar_path_button.clicked.
         connect(self.cambiar_path))

        # Manejadores de los botones
        self.aceptar_config_button.clicked.connect(self.guardar_cambios)
        self.cancelar_config_button.clicked.connect(self.cancelar_cambios)

        # Se visualiza la configuracion del fichero
        self.label.setText(configuracion["path_ffmpeg"])
        if self.label.text() is None:
            self.label.setText("Es necesario establecer un path")
            # TODO poner el texto en rojo y negrita

    def guardar_cambios(self):
        """
        Se recoge la informacion de los campos y se guardan en el fichero de configuracion
        :return:
        """
        print("[guardar_cambios]")
        self.configuracion['path_ffmpeg'] = self.label.text()

        # Se abre el fichero para escritura y se vuelca el contenido de self.configuracion
        with open('config.yml', 'w') as outfile:
            yaml.dump(self.configuracion, outfile, default_flow_style=False)

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
