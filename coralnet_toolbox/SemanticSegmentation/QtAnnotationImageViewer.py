from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGraphicsView, 
                             QGraphicsScene, QGraphicsPixmapItem, QFrame, QGraphicsItemGroup,
                             QGraphicsPolygonItem)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QBrush, QPolygonF
import os

class AnnotationImageViewer(QWidget):
    """Left panel: Display image with polygon annotations overlaid"""
    
    imageLoaded = pyqtSignal(str)  # Emitted when image is loaded
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_image_path = None
        self.annotations = []
        self.pixmap_item = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the image viewer UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Image with Annotations")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title)
        
        # Graphics view for image display
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        
        # Set up view properties for fixed zoom to extents
        self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
        self.graphics_view.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setDragMode(QGraphicsView.NoDrag)
        
        # Set frame style
        self.graphics_view.setFrameStyle(QFrame.StyledPanel)
        
        # Allow basic interaction but disable specific actions that change zoom
        # Remove setInteractive(False) to allow proper rendering
        
        layout.addWidget(self.graphics_view)
        
        # Placeholder label when no image is loaded
        self.placeholder_label = QLabel("No image loaded")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(self.placeholder_label)
        
    def resizeEvent(self, event):
        """Handle widget resize to keep image fitted to extents"""
        super().resizeEvent(event)
        if self.pixmap_item:
            # Fit the image to the view whenever the widget is resized
            self.fit_image_to_view()
    
    def wheelEvent(self, event):
        """Override wheel event to prevent zooming"""
        # Do nothing - prevents mouse wheel zooming
        pass
    
    def mousePressEvent(self, event):
        """Override mouse press to prevent panning"""
        # Do nothing - prevents mouse dragging/panning
        pass
    
    def mouseMoveEvent(self, event):
        """Override mouse move to prevent panning"""
        # Do nothing - prevents mouse dragging/panning  
        pass
        
    def load_image(self, image_path):
        """Load and display an image with its annotations"""
        if not image_path or not os.path.exists(image_path):
            self.clear_image()
            return
            
        print(f"AnnotationImageViewer: Loading image {image_path}")
        
        # Always reload image and annotations, even if it's the same path
        # This ensures annotations show up when switching back to an image
        self.current_image_path = image_path
        
        # IMPORTANT: Reset graphics item references in annotations BEFORE clearing scene
        # This ensures annotations can be recreated properly when switching back to an image
        self.reset_annotation_graphics_state()
        
        # Clear previous content completely and reset annotation graphics state
        self.graphics_scene.clear()
        self.pixmap_item = None
        
        # Load the image using the same approach as main window
        if (self.parent_window and 
            hasattr(self.parent_window, 'main_window') and 
            hasattr(self.parent_window.main_window, 'image_window')):
            
            # Try to get image from raster manager like main window does
            raster_manager = self.parent_window.main_window.image_window.raster_manager
            if hasattr(raster_manager, 'get_raster'):
                raster = raster_manager.get_raster(image_path)
                if raster:
                    q_image = raster.get_qimage()
                    if q_image and not q_image.isNull():
                        pixmap = QPixmap.fromImage(q_image)
                        print(f"Loaded image via raster manager: {pixmap.width()}x{pixmap.height()}")
                    else:
                        print("Failed to get QImage from raster, falling back to direct load")
                        pixmap = QPixmap(image_path)
                else:
                    print("Failed to get raster, falling back to direct load")
                    pixmap = QPixmap(image_path)
            else:
                print("No get_raster method, falling back to direct load")
                pixmap = QPixmap(image_path)
        else:
            print("No raster manager available, loading image directly")
            pixmap = QPixmap(image_path)
        
        if pixmap.isNull():
            print(f"Failed to load image: {image_path}")
            self.clear_image()
            return
            
        # Add image to scene
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.graphics_scene.addItem(self.pixmap_item)
        
        # Set scene rect to exactly match the image dimensions
        image_rect = self.pixmap_item.boundingRect()
        self.graphics_scene.setSceneRect(image_rect)
        print(f"Image loaded: {pixmap.width()}x{pixmap.height()}, scene rect: {image_rect}")
        
        # Fit image in view and ensure it stays fitted
        self.fit_image_to_view()
        
        # Hide placeholder
        self.placeholder_label.hide()
        
        # Fit image in view first
        self.fit_image_to_view()
        
        # Load and display annotations using a timer to ensure image is ready
        print("About to load annotations...")
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(50, self.load_annotations)  # Give image time to render
        
        # Ensure proper fitting after everything is loaded
        QTimer.singleShot(100, self.fit_image_to_view)
        
        self.imageLoaded.emit(image_path)
        
    def fit_image_to_view(self):
        """Fit the image to the view extents"""
        if self.pixmap_item:
            # Reset any transformation first
            self.graphics_view.resetTransform()
            # Set scene rect to exactly match the image
            image_rect = self.pixmap_item.boundingRect()
            self.graphics_scene.setSceneRect(image_rect)
            # Fit the entire image in the view
            self.graphics_view.fitInView(image_rect, Qt.KeepAspectRatio)
            print(f"Fitted image to view: scene rect = {image_rect}, view size = {self.graphics_view.size()}")
        
    def load_annotations(self):
        """Load and display annotations for current image using main window's approach"""
        if not self.current_image_path:
            print("AnnotationImageViewer: No current image path")
            return
            
        print(f"AnnotationImageViewer: Loading annotations for {self.current_image_path}")
        
        # Get annotations from parent window
        if self.parent_window:
            try:
                print("About to call get_annotations_for_current_image...")
                annotations = self.parent_window.get_annotations_for_current_image()
                print(f"AnnotationImageViewer: Received {len(annotations)} annotations from parent")
                
                if annotations:
                    # Use the same approach as main annotation window
                    print("About to display annotations...")
                    self.display_annotations(annotations)
                    print("Finished displaying annotations")
                    # Ensure image stays fitted after annotations are added
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(10, self.fit_image_to_view)
                else:
                    print("AnnotationImageViewer: No annotations to display")
                    
            except Exception as e:
                print(f"AnnotationImageViewer: Error loading annotations: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("AnnotationImageViewer: No parent window available")
    
    def display_annotations(self, annotations):
        """Display annotations using the same approach as main annotation window"""
        print(f"AnnotationImageViewer: Displaying {len(annotations)} annotations")
        
        for i, annotation in enumerate(annotations):
            try:
                print(f"  Processing annotation {i}: {type(annotation).__name__}")
                
                # Always create fresh graphics items for the semantic segmentation view
                # This ensures annotations show up correctly when switching between images
                try:
                    print(f"    Creating fresh graphics item for annotation {i}")
                    annotation.create_graphics_item(self.graphics_scene)
                    print(f"    Graphics item created successfully")
                except Exception as create_error:
                    print(f"    Error creating graphics item: {create_error}")
                    # Fall back to manual polygon drawing
                    self.draw_annotation_fallback(annotation, i)
                
                print(f"    Successfully displayed annotation {i}")
                
            except Exception as e:
                print(f"    Error displaying annotation {i}: {e}")
                import traceback
                traceback.print_exc()
                
                # Fall back to manual polygon drawing
                try:
                    self.draw_annotation_fallback(annotation, i)
                except Exception as e2:
                    print(f"    Fallback drawing also failed for annotation {i}: {e2}")
    
    def draw_annotation_fallback(self, annotation, index):
        """Fallback method to manually draw annotation polygon"""
        print(f"    Using fallback drawing for annotation {index}")
        
        # Try to get polygon points from various attributes
        points = None
        if hasattr(annotation, 'polygon_points') and annotation.polygon_points:
            points = annotation.polygon_points
        elif hasattr(annotation, 'points') and annotation.points:
            points = annotation.points
        elif hasattr(annotation, 'vertices') and annotation.vertices:
            points = annotation.vertices
        
        if not points:
            print(f"    No points found for annotation {index}")
            return
        
        # Create QPolygonF from points
        try:
            polygon = QPolygonF()
            for point in points:
                if isinstance(point, (list, tuple)) and len(point) >= 2:
                    polygon.append(QPointF(float(point[0]), float(point[1])))
                elif hasattr(point, 'x') and hasattr(point, 'y'):
                    polygon.append(QPointF(float(point.x), float(point.y)))
            
            if polygon.isEmpty():
                print(f"    Empty polygon for annotation {index}")
                return
            
            # Create graphics item
            graphics_item = QGraphicsPolygonItem(polygon)
            
            # Set style similar to main window
            color = QColor(255, 0, 0)  # Default red
            if hasattr(annotation, 'label') and hasattr(annotation.label, 'color'):
                color = QColor(annotation.label.color)
            
            color.setAlpha(128)  # Semi-transparent
            graphics_item.setBrush(QBrush(color))
            
            pen = QPen(color.darker(150))
            pen.setWidth(30)  # Increased thickness for better visibility
            graphics_item.setPen(pen)
            
            # Add to scene
            self.graphics_scene.addItem(graphics_item)
            print(f"    Fallback drawing successful for annotation {index}")
            
        except Exception as e:
            print(f"    Fallback drawing failed for annotation {index}: {e}")
    
    def reset_annotation_graphics_state(self):
        """Reset graphics item references in all annotations to ensure clean state"""
        try:
            if self.parent_window and self.current_image_path:
                annotations = self.parent_window.get_annotations_for_current_image()
                for annotation in annotations:
                    # Reset all graphics item references
                    if hasattr(annotation, 'graphics_item_group'):
                        annotation.graphics_item_group = None
                    if hasattr(annotation, 'graphics_item'):
                        annotation.graphics_item = None
                    if hasattr(annotation, 'center_graphics_item'):
                        annotation.center_graphics_item = None
                    if hasattr(annotation, 'bounding_box_graphics_item'):
                        annotation.bounding_box_graphics_item = None
                    if hasattr(annotation, 'polygon_graphics_item'):
                        annotation.polygon_graphics_item = None
                print(f"Reset graphics state for {len(annotations)} annotations")
            else:
                print("No annotations to reset graphics state for")
        except Exception as e:
            print(f"Error resetting annotation graphics state: {e}")
        
    def clear_image(self):
        """Clear the current image and show placeholder"""
        # Reset annotation graphics state before clearing scene
        self.reset_annotation_graphics_state()
        self.graphics_scene.clear()
        self.current_image_path = None
        self.annotations = []
        self.pixmap_item = None
        self.placeholder_label.show()
        
    def refresh_annotations(self):
        """Refresh the annotation display"""
        if self.current_image_path:
            print(f"AnnotationImageViewer: Refreshing annotations for {self.current_image_path}")
            
            # Reset annotation graphics state first
            self.reset_annotation_graphics_state()
            
            # Clear any existing annotation graphics (keep the image)
            items_to_remove = []
            for item in self.graphics_scene.items():
                if item != self.pixmap_item:
                    items_to_remove.append(item)
            
            for item in items_to_remove:
                self.graphics_scene.removeItem(item)
            
            # Reload annotations
            self.load_annotations()
