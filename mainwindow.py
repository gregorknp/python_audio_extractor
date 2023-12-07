from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QPushButton
from pantalla_config import PantallaConfig
from functools import partial
from ventana_wait import VentanaWait
from config import Config
import sys
import yaml
import subprocess
import os


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('mainwindow.ui', self)   # Se carga el fichero .ui que contiene los elementos graficos

        self.setWindowTitle("Extractor de audio")  # Se establece el titulo de la ventana

        # Se establecen los disparadores de eventos para los componentes
        self.lineEdit.textChanged.connect(partial(self.check_if_text, self.but_go_to_paso2))
        self.search_button.clicked.connect(self.search_video_file)
        self.but_go_to_paso2.clicked.connect(self.go_to_paso2)
        self.configButton.clicked.connect(self.show_config)  # TODO

        self.stackedWidget.setCurrentWidget(self.mainWindow)

        # Carga y verificacion de configuracion
        self.configuracion = Config('config/config.yml')
#        self.check_config()

        # Se instancia la ventana de configuracion
        self.pantalla_configuracion = PantallaConfig(self.configuracion)

        self.pantalla_configuracion.cambio_idioma_signal.connect(self.traducir_textos)

        """
        Se inicializan los componentes de la ventana ventana_streams
        """
        self.but_go_to_paso_3.clicked.connect(self.go_to_paso3)

        # Se crean las etiquetas del panel de informacion del stream
        # Se visualiza la informacion del stream en la seccion.
        campos = self.configuracion.lang_dict[self.configuracion.config_dict['idioma']]['info_stream_box.labels']

        for campo in campos:
            self.campos.addWidget(QtWidgets.QLabel(campo))
            self.valores.addWidget(QtWidgets.QLabel(""))  # Etiqueta vacia

        print(self.valores.count())

        """
        Se inicializan los componentes de la ventana ventana_convertir
        """
        self.button_convertir.setEnabled(False)
        self.button_convertir.clicked.connect(self.convertir)
        self.button_sel_carpeta.clicked.connect(self.seleccionar_fichero_salida)
        self.but_back_to_paso_2.clicked.connect(self.go_back_to_paso_2)
        self.but_back_to_paso_1.clicked.connect(self.go_back_to_paso_1)
        self.line_edit_carpeta.textChanged.connect(partial(self.check_if_text, self.button_convertir))

        # Se ajusta el alto de la ventana al contenido para que no haya demasiado espacio vacío en la parte baja
        self.setGeometry(20,20, 831, 300)

        # Stream de audio que se convertira
        self.stream_seleccionado = None

        self.traducir_textos()


        self.show()  # Muestra la ventana

    def go_back_to_paso_1(self):
        """
        Metodo que pone el foco en la ventana principal, independientemente de cual es la ventana actual

        Resetea elementos graficos y variables y se establece como widget actual la ventana principal

        :return: None
        """

        self.limpia_ventana_2()
        self.limpia_ventana_1()

        # Se establece la ventana principal como el widget principal
        self.stackedWidget.setCurrentWidget(self.mainWindow)

    def go_back_to_paso_2(self):
        """
        Rutina que se ejecuta cuando se pincha el boton "Atras" de la ventana del paso 3.

        Limpia los campos de la ventana del paso 3 y establece el foco en la ventana de seleccion de stream

        :return:
        """

        self.limpia_ventana_3()
        self.stackedWidget.setCurrentWidget(self.ventana_streams)

    def go_to_paso2(self):
        """
        Rutina que realiza la transicion desde la ventana principal a la ventana que muestra la informacion del
        video y sus streams

        Verifica que el nmobre del archivo en el campo de texto existe.

        Establece como ventana actual la segunda ventana, obtiene la informacion del archivo de video, muestra la
        informacion y crea los botones que representan las pistas del archivo

        :return:
        """

        if self.check_file_exists():
            self.stackedWidget.setCurrentWidget(self.ventana_streams)

            # Se aumenta el alto de la ventana para poder ver todos los componentes
            self.setGeometry(20, 20, 831, 671)

            self.get_info_file()
        else:
            # Se crea un QMessageBox para mostrar el error al usuario
            msg = QtWidgets.QMessageBox()
            msg.setText(f"El archivo seleccionado: {self.lineEdit.text()} no existe\n"
                        f"Por favor, seleccione un archivo existente")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.exec_()

    def get_info_file(self):
        """
        Metodo que obtiene la informacion del archivo de video y rellena los elementos graficos de la ventana
        :return:
        """
        # Se obtiene la informacion del video y se muestra
        print(self.lineEdit.text())
        print(self.configuracion.config_dict['path_ffmpeg'])

        try:
            # Se forma el comando para obtener la informacion del video
            path_ffprobe = os.path.join(self.configuracion.config_dict['path_ffmpeg'], "ffprobe.exe")
            comando = [path_ffprobe,
                       str(self.lineEdit.text()),
                       "-show_streams",
                       "-print_format",
                       "json"]

            print(comando)
            list_files = subprocess.run(comando, capture_output=True, text=True)
            print(list_files.stdout)

            dict_info_peli = eval(list_files.stdout)
            print(type(dict_info_peli))

            # Despues, muestro la informacion de los streams disponibles
            for stream in dict_info_peli["streams"]:
                # Muesto info de debug TODO quitar
                print(f"id: {stream['index']} tipo: {stream['codec_type']}")

                # Si es un audio, creo un boton con la informacion y lo añado a la lista de streams.
                lang_dict = self.configuracion.lang_dict[self.configuracion.config_dict['idioma']]
                if stream['codec_type'] == "audio":
                    stream_info = f"Stream: {stream['index']} {lang_dict['streamsBox.streams_layout.but.type']}: {stream['codec_type']}\n" \
                                  f"{lang_dict['streamsBox.streams_layout.but.codec']}: {stream['codec_name']} {lang_dict['streamsBox.streams_layout.but.lang']}: {stream.get('tags').get('language') if 'tags' in stream else 'None'}"
                    button = QPushButton(stream_info, self)
                    button.setObjectName(f"but_stream_{stream['index']}")

                    # utilizo partial para poder pasar el index del stream como parametro
                    button.clicked.connect(partial(self.select_stream,
                                                   stream))
                    self.streams_layout.addWidget(button)
                # Si el stream es de video, recojo la informacion y la coloco en su seccion
                elif stream['codec_type'] == "video":
                    nombre_video = stream.get('tags').get('title') if 'tags' in stream else self.lineEdit.text()
                    self.labelNombreStr.setText(nombre_video)
                    self.labelResStr.setText(f"{stream['width']}x{stream['width']}")
                    self.labelCodecStr.setText(f"{stream['codec_name']}")

        except Exception as e:
            exception = e.__class__.__name__
            if exception == "FileNotFoundError":
                mensaje = f"No se ha encontrado {path_ffprobe}. Revise configuracion"
            else:
                mensaje = e

            # Se muestra un mensaje incidando el error
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText(mensaje)
            msg.setDefaultButton(QtWidgets.QMessageBox.Ok)
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.exec_()

            # Volvemos a la ventana anterior
            self.go_back_to_paso_1()

    def select_stream(self, stream):
        """
        Metodo que se ejecuta cuando se pincha sobre uno de los botones que representa un stream
        :return:
        """
        print(f"Se ha seleccionado el stream {stream['index']}")
        self.stream_seleccionado = stream

        atributos = []
        atributos.append(stream.get('tags').get("language"))
        atributos.append(stream.get("codec_name"))
        atributos.append(stream.get("codec_long_name"))
        atributos.append(str(stream.get("channels")))
        atributos.append(stream.get("channel_layout"))
        atributos.append(str(stream.get("NUMBER_OF_FRAMES")))
        atributos.append(str(stream.get("tags").get("NUMBER_OF_BYTES")))

        for index in range(self.valores.count()):
            print(index, atributos[index])
            label = self.valores.itemAt(index).widget()
            label.setText(atributos[index])

        # Se habilita el boton de siguiente
        self.but_go_to_paso_3.setEnabled(True)

    def go_to_paso3(self):
        self.stackedWidget.setCurrentWidget(self.ventana_convertir)

    def check_file_exists(self):
        """
        Metodo que verifica si el texto del cuadro de texto es un fichero valido

        TODO De momento solo verifico si el texto no es vacio
        :return:
        """
        print(f"DEBUG. check_file_exists")
        return os.path.exists(self.lineEdit.text())

    def check_if_text(self, boton: QPushButton):
        """
        Rutina que se dispara cuando se cambiar el texto de un QLineEdit y que verifica si hay o no texto en el.

        En el caso de que haya texto, habilita la pulsacion del boton pasado como parametro.

        Esta rutina se emplea para asegurarnos que podemos pasar al siguiente paso en la aplicacion

        :return: None
        """
        line_edit = self.sender()  # Se obtiene el objeto  que ha disparado el evento
        if line_edit.text():
            print(f"DEBUG. Tenemos {str(line_edit.text())} en el cuadro de texto")
            boton.setEnabled(True)
        else:
            boton.setEnabled(False)

    def search_video_file(self):
        """
        Metodo que se ejecuta cuando se pincha en el boton de busqueda de fichero

        Muestra un dialogo para seleccionar el fichero de video.
        :return:
        """
        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Seleccionar archivo de video',
                                            'c:\\', "Video files (*.mkv);;All files (*) ")


        # Si el sistema es Windows
        print(QtCore.QDir.toNativeSeparators(str(fname)))

        print(f"DEBUG. Archivo seleccionado: {fname}")

        # Se pone la ruta del archivo en el cuadro de texto
        #self.lineEdit.setText(str(fname[0]))
        self.lineEdit.setText(QtCore.QDir.toNativeSeparators(str(fname[0])))

    def show_config(self):
        """
        Muestra la ventana de configuracion de la aplicacion
        :return:
        """
        self.pantalla_configuracion.show()

    def seleccionar_fichero_salida(self):
        """
        Metodo que se ejecuta cuando se pincha en el boton de busqueda de fichero

        Muestra un dialogo para seleccionar el fichero de video.
        :return:
        """
        try:
            # fname = QtWidgets.QFileDialog.getExistingDirectory(self, ('Seleccionar carpeta de salida'), "")
            #
            # print(f"DEBUG. Carpeta seleccionada: {fname}")
            #
            # # Se pone la ruta del archivo en el cuadro de texto
            # self.line_edit_carpeta.setText(str(fname))

            fileName = QtWidgets.QFileDialog.getSaveFileName(self, ("Especificar archivo de salida"),
                                                    "./audio.mp4",
                                                    ("Audio (*.mp4)"))

            print(fileName[0])
            self.line_edit_carpeta.setText(str(fileName[0]))

            # Se habilita el boton 'Convertir'
            self.button_convertir.setEnabled(True)

        except Exception as e:
            print(e)

    def convertir(self):
        """
        Metodo que se ejecuta al pulsar el boton de convertir

        Crea un hilo que ejecuta el comando ffmpeg para extraer el audio. Muestra una ventana de espera para dar feedback
        al usuario.

        :return:
        """

        # Hay que verificar si el fichero realmente existe, por si se ha modificado el contenido del cuadro de texto


        # Coge el nombre de la carpeta y el nombre del fichero y genera el fichero de salida
        nombre_fichero = self.line_edit_carpeta.text()
        print(f"[convertir] {nombre_fichero}")

        self.thread = QtCore.QThread()

        self.worker = Worker(self.stream_seleccionado, nombre_fichero, self.configuracion, self.lineEdit.text())

        self.worker.moveToThread(self.thread)

        # Se mapean funciones manejadoras a los eventos del hilo
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.mata_gif)
        self.worker.inicio.connect(self.muestra_gif)
        self.thread.start()

    def muestra_gif(self):
        """
        Metodo que muestra una ventana en la que aparece un gif informando al usuario que el proceso de extraccion de
        audio esta en ejecucion
        :return: None
        """
        self.ventana_espera = VentanaWait()
        self.ventana_espera.show()

    def mata_gif(self):
        """
        Metodo que se ejecuta cuando termina la tarea de extraer el audio

        Cierra la ventana con el gif de espera, muestra un mensaje indicando que el proceso ha temrinado y retorna a
        la ventana principal
        :return: None
        """
        self.ventana_espera.close()

        # Se un mensaje indicando que el proceso ha terminado
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Info")
        msg.setText(f"El audio ha sido extraido en {self.line_edit_carpeta.text()}")
        msg.setDefaultButton(QtWidgets.QMessageBox.Ok)
        msg.exec_()

        # Limpiamos ventana_convertir
        self.limpia_ventana_3()

        #  y volvemos a la pantalla principal
        self.go_back_to_paso_1()

    def limpia_ventana_1(self):
        """
        Rutina que limpia los elementos graficos de la ventana principal
        :return:
        """

        # Se limpia el campo de texto
        self.lineEdit.setText("")

        # Se deshabilita el boton "Siguiente"
        self.but_go_to_paso2.setEnabled(False)

    def limpia_ventana_2(self):
        """
        Rutina que limpia los elementos graficos de la ventana del paso 2

        :return:
        """

        # Se limpia la seccion "Informacion video"
        self.labelNombreStr.setText("")
        self.labelResStr.setText("")
        self.labelCodecStr.setText("")

        # Se eliminan los botones de la seccion "Streams de audio".
        # NOTA. no puedo utilizar index para acceder a los elementos porque al eliminar el elemento de posicion x,
        # el elemento de posicion x + 1 pasa a ocupar la posicion x. Entonces tengo que eliminar siempre el elemento de
        # posicion 0
        for _ in range(self.streams_layout.count()):
            self.streams_layout.removeWidget(self.streams_layout.itemAt(0).widget())

        # Se limpia la seccion "Informacion stream"
        for index in range(self.valores.count()):
            self.valores.itemAt(index).widget().setText("")

        # Se deshabilita el boton "Siguiente"
        self.but_go_to_paso_3.setEnabled(False)

    def limpia_ventana_3(self):
        """
        Rutina que limpia los elementos graficos de la ventana del paso 3
        :return:
        """

        # Limpiamos ventana_convertir
        self.line_edit_carpeta.setText("")
        self.button_convertir.setEnabled(False)

    def traducir_textos(self):
        """
        Rutina que se ejecuta cuando se cambia el idioma de la ventana de configuracion o cuando se arranca la
        aplicacion para establecer los textos en el idioma actualmente configurado

        Modifica el texto de los elementos graficos en caliente
        :return:
        """
        # Culturilla. Como en python los parametros son pasados "por referencia" cuando cambio el idioma en la
        # ventana de configuracion, el valor en self.configuracion.config_dict['idioma'] ya se ha actualizado aqui!
        # asi que lo puedo utilizar directamente

        # Se obtiene el idioma actual
        dict_idioma = self.configuracion.lang_dict[self.configuracion.config_dict['idioma']]

        # y se cambian todos los textos de la interfaz
        # Se modifican los textos de la ventana principal
        self.setWindowTitle(dict_idioma['mainwindow.title'])
        self.label_sel_fich_video.setText(dict_idioma['label_sel_fich_video'])
        self.search_button.setText(dict_idioma['search_button'])
        self.but_go_to_paso2.setText(dict_idioma['but_go_to_paso2'])

        # Textos de la ventana de seleccion de stream
        self.info_video_box.setTitle(dict_idioma['info_video_box.title'])
        self.labelNombre.setText(dict_idioma['info_video_box.labelNombre'])
        self.labelRes.setText(dict_idioma['info_video_box.labelRes'])
        self.labelCodec.setText(dict_idioma['info_video_box.labelCodec'])

        self.streamsBox.setTitle(dict_idioma['streamsBox.title'])
        self.info_stream_box.setTitle(dict_idioma['info_stream_box.title'])

        self.but_back_to_paso_1.setText(dict_idioma['but_back_to_paso_1'])
        self.but_go_to_paso_3.setText(dict_idioma['but_go_to_paso_3'])

        # Textos de la ventana de seleccion de fichero de salida
        self.groupBox_2.setTitle(dict_idioma['groupBox_2.title'])
        self.but_back_to_paso_2.setText(dict_idioma['but_back_to_paso_2'])
        self.button_convertir.setText(dict_idioma['button_convertir'])
        self.button_sel_carpeta.setText(dict_idioma['button_sel_carpeta'])
        self.labelNombreCarpeta.setText(dict_idioma['labelNombreCarpeta'])


class Worker(QtCore.QObject):
    """
    Clase que encapsula la extracion de la pista de audio. El metodo run se ejecutara en un hilo para no congelar
    la interfaz
    """

    # Señales para informar del estado del hilo
    finished = QtCore.pyqtSignal()
    inicio = QtCore.pyqtSignal()

    def __init__(self, stream_seleccionado, path_fichero_salida, configuracion, path_fichero_video):
        super(Worker, self).__init__()
        self.stream_seleccionado = stream_seleccionado
        self.path_fichero_salida = path_fichero_salida
        self.configuracion = configuracion
        self.path_fichero_video = path_fichero_video

        print(self.stream_seleccionado)
        print(self.path_fichero_salida)
        print(self.path_fichero_video)

    def run(self):
        """
        Rutina que realiza el proceso de extracion del audio
        :return:
        """
        # Se muestra la ventana de esperar
        print("comienza el hilo")

        print("antes de ejecutar subprocess")
        self.inicio.emit()  # Se informa que el hilo ha comenzado

        # Si el fichero de salida existe, ffmpeg preguntara si queremos sobreescribir el fichero. Como no tenemos
        # control sobre la entrada por teclado, con '-y' siempre sobreescribimos el fichero.
        # No nos importa porque la seleccion del fichero de salida mediante QFileDialog.getSaveFileName ya avisa
        # de si queremos sobreescribir el archivo
        comando = [f"{self.configuracion.config_dict['path_ffmpeg']}\\ffmpeg.exe",
                   "-y",
                   "-i",
                   self.path_fichero_video,
                   "-map",
                   f"0:{self.stream_seleccionado['index']}",
                   "-acodec",
                   "libmp3lame",
                   self.path_fichero_salida]

        print(f"Comando para extraer el audio: {" ".join(comando)}")
        try:
            list_files = subprocess.run(comando, capture_output=True, text=True)
        except Exception as e:
            print(e)
        finally:
            # Independientemente de si hay error, se informa que el proceso ha finalizado haciendo emit()
            # de la señal "finished".
            print("finaliza el subprocess")
            self.finished.emit()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    app.exec()