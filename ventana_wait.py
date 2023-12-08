from PyQt5 import QtCore, QtGui, QtWidgets, uic
import logging


class VentanaWait(QtWidgets.QDialog):

    def __init__(self):
        """
        Constructor de la ventana
        """
        super(VentanaWait, self).__init__()
        uic.loadUi("ventana_wait.ui", self)

        self.movie = QtGui.QMovie("./assets/loading.gif")  # TODO HAcerlo configurable
        size = QtCore.QSize(200, 200)
        self.labelLoading.setMovie(self.movie)
        self.movie.setScaledSize(size)
        self.movie.start()

