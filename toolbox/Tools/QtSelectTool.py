import warnings

from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsPolygonItem

from toolbox.Tools.QtTool import Tool
from toolbox.Annotations.QtRectangleAnnotation import RectangleAnnotation

warnings.filterwarnings("ignore", category=DeprecationWarning)


# ----------------------------------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------------------------------


class SelectTool(Tool):
    def __init__(self, annotation_window):
        super().__init__(annotation_window)
        self.cursor = Qt.PointingHandCursor
        self.resizing = False
        self.resize_handle = None
        self.resize_start_pos = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            position = self.annotation_window.mapToScene(event.pos())
            items = self.annotation_window.scene.items(position)
            rect_items = [item for item in items if isinstance(item, QGraphicsRectItem)]
            polygon_items = [item for item in items if isinstance(item, QGraphicsPolygonItem)]
            all_items = rect_items + polygon_items
            all_items.sort(key=lambda item: item.zValue(), reverse=True)

            for item in all_items:
                annotation_id = item.data(0)
                annotation = self.annotation_window.annotations_dict.get(annotation_id)
                if annotation and annotation.contains_point(position):
                    if isinstance(annotation, RectangleAnnotation):
                        self.resize_handle = self.detect_resize_handle(annotation, position)
                        if self.resize_handle:
                            self.resizing = True
                            self.resize_start_pos = position
                            break
                    self.annotation_window.select_annotation(annotation)
                    self.annotation_window.drag_start_pos = position
                    break

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.resizing and self.resize_handle:
            current_pos = self.annotation_window.mapToScene(event.pos())
            delta = current_pos - self.resize_start_pos
            self.resize_annotation(self.annotation_window.selected_annotation, delta)
            self.resize_start_pos = current_pos
        elif event.buttons() & Qt.LeftButton and self.annotation_window.selected_annotation:
            current_pos = self.annotation_window.mapToScene(event.pos())
            if not self.annotation_window.drag_start_pos:
                self.annotation_window.drag_start_pos = current_pos

            delta = current_pos - self.annotation_window.drag_start_pos
            new_center = self.annotation_window.selected_annotation.center_xy + delta

            if self.annotation_window.cursorInWindow(current_pos, mapped=True):
                selected_annotation = self.annotation_window.selected_annotation
                rasterio_image = self.annotation_window.rasterio_image
                self.annotation_window.set_annotation_location(selected_annotation.id, new_center)
                self.annotation_window.selected_annotation.create_cropped_image(rasterio_image)
                self.annotation_window.main_window.confidence_window.display_cropped_image(selected_annotation)
                self.annotation_window.drag_start_pos = current_pos

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.resizing:
            self.resizing = False
            self.resize_handle = None
            self.resize_start_pos = None
        self.annotation_window.drag_start_pos = None

    def detect_resize_handle(self, annotation, position):
        if isinstance(annotation, RectangleAnnotation):
            top_left = annotation.top_left
            bottom_right = annotation.bottom_right
            handles = {
                "top_left": QRectF(top_left.x() - 5, top_left.y() - 5, 10, 10),
                "top_right": QRectF(bottom_right.x() - 5, top_left.y() - 5, 10, 10),
                "bottom_left": QRectF(top_left.x() - 5, bottom_right.y() - 5, 10, 10),
                "bottom_right": QRectF(bottom_right.x() - 5, bottom_right.y() - 5, 10, 10),
            }
            for handle, rect in handles.items():
                if rect.contains(position):
                    return handle
        return None

    def resize_annotation(self, annotation, delta):
        if isinstance(annotation, RectangleAnnotation):
            if self.resize_handle == "top_left":
                annotation.top_left += delta
            elif self.resize_handle == "top_right":
                annotation.top_left.setY(annotation.top_left.y() + delta.y())
                annotation.bottom_right.setX(annotation.bottom_right.x() + delta.x())
            elif self.resize_handle == "bottom_left":
                annotation.top_left.setX(annotation.top_left.x() + delta.x())
                annotation.bottom_right.setY(annotation.bottom_right.y() + delta.y())
            elif self.resize_handle == "bottom_right":
                annotation.bottom_right += delta
            annotation.calculate_centroid()
            annotation.set_cropped_bbox()
            annotation.update_graphics_item()
