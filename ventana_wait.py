from PyQt5 import QtCore, QtGui, QtWidgets, uic
import logging


class VentanaWait(QtWidgets.QDialog):

    def __init__(self, configuracion):
        """
        Constructor de la ventana
        """
        super(VentanaWait, self).__init__()
        uic.loadUi("ventana_wait.ui", self)
        self.setWindowTitle(configuracion.lang_dict[configuracion.config_dict['idioma']]['wait.title'])

        self.movie = QtGui.QMovie("./assets/loading.gif")  # TODO HAcerlo configurable
        size = QtCore.QSize(200, 200)
        self.label.setText(configuracion.lang_dict[configuracion.config_dict['idioma']]['wait.label'])
        self.labelLoading.setMovie(self.movie)
        self.movie.setScaledSize(size)
        self.movie.start()

