import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import os

from ultralytics import YOLO

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QStatusBar, QTableWidget, QGraphicsView, QScrollArea,
                             QGraphicsScene, QPushButton, QComboBox, QLabel, QWidget, QSizePolicy, QGridLayout,
                             QFileDialog, QMainWindow, QTableWidgetItem)

from toolbox.Annotations.QtPatchAnnotation import PatchAnnotation
from toolbox.Annotations.QtRectangleAnnotation import RectangleAnnotation
from toolbox.Annotations.QtPolygonAnnotation import PolygonAnnotation


# ----------------------------------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------------------------------


class SpotlightWindow(QMainWindow):
    def __init__(self, main_window, parent=None):
        super(SpotlightWindow, self).__init__(parent)
        self.main_window = main_window
        self.image_window = main_window.image_window
        self.label_window = main_window.label_window
        self.annotation_window = main_window.annotation_window

        self.filtered_images = []
        self.filtered_labels = []
        self.filtered_annotations = []

        self.model_path = ""
        self.loaded_model = None

        self.setWindowTitle("Spotlight")

        # Create a central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

    def showEvent(self, event):
        self.setup_ui()
        super(SpotlightWindow, self).showEvent(event)

    def closeEvent(self, event):
        # Do any cleanup here if needed
        self.main_window.spotlight_window = None  # Clear the reference in the main window
        event.accept()

    def setup_ui(self):
        # Clear the main layout to remove any existing widgets
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.filtered_images = []
        self.filtered_labels = []
        self.filtered_annotations = []

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
        self.image_dropdown.currentIndexChanged.connect(self.filter_images)

        # Multiselect dropdown for short code labels
        self.label_dropdown = QComboBox()
        self.label_dropdown.setEditable(True)
        self.label_dropdown.addItem("All")  # Add "All" at the first index
        self.label_dropdown.addItems([label.short_label_code for label in self.label_window.labels])
        self.label_dropdown.setInsertPolicy(QComboBox.NoInsert)
        self.label_dropdown.setDuplicatesEnabled(False)
        self.label_dropdown.setToolTip("Select labels")
        self.label_dropdown.currentIndexChanged.connect(self.filter_labels)

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
        self.status_bar.addPermanentWidget(self.deploy_model_button)

        self.apply_cluster_button = QPushButton('Apply Clustering', self)
        self.apply_cluster_button.clicked.connect(self.apply_clustering)
        self.status_bar.addPermanentWidget(self.apply_cluster_button)

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

    def filter_images(self):
        # Get all the selected images
        if self.image_dropdown.itemText(0) == "All":
            # If the first item is "All", then all images are selected
            selected_images = self.image_window.image_paths
        else:
            selected_images = []
            # Otherwise, iterate through the dropdown and add all selected images
            for i in range(self.image_dropdown.count()):
                if self.image_dropdown.itemText(i) != "All":
                    selected_images.append(self.image_dropdown.itemText(i))

        # TODO fix this
        self.filtered_images = list(set(selected_images))
        self.update_table()

    def filter_labels(self):
        # Get all the selected labels
        if self.label_dropdown.itemText(0) == "All":
            # If the first item is "All", then all labels are selected
            selected_labels = [label.short_label_code for label in self.label_window.labels]
        else:
            selected_labels = []
            # Otherwise, iterate through the dropdown and add all selected labels
            for i in range(self.label_dropdown.count()):
                if self.label_dropdown.itemText(i) != "All":
                    selected_labels.append(self.label_dropdown.itemText(i))

        self.filtered_labels = list(set(selected_labels))
        self.update_table()

    def filter_annotations(self):
        # Get all the selected annotations
        if self.annotation_dropdown.itemText(0) == "All":
            # If the first item is "All", then all annotations are selected
            selected_annotations = ["PatchAnnotations", "RectangleAnnotations", "PolygonAnnotations"]
        else:
            selected_annotations = []
            # Otherwise, iterate through the dropdown and add all selected annotations
            for i in range(self.annotation_dropdown.count()):
                if self.annotation_dropdown.itemText(i) != "All":
                    selected_annotations.append(self.annotation_dropdown.itemText(i))

        self.filtered_annotations = list(set(selected_annotations))
        self.update_table()

    def update_table(self):
        # Clear the table before populating it with new data
        self.table_widget.clear()
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(0)

        # Set the column headers
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["Label Short Code", "Label Long Code", "Image Path", "Annotation Type"])

        # Populate the table with filtered annotations
        for annotation in self.annotation_window.annotations_dict.values():
            annotation_dict = annotation.to_dict()
            if (annotation_dict['image_path'] in self.filtered_images and
                annotation_dict['label_short_code'] in self.filtered_labels and
                type(annotation).__name__ in self.filtered_annotations):
                row_position = self.table_widget.rowCount()
                self.table_widget.insertRow(row_position)
                self.table_widget.setItem(row_position, 0, QTableWidgetItem(annotation_dict['label_short_code']))
                self.table_widget.setItem(row_position, 1, QTableWidgetItem(annotation_dict['label_long_code']))
                self.table_widget.setItem(row_position, 2, QTableWidgetItem(annotation_dict['image_path']))
                self.table_widget.setItem(row_position, 3, QTableWidgetItem(type(annotation).__name__))

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
                                                   "Model Files (*.pt);;All Files (*)", options=options)
        if file_name:
            self.load_model(file_name)

            if self.loaded_model:
                self.model_path = file_name
                self.deployed_model_text.setText(f"✅")
                self.status_bar.showMessage(f"Model deployed: {os.path.basename(self.model_path)}", 3000)
            else:
                self.status_bar.showMessage("Model failed to deploy.", 3000)

    def load_model(self, model_path):
        if not os.path.exists(model_path):
            self.status_bar.showMessage("Model file does not exist.", 3000)
            return

        try:
            self.loaded_model = YOLO(model_path, task='classify')
            self.model_path = model_path

        except Exception as e:
            self.status_bar.showMessage("Model failed to load.", 3000)

    def extract_features(self):
        if not self.loaded_model:
            self.status_bar.showMessage("Model not deployed.", 3000)
            return

    def apply_clustering(self):
        if not self.loaded_model:
            self.status_bar.showMessage("Model not deployed.", 3000)
            return

    def apply(self):
        self.status_bar.showMessage("Changes applied successfully.", 3000)

    def save(self):
        self.status_bar.showMessage("Changes saved successfully.", 3000)
