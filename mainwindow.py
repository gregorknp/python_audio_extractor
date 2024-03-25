from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QPushButton
from pantalla_config import PantallaConfig
from functools import partial
from ventana_wait import VentanaWait
from config import Config
import sys
import subprocess
import os
import logging
from logging import config
import time


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

        # Se configura el sistema de logs
        logging.config.dictConfig(self.configuracion.config_dict['logging'])

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

        """
        Se inicializan los componentes de la ventana ventana_convertir
        """
        self.button_convertir.setEnabled(False)
        self.button_convertir.clicked.connect(self.convertir)
        self.button_sel_carpeta.clicked.connect(self.seleccionar_fichero_salida)
        self.but_back_to_paso_2.clicked.connect(self.go_back_to_paso_2)
        self.but_back_to_paso_1.clicked.connect(self.go_back_to_paso_1)
        self.line_edit_carpeta.textChanged.connect(partial(self.check_if_text, self.button_convertir))

        # Se ajustan las dimensiones de la ventana principal y se evita que se pueda redimensionar
        self.setFixedSize(860, 250)

        # Stream de audio que se convertira
        self.stream_seleccionado = None

        self.traducir_textos()
        logging.info("Inicio de la aplicacion")
        logging.debug("Inicio de la aplicacion")
        self.show()  # Muestra la ventana

    def go_back_to_paso_1(self):
        """
        Metodo que pone el foco en la ventana principal, independientemente de cual es la ventana actual

        Resetea elementos graficos y variables y se establece como widget actual la ventana principal

        :return: None
        """
        logging.info("Se vuelve a la ventana principal")
        self.limpia_ventana_2()
        self.limpia_ventana_1()

        # Se establece la ventana principal como el widget principal
        self.stackedWidget.setCurrentWidget(self.mainWindow)

        # Se aumenta el alto de la ventana para poder ver todos los componentes
        self.setFixedSize(860, 250)

    def go_back_to_paso_2(self):
        """
        Rutina que se ejecuta cuando se pincha el boton "Atras" de la ventana del paso 3.

        Limpia los campos de la ventana del paso 3 y establece el foco en la ventana de seleccion de stream

        :return:
        """
        logging.info("Volvemos a la ventana de seleccion del stream de audio")
        self.limpia_ventana_3()
        self.stackedWidget.setCurrentWidget(self.ventana_streams)
        self.setFixedSize(860, 620)

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
            logging.info("Vamos a la ventana de seleccion del audio a extraer")
            self.stackedWidget.setCurrentWidget(self.ventana_streams)

            # Se aumenta el alto de la ventana para poder ver todos los componentes
            self.setFixedSize(860, 620)

            self.get_info_file()
        else:
            logging.error(f"El archivo seleccionado: {self.lineEdit.text()} no existe")

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

        try:
            # Se forma el comando para obtener la informacion del video
            path_ffprobe = os.path.join(self.configuracion.config_dict['path_ffmpeg'], "ffprobe.exe")
            comando = [path_ffprobe,
                       str(self.lineEdit.text()),
                       "-show_streams",
                       "-print_format",
                       "json"]

            logging.debug(f"Comando: {comando}")

            # Se ejecuta el comando
            list_files = subprocess.run(comando, capture_output=True, text=True)
            logging.debug(f"Info devuelta por el comando: {list_files.stdout}")
            dict_info_peli = eval(list_files.stdout)

            # Despues, muestro la informacion de los streams disponibles
            for stream in dict_info_peli["streams"]:

                logging.debug(f"id: {stream['index']} tipo: {stream['codec_type']}")

                # Si es un audio, creo un boton con la informacion y lo añado a la lista de streams.
                lang_dict = self.configuracion.lang_dict[self.configuracion.config_dict['idioma']]
                if stream['codec_type'] == "audio":
                    stream_info = f"Stream: {stream['index']} {lang_dict['streamsBox.streams_layout.but.type']}: {stream['codec_type']}\n" \
                                  f"{lang_dict['streamsBox.streams_layout.but.codec']}: {stream['codec_name']} {lang_dict['streamsBox.streams_layout.but.lang']}: {stream.get('tags').get('language') if 'tags' in stream else 'None'}"
                    button = QPushButton(stream_info, self)
                    button.setObjectName(f"but_stream_{stream['index']}")

                    # Utilizo partial para poder pasar el index del stream como parametro
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

            # Error log
            error_logger = logging.getLogger("error_logger")
            error_logger.critical(f"Se ha producido el siguiente error: {e}")

            # Volvemos a la ventana anterior
            self.go_back_to_paso_1()

    def select_stream(self, stream):
        """
        Metodo que se ejecuta cuando se pincha sobre uno de los botones que representa un stream
        :return:
        """
        logging.info(f"Se ha seleccionado el stream #{stream['index']}")
        self.stream_seleccionado = stream

        # Se obtiene la informacion del stream seleccionado para mostrarse en pantalla
        atributos = [stream.get('tags').get("language"),
                     stream.get("codec_name"),
                     stream.get("codec_long_name"),
                     str(stream.get("channels")),
                     stream.get("channel_layout"),
                     str(stream.get("NUMBER_OF_FRAMES")),
                     str(stream.get("tags").get("NUMBER_OF_BYTES"))]

        # Se itera sobre las etiquetas del QVBoxLayout y se establece el texto con el correspondiente atributo
        for index in range(self.valores.count()):
            label = self.valores.itemAt(index).widget()
            label.setText(atributos[index])

        # Se habilita el boton de siguiente
        self.but_go_to_paso_3.setEnabled(True)

    def go_to_paso3(self):
        logging.info("Vamos a la ventana de extraccion del audio")
        self.stackedWidget.setCurrentWidget(self.ventana_convertir)

        # Se establece por defecto el nombre del fichero de entrada cambiando la extension por .mp4
        self.line_edit_carpeta.setText(f"{os.path.splitext(self.lineEdit.text())[0]}.mp4")

        self.setFixedSize(860, 320)

    def check_file_exists(self):
        """
        Metodo que verifica si el texto del cuadro de texto es un fichero valido

        TODO De momento solo verifico si el texto no es vacio
        :return:
        """
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
        # print(QtCore.QDir.toNativeSeparators(str(fname)))
        logging.info(f"Se selecciona archivo: {str(fname[0])}")

        # Se pone la ruta del archivo en el cuadro de texto
        self.lineEdit.setText(QtCore.QDir.toNativeSeparators(str(fname[0])))

    def show_config(self):
        """
        Muestra la ventana de configuracion de la aplicacion
        :return:
        """
        logging.info("Acceso a pantalla configuracion")
        self.pantalla_configuracion.show()

    def seleccionar_fichero_salida(self):
        """
        Metodo que se ejecuta cuando se pincha en el boton de busqueda de fichero

        Muestra un dialogo para seleccionar el fichero de video.
        :return:
        """
        try:
            out_filename = QtWidgets.QFileDialog.getSaveFileName(self, ("Especificar archivo de salida"),
                                                    # "./audio.mp4",
                                                    os.path.splitext(self.lineEdit.text())[0],
                                                    ("Audio (*.mp4)"))

            logging.info(f"Se seleccionado {str(out_filename[0])} como fichero de salida")
            self.line_edit_carpeta.setText(str(out_filename[0]))

        except Exception as e:
            error_logger = logging.getLogger("error_logger")
            error_logger.critical(f"Se ha producido el error: {e}", stack_info=True)

    def convertir(self):
        """
        Metodo que se ejecuta al pulsar el boton de convertir

        Crea un hilo que ejecuta el comando ffmpeg para extraer el audio. Muestra una ventana de espera para dar feedback
        al usuario.

        :return: None
        """

        # Hay que verificar si el fichero realmente existe, por si se ha modificado el contenido del cuadro de texto

        # Coge el nombre de la carpeta y el nombre del fichero y genera el fichero de salida
        out_filename = self.line_edit_carpeta.text()

        self.thread = QtCore.QThread()
        self.worker = Worker(self.stream_seleccionado, out_filename, self.configuracion, self.lineEdit.text())
        self.worker.moveToThread(self.thread)

        # Se mapean funciones manejadoras a los eventos del hilo
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.mata_gif)
        self.worker.inicio.connect(self.muestra_gif)

        # Comienza la conversion
        self.thread.start()

    def muestra_gif(self):
        """
        Metodo que muestra una ventana en la que aparece un gif informando al usuario que el proceso de extraccion de
        audio esta en ejecucion
        :return: None
        """
        self.ventana_espera = VentanaWait(self.configuracion)
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
        msg.setText(f"{self.configuracion.lang_dict[self.configuracion.config_dict['idioma']]['success_end_process']} "
                    f"{self.line_edit_carpeta.text()}")
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

        self.info_paso_1.setHtml(f"<body style=' font-family:'Segoe UI'; font-size:9pt; font-weight:400; "
                                 f"font-style:normal;>"
                                 f"<p style='margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; "
                                 f"-qt-block-indent:0; text-indent:0px;'><span style=' font-weight:700; "
                                 f"font-style:italic;'>{dict_idioma['info_paso_1.step']}</span></p>"
                                 f"<p style=' margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; "
                                 f"-qt-block-indent:0; text-indent:0px;'>{dict_idioma['info_paso_1.desc']}</p>"
                                 f"</body>")

        # Textos de la ventana de seleccion de stream
        self.info_video_box.setTitle(dict_idioma['info_video_box.title'])
        self.labelNombre.setText(dict_idioma['info_video_box.labelNombre'])
        self.labelRes.setText(dict_idioma['info_video_box.labelRes'])
        self.labelCodec.setText(dict_idioma['info_video_box.labelCodec'])

        self.streamsBox.setTitle(dict_idioma['streamsBox.title'])
        self.info_stream_box.setTitle(dict_idioma['info_stream_box.title'])

        self.but_back_to_paso_1.setText(dict_idioma['but_back_to_paso_1'])
        self.but_go_to_paso_3.setText(dict_idioma['but_go_to_paso_3'])

        self.info_paso_2.setHtml(f"<body style=' font-family:'Segoe UI'; font-size:9pt; font-weight:400; "
                                 f"font-style:normal;>"
                                 f"<p style='margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; "
                                 f"-qt-block-indent:0; text-indent:0px;'><span style=' font-weight:700; "
                                 f"font-style:italic;'>{dict_idioma['info_paso_2.step']}</span></p>"
                                 f"<p style=' margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; "
                                 f"-qt-block-indent:0; text-indent:0px;'>{dict_idioma['info_paso_2.desc']}</p>"
                                 f"</body>")

        # Textos de la ventana de seleccion de fichero de salida
        self.groupBox_2.setTitle(dict_idioma['groupBox_2.title'])
        self.but_back_to_paso_2.setText(dict_idioma['but_back_to_paso_2'])
        self.button_convertir.setText(dict_idioma['button_convertir'])
        self.button_sel_carpeta.setText(dict_idioma['button_sel_carpeta'])
        self.labelNombreCarpeta.setText(dict_idioma['labelNombreCarpeta'])
        self.info_paso_3.setHtml(f"<body style=' font-family:'Segoe UI'; font-size:9pt; font-weight:400; "
                                 f"font-style:normal;>"
                                 f"<p style='margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; "
                                 f"-qt-block-indent:0; text-indent:0px;'><span style=' font-weight:700; "
                                 f"font-style:italic;'>{dict_idioma['info_paso_3.step']}</span></p>"
                                 f"<p style=' margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; "
                                 f"-qt-block-indent:0; text-indent:0px;'>{dict_idioma['info_paso_3.desc']}</p>"
                                 f"</body>")


    def closeEvent(self, event):
        logging.info("Finaliza la aplicacion")


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

        logging.info("Se crea hilo para la extraccion del audio")

    def run(self):
        """
        Rutina que realiza el proceso de extracion del audio

        Ejecuta el comando ffmpeg con los parametros necesarios para la extraccion del audio.
        Tanto al inicio como al final de la extraccion, la clase emite señales para notificar a la clase
        principal el estado del proceso

        :return: None
        """
        inicio = time.time()
        logging.info("Comienza la extraccion del audio:")
        logging.info(f"Fichero origen: {self.path_fichero_video}")
        logging.info(f"Fichero destino: {self.path_fichero_salida}")
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

        logging.debug(f"Comando para extraer el audio: {" ".join(comando)}")
        try:
            list_files = subprocess.run(comando, capture_output=True, text=True)
        except Exception as e:
            error_logger = logging.getLogger(f"Se ha producido un error: {e}")
        finally:
            # Independientemente de si hay error, se informa que el proceso ha finalizado haciendo emit()
            # de la señal "finished".
            fin = time.time()
            logging.info(f"Finaliza el proceso de extraccion del audio. Tiempo de proceso: {(fin - inicio):.2f}s")
            self.finished.emit()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    app.exec()
