import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget)


# ----------------------------------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------------------------------


class SpotlightWindow(QWidget):
    def __init__(self, main_window, parent=None):
        super(SpotlightWindow, self).__init__(parent)
        self.main_window = main_window
        self.annotation_window = main_window.annotation_window

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)