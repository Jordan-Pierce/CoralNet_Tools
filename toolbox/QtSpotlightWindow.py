import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QStatusBar, QTableWidget, QGraphicsView, QScrollArea,
                             QGraphicsScene, QPushButton)


# ----------------------------------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------------------------------


class SpotlightWindow(QDialog):
    def __init__(self, main_window, parent=None):
        super(SpotlightWindow, self).__init__(parent)
        self.main_window = main_window
        self.annotation_window = main_window.annotation_window

        self.setWindowTitle("Spotlight")
        self.setWindowState(Qt.WindowMaximized)  # Ensure the dialog is maximized

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

        # Add Cancel, Apply, and Okay buttons
        self.buttons_layout = QHBoxLayout()
        self.cancel_button = QPushButton('Cancel', self)
        self.cancel_button.clicked.connect(self.close)
        self.buttons_layout.addWidget(self.cancel_button)
        self.apply_button = QPushButton('Apply', self)
        self.apply_button.clicked.connect(self.apply)
        self.buttons_layout.addWidget(self.apply_button)
        self.save_button = QPushButton('Save', self)
        self.save_button.clicked.connect(self.save)
        self.buttons_layout.addWidget(self.save_button)
        self.main_layout.addLayout(self.buttons_layout)

    def apply(self):
        pass

    def save(self):
        pass

    def update_table(self):
        pass

    def update_graphics(self):
        pass

    def update_scroll_area(self):
        pass