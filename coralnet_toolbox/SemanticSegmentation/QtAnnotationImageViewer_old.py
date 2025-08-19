from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGraphicsView, 
                             QGraphicsScene, QGraphicsPixmapItem, QFrame, QGraphicsItemGroup)
from PyQt5.QtCore import Qt, pyqtSignal
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
        
        # Set up view properties similar to main annotation window
        self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.graphics_view.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Set frame style
        self.graphics_view.setFrameStyle(QFrame.StyledPanel)
        
        layout.addWidget(self.graphics_view)
        
        # Placeholder label when no image is loaded
        self.placeholder_label = QLabel("No image loaded")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(self.placeholder_label)
        
    def load_image(self, image_path):
        """Load and display an image with its annotations"""
        if not image_path or not os.path.exists(image_path):
            self.clear_image()
            return
            
        print(f"AnnotationImageViewer: Loading image {image_path}")
        self.current_image_path = image_path
        
        # Clear previous content
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
        
        # Set scene rect to image size
        self.graphics_scene.setSceneRect(pixmap.rect())
        
        # Fit image in view
        self.graphics_view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
        
        # Hide placeholder
        self.placeholder_label.hide()
        
        # Load and display annotations using the same approach as main window
        self.load_annotations()
        
        self.imageLoaded.emit(image_path)
        
    def load_annotations(self):
        """Load and display annotations for current image using main window's approach"""
        if not self.current_image_path:
            print("AnnotationImageViewer: No current image path")
            return
            
        print(f"AnnotationImageViewer: Loading annotations for {self.current_image_path}")
        
        # Get annotations from parent window
        if self.parent_window:
            try:
                annotations = self.parent_window.get_annotations_for_current_image()
                print(f"AnnotationImageViewer: Received {len(annotations)} annotations")
                
                if annotations:
                    # Use the same approach as main annotation window
                    self.display_annotations(annotations)
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
                
                # Create graphics item for this annotation if it doesn't exist
                if not hasattr(annotation, 'graphics_item') or not annotation.graphics_item:
                    print(f"    Creating graphics item for annotation {i}")
                    annotation.create_graphics_item(self.graphics_scene)
                    print(f"    Graphics item created: {annotation.graphics_item}")
                else:
                    # Add existing graphics item to our scene
                    print(f"    Using existing graphics item for annotation {i}")
                    if hasattr(annotation, 'graphics_item_group') and annotation.graphics_item_group:
                        # Remove from old scene if present
                        if annotation.graphics_item_group.scene():
                            annotation.graphics_item_group.scene().removeItem(annotation.graphics_item_group)
                        # Add to our scene
                        self.graphics_scene.addItem(annotation.graphics_item_group)
                    elif hasattr(annotation, 'graphics_item') and annotation.graphics_item:
                        # Remove from old scene if present
                        if annotation.graphics_item.scene():
                            annotation.graphics_item.scene().removeItem(annotation.graphics_item)
                        # Add to our scene
                        self.graphics_scene.addItem(annotation.graphics_item)
                
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
            from PyQt5.QtCore import QPointF
            from PyQt5.QtWidgets import QGraphicsPolygonItem
            
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
            pen.setWidth(2)
            graphics_item.setPen(pen)
            
            # Add to scene
            self.graphics_scene.addItem(graphics_item)
            print(f"    Fallback drawing successful for annotation {index}")
            
        except Exception as e:
            print(f"    Fallback drawing failed for annotation {index}: {e}")
        
        # Fall back to sample annotations if no real data
        print("No real annotations found, drawing sample data")
        self.draw_sample_annotations()
        
    def draw_real_annotations(self, annotations):
        """Draw real polygon annotations from the main window"""
        if not annotations:
            print("No annotations to draw")
            return
            
        # Sample annotation colors
        colors = [
            QColor(255, 0, 0, 100),    # Red
            QColor(0, 255, 0, 100),    # Green
            QColor(0, 0, 255, 100),    # Blue
            QColor(255, 255, 0, 100),  # Yellow
            QColor(255, 0, 255, 100),  # Magenta
            QColor(0, 255, 255, 100),  # Cyan
            QColor(255, 128, 0, 100),  # Orange
            QColor(128, 0, 255, 100),  # Purple
            QColor(255, 192, 203, 100), # Pink
            QColor(128, 128, 128, 100), # Gray
        ]
        
        drawn_count = 0
        skipped_count = 0
        
        for i, annotation in enumerate(annotations):
            try:
                # Get polygon points from annotation - try different attribute names
                points = None
                
                if hasattr(annotation, 'polygon_points') and annotation.polygon_points:
                    points = annotation.polygon_points
                    print(f"Using polygon_points for annotation {i}")
                elif hasattr(annotation, 'points') and annotation.points:
                    points = annotation.points
                    print(f"Using points for annotation {i}")
                elif hasattr(annotation, 'vertices') and annotation.vertices:
                    points = annotation.vertices
                    print(f"Using vertices for annotation {i}")
                
                # Skip non-polygon annotations (like patches, rectangles without points)
                if not points or len(points) < 3:
                    annotation_type = type(annotation).__name__ if annotation else "Unknown"
                    print(f"Skipping annotation {i} ({annotation_type}): insufficient points ({len(points) if points else 0})")
                    skipped_count += 1
                    continue
                
                # Get color based on annotation label or index
                color_index = i
                if hasattr(annotation, 'label') and annotation.label:
                    # Try to get color based on label for consistency
                    color_index = hash(annotation.label) % len(colors)
                else:
                    color_index = i % len(colors)
                    
                color = colors[color_index]
                
                # Draw the annotation
                self.draw_polygon(points, color)
                drawn_count += 1
                
                # Debug info for first few annotations
                if i < 3:
                    label = getattr(annotation, 'label', 'No label')
                    print(f"Drew annotation {i}: {type(annotation).__name__}, label='{label}', {len(points)} points")
                    
            except Exception as e:
                print(f"Error drawing annotation {i}: {e}")
                skipped_count += 1
                
        print(f"Drew {drawn_count} real annotations, skipped {skipped_count}")
        
        # If no annotations were drawn, show sample annotations
        if drawn_count == 0:
            print("No annotations could be drawn, showing sample data")
            self.draw_sample_annotations()
        
    def draw_sample_annotations(self):
        """Draw sample annotations for demonstration"""
        # Sample annotation colors
        colors = [
            QColor(255, 0, 0, 100),    # Red
            QColor(0, 255, 0, 100),    # Green
            QColor(0, 0, 255, 100),    # Blue
        ]
        
        # Sample polygons (only if we have an image loaded)
        if self.image_item:
            image_rect = self.image_item.boundingRect()
            if image_rect.width() > 0 and image_rect.height() > 0:
                # Create sample polygons relative to image size
                w, h = image_rect.width(), image_rect.height()
                sample_polygons = [
                    [(w*0.1, h*0.1), (w*0.3, h*0.1), (w*0.3, h*0.3), (w*0.1, h*0.3)],  # Rectangle
                    [(w*0.5, h*0.2), (w*0.7, h*0.15), (w*0.8, h*0.4), (w*0.6, h*0.45)],  # Irregular polygon
                    [(w*0.2, h*0.6), (w*0.4, h*0.6), (w*0.3, h*0.8)],  # Triangle
                ]
                
                for i, polygon_points in enumerate(sample_polygons):
                    color = colors[i % len(colors)]
                    self.draw_polygon(polygon_points, color)
            
    def draw_polygon(self, points, color):
        """Draw a single polygon annotation"""
        if len(points) < 3:
            return
            
        try:
            # Create QPolygonF from points
            polygon = QPolygonF()
            
            for point in points:
                # Handle different point formats
                if isinstance(point, (tuple, list)) and len(point) >= 2:
                    x, y = float(point[0]), float(point[1])
                elif hasattr(point, 'x') and hasattr(point, 'y'):
                    # Qt point objects
                    x, y = float(point.x()), float(point.y())
                elif hasattr(point, '__getitem__') and len(point) >= 2:
                    # Array-like objects
                    x, y = float(point[0]), float(point[1])
                else:
                    print(f"Unrecognized point format: {point}")
                    continue
                    
                polygon.append(x, y)
            
            if polygon.size() < 3:
                print(f"Not enough valid points to draw polygon: {polygon.size()}")
                return
                
            # Create graphics item
            polygon_item = self.graphics_scene.addPolygon(polygon)
            
            # Set appearance
            pen = QPen(color.darker(150), 2)
            brush = QBrush(color)
            polygon_item.setPen(pen)
            polygon_item.setBrush(brush)
            
            print(f"Successfully drew polygon with {polygon.size()} points")
            
        except Exception as e:
            print(f"Error drawing polygon: {e}")
            import traceback
            traceback.print_exc()
        
    def clear_image(self):
        """Clear the current image and show placeholder"""
        self.graphics_scene.clear()
        self.current_image_path = None
        self.annotations = []
        self.placeholder_label.show()
        
    def refresh_annotations(self):
        """Refresh the annotation display"""
        if self.current_image_path:
            self.load_annotations()
