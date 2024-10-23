import os.path
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QStatusBar, QTableWidget, QGraphicsView, QScrollArea,
                             QGraphicsScene, QPushButton, QComboBox, QLabel, QWidget, QSizePolicy, QGridLayout,
                             QFileDialog)


# ----------------------------------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------------------------------


class SpotlightWindow(QDialog):
    def __init__(self, main_window, parent=None):
        super(SpotlightWindow, self).__init__(parent)
        self.main_window = main_window
        self.image_window = main_window.image_window
        self.label_window = main_window.label_window
        self.annotation_window = main_window.annotation_window

        self.model_path = ""
        self.loaded_model = None

        self.setWindowTitle("Spotlight")
        self.setWindowState(Qt.WindowMaximized)  # Ensure the dialog is maximized

        # Create the main layout
        self.main_layout = QVBoxLayout(self)

        # Add a status bar widget along the top
        self.status_bar = QStatusBar(self)

        # Multiselect dropdown for image paths
        self.image_dropdown = QComboBox()
        self.image_dropdown.setEditable(True)
        self.image_dropdown.addItem("All")  # Add "All" at the first index
        self.image_dropdown.addItems([os.path.basename(path) for path in self.image_window.image_paths])
        self.image_dropdown.setInsertPolicy(QComboBox.NoInsert)
        self.image_dropdown.setDuplicatesEnabled(False)
        self.image_dropdown.setToolTip("Select images")
        self.image_dropdown.currentIndexChanged.connect(self.filter_image_paths)

        # Multiselect dropdown for short code labels
        self.label_dropdown = QComboBox()
        self.label_dropdown.setEditable(True)
        self.label_dropdown.addItem("All")  # Add "All" at the first index
        self.label_dropdown.addItems([label.short_label_code for label in self.label_window.labels])
        self.label_dropdown.setInsertPolicy(QComboBox.NoInsert)
        self.label_dropdown.setDuplicatesEnabled(False)
        self.label_dropdown.setToolTip("Select labels")
        self.label_dropdown.currentIndexChanged.connect(self.filter_label_codes)

        # Multiselect dropdown for annotation options
        self.annotation_dropdown = QComboBox()
        self.annotation_dropdown.setEditable(True)
        self.annotation_dropdown.addItems(["All",
                                           "PatchAnnotations",
                                           "RectangleAnnotations",
                                           "PolygonAnnotations"])
        self.annotation_dropdown.setInsertPolicy(QComboBox.NoInsert)
        self.annotation_dropdown.setDuplicatesEnabled(False)
        self.annotation_dropdown.setToolTip("Select annotations")
        self.annotation_dropdown.currentIndexChanged.connect(self.filter_annotations)

        self.status_bar.addWidget(QLabel("Images:"))
        self.status_bar.addWidget(self.image_dropdown)
        self.status_bar.addWidget(QLabel("Labels:"))
        self.status_bar.addWidget(self.label_dropdown)
        self.status_bar.addWidget(QLabel("Annotations:"))
        self.status_bar.addWidget(self.annotation_dropdown)

        # Add a Deploy model button, and an apply model button on the far right side of the status bar
        self.deployed_model_text = QLabel(f"❌")
        self.status_bar.addPermanentWidget(self.deployed_model_text)
        self.deploy_model_button = QPushButton('Deploy Model', self)
        self.deploy_model_button.clicked.connect(self.deploy_model_dialog)
        self.deploy_model_button.setToolTip("Deploy a model")
        self.status_bar.addPermanentWidget(self.deploy_model_button)

        self.apply_model_button = QPushButton('Apply Model', self)
        self.apply_model_button.clicked.connect(self.apply_model)
        self.apply_model_button.setToolTip("Apply the deployed model")
        self.status_bar.addPermanentWidget(self.apply_model_button)

        self.main_layout.addWidget(self.status_bar)

        # Create a grid layout for the top half
        self.top_layout = QGridLayout()

        # Add a table widget on the left-side (top half)
        self.table_widget = QTableWidget(self)
        self.top_layout.addWidget(self.table_widget, 0, 0, 1, 1)

        # Add a GraphicsView on the right-side (top half)
        self.graphics_view = QGraphicsView(self)
        self.graphics_scene = QGraphicsScene(self)
        self.graphics_view.setScene(self.graphics_scene)
        self.top_layout.addWidget(self.graphics_view, 0, 1, 1, 1)

        self.main_layout.addLayout(self.top_layout)

        # Add a horizontal scrollable area to display graphic items (bottom half)
        self.scroll_area = QScrollArea(self)
        self.main_layout.addWidget(self.scroll_area)

        # Add Cancel, Apply, and Accept buttons on the far right side along the bottom
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addStretch(1)  # Add stretch to push buttons to the right

        self.cancel_button = QPushButton('Cancel', self)
        self.cancel_button.clicked.connect(self.close)
        self.cancel_button.setToolTip("Close the window")
        self.buttons_layout.addWidget(self.cancel_button)

        self.apply_button = QPushButton('Apply', self)
        self.apply_button.clicked.connect(self.apply)
        self.apply_button.setToolTip("Apply changes")
        self.buttons_layout.addWidget(self.apply_button)

        self.save_button = QPushButton('Save', self)
        self.save_button.clicked.connect(self.save)
        self.save_button.setToolTip("Save changes")
        self.buttons_layout.addWidget(self.save_button)

        self.main_layout.addLayout(self.buttons_layout)

    def filter_image_paths(self):
        selected_image_path = self.image_dropdown.currentText()
        self.status_bar.showMessage(f"Filtering image paths by: {selected_image_path}", 3000)
        # Implement image path filtering logic here

        self.update_table()

    def filter_label_codes(self):
        selected_label_code = self.label_dropdown.currentText()
        self.status_bar.showMessage(f"Filtering label codes by: {selected_label_code}", 3000)
        # Implement label code filtering logic here

        self.update_table()

    def filter_annotations(self):
        selected_annotation = self.annotation_dropdown.currentText()
        self.status_bar.showMessage(f"Filtering annotations by: {selected_annotation}", 3000)
        # Implement annotation filtering logic here

        self.update_table()

    def update_table(self):
        # Implement table update logic
        pass

    def update_graphics(self):
        # Implement graphics update logic
        pass

    def update_scroll_area(self):
        # Implement scroll area update logic
        pass

    def deploy_model_dialog(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self,
                                                   "Select Model File",
                                                   "",
                                                   "Model Files (*.h5 *.pt);;All Files (*)", options=options)
        if file_name:
            self.model_path = file_name
            self.deployed_model_text.setText(f"✅")
            self.status_bar.showMessage(f"Model deployed: {os.path.basename(self.model_path)}", 3000)

    def apply_model(self):
        if self.model_path:
            self.status_bar.showMessage("Model applied successfully.", 3000)
        else:
            self.status_bar.showMessage("No model deployed.", 3000)

    def apply(self):
        self.status_bar.showMessage("Changes applied successfully.", 3000)

    def save(self):
        self.status_bar.showMessage("Changes saved successfully.", 3000)