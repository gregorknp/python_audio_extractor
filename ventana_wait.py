from PyQt5 import QtCore, QtGui, QtWidgets, uic


class VentanaWait(QtWidgets.QDialog):
    """
    Class the represents the little wait window that pops up while the audio extration is being performed

    Attributes:
    -----------
    movie: QMovie
        Object the represents the gif object being displayed

    label: QLabel
        Label that shows a message to let the user know the audio is being extracted

    labelLoading: QLabel
        Label that contains the .gif image rendered while the audio is being extracted

    """

    def __init__(self, configuracion):
        """
        Constructor

        Loads the .ui file which contains the graphical elements of the window and shows the gif file while the
        audio is extracted. The window will be closed from the outside when the extraction has finished
        """
        super(VentanaWait, self).__init__()
        uic.loadUi("ventana_wait.ui", self)
        self.setWindowTitle(configuracion.lang_dict[configuracion.config_dict['idioma']]['wait.title'])

        # Loads the gif file in a QMovie object
        self.movie = QtGui.QMovie("./assets/loading.gif")  # TODO Make it configurable

        # Sets a text to inform the user the audio is being extracted
        self.label.setText(configuracion.lang_dict[configuracion.config_dict['idioma']]['wait.label'])

        # Loads de .gif file into a label, sets its size and gets displayed
        self.labelLoading.setMovie(self.movie)
        size = QtCore.QSize(200, 200)
        self.movie.setScaledSize(size)
        self.movie.start()  # Shows de .gif file
