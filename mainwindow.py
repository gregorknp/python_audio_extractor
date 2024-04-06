from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QPushButton
from config_window import ConfigWindow
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
    """
    Class that encapsules the app main window logic.

    The main window basically consists of a stacker widget containing three windows:
    1. Main window. Allows us to select the video file we want to extract the audio from.
    2. Stream selection window. Shows all audio streams available to extract.
    3. Output file selection window. Allows us to select the name of the final audio file.
    """
    def __init__(self):
        """
        Class constructor

        It performs the following actions:
        1. Loads the mainwindow.ui file. This file was created using QTCreator and contains all graphical elements of the main window.
        2. Create connections between events in ui objects and the appropriate handler
        3. Initialize variables such as the window size, window title, set initial widget...
        4. Loads configuation file
        """
        super(MainWindow, self).__init__()
        uic.loadUi('mainwindow.ui', self)   # Graphical elements of the main window are loaded

        self.setWindowTitle("Extractor de audio")

        # Connection between object's events and handler
        self.lineEdit.textChanged.connect(partial(self.check_if_text, self.but_go_to_paso2))
        self.search_button.clicked.connect(self.search_video_file)
        self.but_go_to_paso2.clicked.connect(self.go_to_paso2)
        self.configButton.clicked.connect(self.show_config)  # TODO

        self.but_go_to_paso_3.clicked.connect(self.go_to_paso3)

        self.button_convertir.setEnabled(False)
        self.button_convertir.clicked.connect(self.convertir)
        self.button_sel_carpeta.clicked.connect(self.seleccionar_fichero_salida)
        self.but_back_to_paso_2.clicked.connect(self.go_back_to_paso_2)
        self.but_back_to_paso_1.clicked.connect(self.go_back_to_paso_1)
        self.line_edit_carpeta.textChanged.connect(partial(self.check_if_text, self.button_convertir))

        self.stackedWidget.setCurrentWidget(self.mainWindow)

        # Configuration load
        self.configuracion = Config('config/config.yml')

        # Creates the configuration dialog and creates a connection when the language changes to automatically
        # translate texts
        self.pantalla_configuracion = ConfigWindow(self.configuracion)
        self.pantalla_configuracion.cambio_idioma_signal.connect(self.traducir_textos)

        # Logging manager configuration using config.yml file
        logging.config.dictConfig(self.configuracion.config_dict['logging'])

        # Se crean las etiquetas del panel de informacion del stream
        # Se visualiza la informacion del stream en la seccion.
        campos = self.configuracion.lang_dict[self.configuracion.config_dict['idioma']]['info_stream_box.labels']

        for campo in campos:
            self.campos.addWidget(QtWidgets.QLabel(campo))
            self.valores.addWidget(QtWidgets.QLabel(""))  # Etiqueta vacia

        self.setFixedSize(860, 250)  # We set the size of the window and prevent it from resizing

        self.stream_seleccionado = None
        self.ventana_espera = None

        self.traducir_textos()  # Texts are translated according to current language
        logging.info("Application starts")
        logging.debug("Application starts")
        self.show()

    def go_back_to_paso_1(self):
        """
        Method that takes the user back to step 1 regardless which is the current window.

        It resets some graphical elements and sets the main window as current widget

        :return: None
        """
        logging.info("Going back to main window")
        self.limpia_ventana_2()
        self.limpia_ventana_1()

        self.stackedWidget.setCurrentWidget(self.mainWindow)

        # Fixing window size
        self.setFixedSize(860, 250)

    def go_back_to_paso_2(self):
        """
        Method invoked when cliking the "Back" button in step 3 window

        Clears graphical elements of step 3 window and set focus on stream selection window (step 2)

        :return: None
        """
        logging.info("Coing back to stream selection window")
        self.limpia_ventana_3()
        self.stackedWidget.setCurrentWidget(self.ventana_streams)
        self.setFixedSize(860, 620)

    def go_to_paso2(self):
        """
        Method that makes the transition from the main window (step 1) to the stream selection window (step 2).

        If the source video file exists:
         The stream selection window is set as current widget
         We get information about the source video file to be shown in the window
         Window size is fised
        else:
         An error message if displayed

        Important information is logged.

        :return: None
        """

        if self.check_file_exists():
            logging.info("Go to stream selection window")
            self.stackedWidget.setCurrentWidget(self.ventana_streams)
            self.setFixedSize(860, 620)
            self.get_info_file()
        else:
            logging.error(f"The selected file: {self.lineEdit.text()} does not exist")

            # Error message shown in a QMessageBox to give feedback to the user
            msg = QtWidgets.QMessageBox()
            msg.setText(f"The selected file: {self.lineEdit.text()} does not exist\n"
                        f"Please select an existing file")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.exec_()

    def get_info_file(self):
        """
        Method that gets some information from the video file that will be rendered in the window

        Information from both audio and video streams are displayed in the window, allowing the user to select the
        audio stream to extract using the corresponding button. When the button is clicked, the audio stream information
        is displayed.

        :return: None
        """
        try:
            # Command along with parameters to get the informacion of the video file
            path_ffprobe = os.path.join(self.configuracion.config_dict['path_ffmpeg'], "ffprobe.exe")
            comando = [path_ffprobe,
                       str(self.lineEdit.text()),
                       "-show_streams",
                       "-print_format",
                       "json"]

            logging.debug(f"Comando: {comando}")

            # Command execution
            list_files = subprocess.run(comando, capture_output=True, text=True)
            logging.debug(f"Info devuelta por el comando: {list_files.stdout}")
            dict_info_peli = eval(list_files.stdout)

            # We iterate over the streams of the file. for each stream...
            for stream in dict_info_peli["streams"]:

                logging.debug(f"id: {stream['index']} tipo: {stream['codec_type']}")

                # ... if it is an audio stream, we create a button labeled with the stream info, connect the button
                # with the method handler and add the button to the leayout
                lang_dict = self.configuracion.lang_dict[self.configuracion.config_dict['idioma']]
                if stream['codec_type'] == "audio":
                    stream_info = f"Stream: {stream['index']} {lang_dict['streamsBox.streams_layout.but.type']}: {stream['codec_type']}\n" \
                                  f"{lang_dict['streamsBox.streams_layout.but.codec']}: {stream['codec_name']} {lang_dict['streamsBox.streams_layout.but.lang']}: {stream.get('tags').get('language') if 'tags' in stream else 'None'}"
                    button = QPushButton(stream_info, self)
                    button.setObjectName(f"but_stream_{stream['index']}")

                    # "partial" is used to pass the stream as an argument to the hanlder
                    button.clicked.connect(partial(self.select_stream,
                                                   stream))
                    self.streams_layout.addWidget(button)
                # ... if it is a video stream, some information is extracted and rendered
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

            # A QMessageBox is shown to give feedback to the user
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText(mensaje)
            msg.setDefaultButton(QtWidgets.QMessageBox.Ok)
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.exec_()

            # Error log
            error_logger = logging.getLogger("error_logger")
            error_logger.critical(f"Se ha producido el siguiente error: {e}")

            # Go back to main window
            self.go_back_to_paso_1()

    def select_stream(self, stream):
        """
        Handler method triggered when the user clicks on an audio stream button

        We extract some fields from the stream such as the stream languaje or the codes name and visualize these fields
        in the form of labels in an specific panel of the window

        :param stream: Audio stream information associated with the button just clicked in dictionary format
        :return: None
        """
        logging.info(f"Se ha seleccionado el stream #{stream['index']}")
        self.stream_seleccionado = stream  # Class variable set as we will need the stream in the future

        # List created with information extracted from the audio stream.
        atributos = [stream.get('tags').get("language"),
                     stream.get("codec_name"),
                     stream.get("codec_long_name"),
                     str(stream.get("channels")),
                     stream.get("channel_layout"),
                     str(stream.get("NUMBER_OF_FRAMES")),
                     str(stream.get("tags").get("NUMBER_OF_BYTES"))]

        # We iterate over the labels of the QVBoxLayout and set its text using the information extracted from the audio
        # stream
        for index in range(self.valores.count()):
            label = self.valores.itemAt(index).widget()
            label.setText(atributos[index])

        # The button to go to the next window is enabled
        self.but_go_to_paso_3.setEnabled(True)

    def go_to_paso3(self):
        """
        Handler method triggered when the user clicks on the button "but_go_to_paso_3"

        The transition to step 3 window is logged in the log file, the step 3 window is set as the current window and
        the line edit field is filled with the full path of the source file changing the file extension to .mp4 by
        default. Additionally, the size of the window is set and resizing is disabled.

        :return: None
        """
        logging.info("Got to audio extraction window")
        self.stackedWidget.setCurrentWidget(self.ventana_convertir)
        self.line_edit_carpeta.setText(f"{os.path.splitext(self.lineEdit.text())[0]}.mp4")
        self.setFixedSize(860, 320)

    def check_file_exists(self):
        """
        Method that checks if the source video file selected already exists

        :return: True if the video file exists
                 False otherwise
        """
        return os.path.exists(self.lineEdit.text())

    def check_if_text(self, boton: QPushButton):
        """
        Handler method triggered when the content of a line edit element changes.

        This method is generic and can be applied to several line edit elements as far as we pass the right button as
        a parameter

        If there is text in the line edit, the button passed as parameter is enabled.
        If there is no text, the button is disabled.

        The idea is to make sure we can transition to the next step in the process.

        :param boton. Button to go to the next step in the process
        :return: None
        """
        line_edit = self.sender()
        if line_edit.text():
            boton.setEnabled(True)
        else:
            boton.setEnabled(False)

    def search_video_file(self):
        """
        Handler method triggered when the user clicks on the button to search the source video file locally in the system

        Shows a QFileDialog to make the search of the file easier. The full path of the file selected is placed in the
        line edit field.

        :return: None
        """
        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Seleccionar archivo de video',
                                            'c:\\', "Video files (*.mkv);;All files (*) ")

        logging.info(f"Selected file: {str(fname[0])}")
        self.lineEdit.setText(QtCore.QDir.toNativeSeparators(str(fname[0])))

    def show_config(self):
        """
        Shows the configuration screen

        This window allows us to change some application settings

        :return: None
        """
        logging.info("Access to configuration screen")
        self.pantalla_configuracion.show()

    def seleccionar_fichero_salida(self):
        """
        Handler method triggered when the user clicks on "Select file" button in step 3 window.

        A QFileDialog shows up and allow us to select the output file. The text field next to the button is filled
        with the path of the selected file.

        :return: None
        """
        try:
            out_filename = QtWidgets.QFileDialog.getSaveFileName(self, "Select output file",
                                                    os.path.splitext(self.lineEdit.text())[0],
                                                    "Audio (*.mp4)")

            logging.info(f"You have selected {str(out_filename[0])} as output file")
            self.line_edit_carpeta.setText(str(out_filename[0]))

        except Exception as e:
            error_logger = logging.getLogger("error_logger")
            error_logger.critical(f"The following error has ocurred: {e}", stack_info=True)

    def convertir(self):
        """
        Handler method triggered when the user clicks on "Convert" button.

        It creates a Worker object that performs the extraction of the audio on its "run" method. This object is
        moved to a thread so the extraction is executed in the background.

        :return: None
        """

        # Gets the output file path from the text field
        out_filename = self.line_edit_carpeta.text()

        self.thread = QtCore.QThread()
        self.worker = Worker(self.stream_seleccionado, out_filename, self.configuracion, self.lineEdit.text())
        self.worker.moveToThread(self.thread)

        # We associate methods with events in the thread
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.mata_gif)
        self.worker.inicio.connect(self.muestra_gif)

        # Audio extraction starts
        self.thread.start()

    def muestra_gif(self):
        """
        Method that shows a gif file to give feedback to the user while the audio is extracted.

        :return: None
        """
        self.ventana_espera = VentanaWait(self.configuracion)
        self.ventana_espera.show()

    def mata_gif(self):
        """
        Method executed when the thread finishes extracting the audio.

        The window with the waiting gif closes and shows a QMessageBox saying that the proccess has ended.
        The step 3 window is cleared and we go back to step 1 window

        :return: None
        """
        self.ventana_espera.close()

        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Info")
        msg.setText(f"{self.configuracion.lang_dict[self.configuracion.config_dict['idioma']]['success_end_process']} "
                    f"{self.line_edit_carpeta.text()}")
        msg.setDefaultButton(QtWidgets.QMessageBox.Ok)
        msg.exec_()

        # Step 3 is cleared and go back to step 1 window
        self.limpia_ventana_3()
        self.go_back_to_paso_1()

    def limpia_ventana_1(self):
        """
        Method that clears graphic elements of step 1 window.

        Empties the text field and disables "Next" button.

        :return: None
        """
        self.lineEdit.setText("")
        self.but_go_to_paso2.setEnabled(False)

    def limpia_ventana_2(self):
        """
        Method the clears graphic elements of step 2 window

        Clears all labels, removes all audio stream buttons, clears "Stream information" panel and
        disables "Next" button

        :return: None
        """

        # Clars labels setting its texts to ""
        self.labelNombreStr.setText("")
        self.labelResStr.setText("")
        self.labelCodecStr.setText("")

        # This iterates over all buttons in streams_layout QVBoxLayout and removes them from the layout.
        # NOTE. We have to use itemAt(0) because when we remove an item in position 0, the next element occupies
        # position 0
        for _ in range(self.streams_layout.count()):
            self.streams_layout.removeWidget(self.streams_layout.itemAt(0).widget())

        # This empties "Stream information" labels by iterating over al items in valores QVBoxLayout and setting its
        # text to ""
        for index in range(self.valores.count()):
            self.valores.itemAt(index).widget().setText("")

        self.but_go_to_paso_3.setEnabled(False)

    def limpia_ventana_3(self):
        """
        Method that clears graphic elements in step 3 window

        The text filed is emptied and "Convert" button is disabled

        :return: None
        """
        self.line_edit_carpeta.setText("")
        self.button_convertir.setEnabled(False)

    def traducir_textos(self):
        """
        Method executed when the curren tlanguage is changed from the configuration window or when the application
        starts.

        It changes most of the texts displayed on the screen.

        :return: None
        """

        # We get the dictionary which contains the texts in the selected language...
        dict_idioma = self.configuracion.lang_dict[self.configuracion.config_dict['idioma']]

        # ... and the texts on the screen are changed accordingly
        # Main window texts
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

        # Stream selection window
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

        # Output file selection window
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
        """
        Method that overwrites closeEvent on QObject. We simply register an application end event.
        :param event:
        :return: None
        """
        logging.info("Application ends execution")


class Worker(QtCore.QObject):
    """
    Clase que encapsula la extracion de la pista de audio. El metodo run se ejecutara en un hilo para no congelar
    la interfaz

    Attributes:
    ----------
    stream_seleccionado:
        Information of the audio stream that will be extracted from the video

    path_fichero_salida: String
        Output file fuill path

    configuracion: Config
        Configuration object. Intended for text translation

    path_fichero_video: String
        Source video file full path

    """

    # Signals used to inform about the state of the thread:
    finished = QtCore.pyqtSignal()  # Signal emitted when the job is finished
    inicio = QtCore.pyqtSignal()   # Signal emitted when the job if started

    def __init__(self, stream_seleccionado, path_fichero_salida, configuracion, path_fichero_video):
        """
        Constructor method. It initializes class variables

        :param stream_seleccionado:
        :param path_fichero_salida:
        :param configuracion:
        :param path_fichero_video:
        """
        super(Worker, self).__init__()
        self.stream_seleccionado = stream_seleccionado
        self.path_fichero_salida = path_fichero_salida
        self.configuracion = configuracion
        self.path_fichero_video = path_fichero_video

        logging.info("Worker class is created to extract the audio")

    def run(self):
        """
        Method that performs the extraction of the audio track

        It executes the ffmpeg command with the parameters needed to extract the audio. Both at start and end of the
        process signals are emitted in order to notify the main thread

        :return: None
        """
        start = time.time()
        logging.info("Audio extraction starts:")
        logging.info(f"Source video file: {self.path_fichero_video}")
        logging.info(f"Output audio file: {self.path_fichero_salida}")
        self.inicio.emit()  # Main thread is informed that the extraction has started

        comando = [f"{self.configuracion.config_dict['path_ffmpeg']}\\ffmpeg.exe",  # ffmpeg.exe full path
                   "-y",  # Used to overwrite the output file if it already exists
                   "-i",  # option to specify the input file
                   self.path_fichero_video,  # input file
                   "-map",  # used to select which audio stream is placed in the output file
                   f"0:{self.stream_seleccionado['index']}",  # Audio track index
                   "-acodec",  # to set the audio codec to use
                   "libmp3lame",  # encoding library used to create the audio file
                   self.path_fichero_salida  # Output full path
                   ]

        logging.debug(f"Full command to extract the audio: {" ".join(comando)}")
        try:
            subprocess.run(comando, capture_output=True, text=True)  # Command execution
        except Exception as e:
            logging.getLogger(f"The following errro has occurred: {e}")
        finally:
            # Regardless of failure or success in the process, we emit a signal to notify the main thread that the
            # jos has ended
            end = time.time()
            logging.info(f"Audio extraction ends. Process duration: {(end - start):.2f}s")
            self.finished.emit()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    app.exec()
