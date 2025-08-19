import warnings

from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QMouseEvent, QKeyEvent
from PyQt5.QtWidgets import QMessageBox

from coralnet_toolbox.Tools.QtTool import Tool
from coralnet_toolbox.Annotations.QtPolygonAnnotation import PolygonAnnotation

warnings.filterwarnings("ignore", category=DeprecationWarning)


# ----------------------------------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------------------------------


class PolygonTool(Tool):
    def __init__(self, annotation_window):
        super().__init__(annotation_window)
        self.cursor = Qt.CrossCursor
        self.default_cursor = Qt.ArrowCursor  # Explicitly set, if needed
        self.points = []
        self.drawing_continuous = False  # Flag to indicate continuous drawing mode
        self.epsilon = 1.0  # Default epsilon value for polygon simplification (in pixels)
        self.ctrl_pressed = False  # Flag to track Ctrl key state for straight line drawing
        self.last_click_point = None  # Store the last clicked point for straight line drawing
        self.edge_snap_threshold = 3  # Pixels from edge to trigger snapping
        self.corner_snap_threshold = 5  # Pixels from corner to trigger corner snapping

    def activate(self):
        self.active = True
        self.annotation_window.setCursor(self.cursor)

    def deactivate(self):
        self.active = False
        self.annotation_window.setCursor(self.default_cursor)
        self.clear_cursor_annotation()
        self.points = []
        self.drawing_continuous = False
        self.ctrl_pressed = False
        self.last_click_point = None

    def mousePressEvent(self, event: QMouseEvent):
        
        if not self.annotation_window.selected_label:
            QMessageBox.warning(self.annotation_window,
                                "No Label Selected",
                                "A label must be selected before adding an annotation.")
            return None
        
        # Enhanced cursor bounds check - allow clicks slightly outside for edge cases
        if not self.annotation_window.cursorInWindow(event.pos()) and not self.is_cursor_outside_image(event.pos()):
            return None

        if event.button() == Qt.LeftButton and not self.drawing_continuous:
            self.drawing_continuous = True
            self.annotation_window.unselect_annotations()
            scene_pos = self.annotation_window.mapToScene(event.pos())
            
            # Apply boundary clamping and snapping
            scene_pos = self.clamp_to_image_bounds(scene_pos)
            scene_pos = self.snap_to_corner_or_edge(scene_pos)
            
            self.points.append(scene_pos)
            self.last_click_point = scene_pos
            self.create_cursor_annotation(scene_pos)
        elif event.button() == Qt.LeftButton and self.drawing_continuous:
            scene_pos = self.annotation_window.mapToScene(event.pos())
            
            # Apply boundary clamping and snapping
            scene_pos = self.clamp_to_image_bounds(scene_pos)
            scene_pos = self.snap_to_corner_or_edge(scene_pos)
            
            if self.ctrl_pressed and self.last_click_point:
                # Add a straight line segment from last point to this click
                self.points.append(scene_pos)
                self.last_click_point = scene_pos
                self.update_cursor_annotation(scene_pos)
            else:
                # Free-hand: finish polygon
                self.points.append(scene_pos)
                self.annotation_window.unselect_annotations()
                annotation = self.create_annotation(scene_pos, finished=True)
                self.annotation_window.add_annotation_from_tool(annotation)
                self.drawing_continuous = False
                self.clear_cursor_annotation()
        elif event.button() == Qt.RightButton and self.drawing_continuous:
            pass
        else:
            self.cancel_annotation()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.drawing_continuous:
            scene_pos = self.annotation_window.mapToScene(event.pos())
            active_image = self.annotation_window.active_image
            pixmap_image = self.annotation_window.pixmap_image
            
            # Enhanced cursor checking - continue tracking even when slightly outside
            cursor_in_window = self.annotation_window.cursorInWindow(event.pos())
            cursor_outside_image = self.is_cursor_outside_image(event.pos())
            
            if active_image and pixmap_image and self.points:
                # Always clamp to image bounds and apply snapping
                clamped_pos = self.clamp_to_image_bounds(scene_pos)
                snapped_pos = self.snap_to_corner_or_edge(clamped_pos)
                
                if self.ctrl_pressed and self.last_click_point:
                    # Show a straight line preview from last point to cursor, do not modify self.points
                    self.update_cursor_annotation(snapped_pos)
                else:
                    # Free-hand: add points as the mouse moves, but only if cursor is reasonably close
                    if cursor_in_window or not cursor_outside_image:
                        self.points.append(snapped_pos)
                    else:
                        # If far outside, just update preview without adding points
                        pass
                    self.update_cursor_annotation(snapped_pos)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Backspace:
            self.cancel_annotation()
        elif event.key() == Qt.Key_Control:
            # Check if drawing is active and if Ctrl wasn't already pressed
            if self.drawing_continuous and not self.ctrl_pressed:
                self.ctrl_pressed = True
                cursor_pos = self.annotation_window.mapFromGlobal(self.annotation_window.cursor().pos())
                scene_pos = self.annotation_window.mapToScene(cursor_pos)
                
                # Apply boundary clamping and snapping
                scene_pos = self.clamp_to_image_bounds(scene_pos)
                scene_pos = self.snap_to_corner_or_edge(scene_pos)
                
                # Add the current point when switching to straight-line mode
                if not self.points or scene_pos != self.points[-1]:
                    self.points.append(scene_pos)
                self.last_click_point = scene_pos  # Update the anchor for the straight line
                self.update_cursor_annotation(scene_pos)  # Update preview for straight line

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Control:
            # Check if drawing is active and if Ctrl was actually pressed
            if self.drawing_continuous and self.ctrl_pressed:
                self.ctrl_pressed = False
                cursor_pos = self.annotation_window.mapFromGlobal(self.annotation_window.cursor().pos())
                scene_pos = self.annotation_window.mapToScene(cursor_pos)
                
                # Apply boundary clamping and snapping
                scene_pos = self.clamp_to_image_bounds(scene_pos)
                scene_pos = self.snap_to_corner_or_edge(scene_pos)
                
                # Add the current point when switching back to free-hand mode
                if not self.points or scene_pos != self.points[-1]:
                    self.points.append(scene_pos)
                # Update last_click_point, although less critical for free-hand mode start
                self.last_click_point = scene_pos
                self.update_cursor_annotation(scene_pos)  # Update preview for free-hand

    def cancel_annotation(self):
        self.points = []
        self.drawing_continuous = False
        self.clear_cursor_annotation()
        self.last_click_point = None

    def create_annotation(self, scene_pos: QPointF, finished: bool = False):
        if not self.annotation_window.active_image or not self.annotation_window.pixmap_image:
            return None

        # Create the annotation with current points
        # The polygon simplification is now handled inside the PolygonAnnotation class
        if finished and len(self.points) > 2:
            # Close the polygon
            self.points.append(self.points[0])

        # Create the annotation - will be simplified in the constructor
        annotation = PolygonAnnotation(self.points,
                                       self.annotation_window.selected_label.short_label_code,
                                       self.annotation_window.selected_label.long_label_code,
                                       self.annotation_window.selected_label.color,
                                       self.annotation_window.current_image_path,
                                       self.annotation_window.selected_label.id,
                                       self.annotation_window.main_window.label_window.active_label.transparency)

        if finished:
            # Reset the tool
            self.points = []
            self.drawing_continuous = False
            self.last_click_point = None

        return annotation
        
    def create_cursor_annotation(self, scene_pos: QPointF = None):
        """Create a polygon cursor annotation at the given position."""
        if not scene_pos or not self.annotation_window.selected_label or not self.annotation_window.active_image:
            self.clear_cursor_annotation()
            return

        if self.drawing_continuous and len(self.points) > 0:
            # Apply boundary clamping and snapping to the preview position
            clamped_pos = self.clamp_to_image_bounds(scene_pos)
            snapped_pos = self.snap_to_corner_or_edge(clamped_pos)
            
            # Determine points for preview: always include current scene_pos
            preview_points = self.points + [snapped_pos]

            # Create the preview annotation using preview_points
            annotation = PolygonAnnotation(
                preview_points,
                self.annotation_window.selected_label.short_label_code,
                self.annotation_window.selected_label.long_label_code,
                self.annotation_window.selected_label.color,
                self.annotation_window.current_image_path,
                self.annotation_window.selected_label.id,
                self.annotation_window.main_window.label_window.active_label.transparency 
            )
            annotation.create_graphics_item(self.annotation_window.scene)
            self.cursor_annotation = annotation

    def update_cursor_annotation(self, scene_pos: QPointF = None):
        """Update the cursor annotation position."""
        # Clear previous preview first to avoid flickering or overlap
        self.clear_cursor_annotation()
        # Create the new preview at the current cursor position
        self.create_cursor_annotation(scene_pos)

    def get_image_bounds(self):
        """Get the bounds of the current image in scene coordinates."""
        if not self.annotation_window.active_image or not self.annotation_window.pixmap_image:
            return None
        
        # Check if pixmap_image is a QGraphicsPixmapItem or QPixmap
        if hasattr(self.annotation_window.pixmap_image, 'boundingRect'):
            # It's a QGraphicsPixmapItem
            image_rect = self.annotation_window.pixmap_image.boundingRect()
        else:
            # It's a QPixmap, create a rect based on its size
            pixmap = self.annotation_window.pixmap_image
            image_rect = QRectF(0, 0, pixmap.width(), pixmap.height())
            
        return image_rect

    def clamp_to_image_bounds(self, scene_pos: QPointF):
        """Clamp a scene position to stay within the image bounds."""
        image_bounds = self.get_image_bounds()
        if not image_bounds:
            return scene_pos
            
        clamped_x = max(image_bounds.left(), min(image_bounds.right(), scene_pos.x()))
        clamped_y = max(image_bounds.top(), min(image_bounds.bottom(), scene_pos.y()))
        
        return QPointF(clamped_x, clamped_y)

    def snap_to_corner_or_edge(self, scene_pos: QPointF):
        """Snap to corner or edge if close enough."""
        image_bounds = self.get_image_bounds()
        if not image_bounds:
            return scene_pos
            
        # Check corner snapping first (higher priority)
        corners = [
            QPointF(image_bounds.left(), image_bounds.top()),      # Top-left
            QPointF(image_bounds.right(), image_bounds.top()),     # Top-right
            QPointF(image_bounds.left(), image_bounds.bottom()),   # Bottom-left
            QPointF(image_bounds.right(), image_bounds.bottom())   # Bottom-right
        ]
        
        for corner in corners:
            distance = ((scene_pos.x() - corner.x()) ** 2 + (scene_pos.y() - corner.y()) ** 2) ** 0.5
            if distance <= self.corner_snap_threshold:
                return corner
        
        # Check edge snapping
        snapped_pos = QPointF(scene_pos)
        
        # Snap to left edge
        if abs(scene_pos.x() - image_bounds.left()) <= self.edge_snap_threshold:
            snapped_pos.setX(image_bounds.left())
        # Snap to right edge
        elif abs(scene_pos.x() - image_bounds.right()) <= self.edge_snap_threshold:
            snapped_pos.setX(image_bounds.right())
            
        # Snap to top edge
        if abs(scene_pos.y() - image_bounds.top()) <= self.edge_snap_threshold:
            snapped_pos.setY(image_bounds.top())
        # Snap to bottom edge
        elif abs(scene_pos.y() - image_bounds.bottom()) <= self.edge_snap_threshold:
            snapped_pos.setY(image_bounds.bottom())
            
        return snapped_pos

    def is_cursor_outside_image(self, event_pos):
        """Check if cursor position is outside the image bounds."""
        if not self.annotation_window.active_image or not self.annotation_window.pixmap_image:
            return True
            
        scene_pos = self.annotation_window.mapToScene(event_pos)
        image_bounds = self.get_image_bounds()
        
        if not image_bounds:
            return True
            
        return not image_bounds.contains(scene_pos)

