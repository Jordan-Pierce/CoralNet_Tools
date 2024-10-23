import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QStatusBar, QTableWidget, QGraphicsView, QScrollArea, QGraphicsScene)


# ----------------------------------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------------------------------


class SpotlightWindow(QWidget):
    def __init__(self, main_window, parent=None):
        super(SpotlightWindow, self).__init__(parent)
        self.main_window = main_window
        self.annotation_window = main_window.annotation_window

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # Create the main layout
        self.main_layout = QVBoxLayout(self)

        # Add a status bar widget along the top
        self.status_bar = QStatusBar(self)
        self.main_layout.addWidget(self.status_bar)

        # Create a horizontal layout for the top half
        self.top_layout = QHBoxLayout()

        # Add a table widget on the left-side (top half)
        self.table_widget = QTableWidget(self)
        self.top_layout.addWidget(self.table_widget)

        # Add a GraphicsView on the right-side (top half)
        self.graphics_view = QGraphicsView(self)
        self.graphics_scene = QGraphicsScene(self)
        self.graphics_view.setScene(self.graphics_scene)
        self.top_layout.addWidget(self.graphics_view)

        self.main_layout.addLayout(self.top_layout)

        # Add a horizontal scrollable area to display graphic items (bottom half)
        self.scroll_area = QScrollArea(self)
        self.main_layout.addWidget(self.scroll_area)
