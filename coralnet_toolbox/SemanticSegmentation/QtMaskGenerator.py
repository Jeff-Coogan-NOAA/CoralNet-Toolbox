from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGraphicsView, 
                             QGraphicsScene, QGraphicsPixmapItem, QFrame, QPushButton,
                             QHBoxLayout, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
from PyQt5.QtGui import QPixmap, QPainter, QColor, QImage, QPen, QBrush
import numpy as np
import os
import math

class InteractiveMaskView(QGraphicsView):
    """Custom graphics view that supports drawing on the mask"""
    
    maskEdited = pyqtSignal(np.ndarray)  # Emitted when mask is edited
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.mask_item = None
        self.drawing = False
        self.last_point = None
        self.current_mask = None
        
        # Drawing settings
        self.draw_color = QColor(255, 0, 0)  # Default red
        self.brush_size = 5
        self.is_eraser = False
        
        # Set up the view
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setFrameStyle(QFrame.StyledPanel)
        
    def set_mask(self, mask_array):
        """Set the mask array for editing"""
        if mask_array is not None:
            # Ensure the mask is a contiguous array in the right format
            self.current_mask = np.ascontiguousarray(mask_array, dtype=np.uint8)
            print(f"Set mask: shape={self.current_mask.shape}, dtype={self.current_mask.dtype}")
        else:
            self.current_mask = None
            print("Set mask to None")
        
    def set_draw_color(self, color):
        """Set the drawing color"""
        self.draw_color = color
        
    def set_brush_size(self, size):
        """Set the brush size in pixels"""
        self.brush_size = size
        
    def set_eraser_mode(self, is_eraser):
        """Set eraser mode on/off"""
        self.is_eraser = is_eraser
        
    def mousePressEvent(self, event):
        """Handle mouse press for drawing"""
        print(f"Mouse press event: button={event.button()}, pos={event.pos()}")
        print(f"Left button check: {event.button() == Qt.LeftButton}")
        print(f"Current mask exists: {self.current_mask is not None}")
        if self.current_mask is not None:
            print(f"Current mask shape: {self.current_mask.shape}")
        
        print(f"Drawing tool settings: color={self.draw_color.name()}, brush_size={self.brush_size}, eraser={self.is_eraser}")
        
        if event.button() == Qt.LeftButton and self.current_mask is not None:
            print(f"Left button pressed, mask shape: {self.current_mask.shape}")
            
            # Convert view coordinates to scene coordinates
            scene_pos = self.mapToScene(event.pos())
            print(f"Scene pos: {scene_pos}")
            
            # Convert scene coordinates to image coordinates
            print(f"Mask item exists: {self.mask_item is not None}")
            if self.mask_item:
                try:
                    print(f"Mask item bounds: {self.mask_item.boundingRect()}")
                    item_pos = self.mask_item.mapFromScene(scene_pos)
                    x, y = int(item_pos.x()), int(item_pos.y())
                    print(f"Item pos: {item_pos}, x={x}, y={y}")
                    
                    # Check bounds
                    if (0 <= x < self.current_mask.shape[1] and 
                        0 <= y < self.current_mask.shape[0]):
                        
                        print(f"Drawing at valid position: ({x}, {y})")
                        self.drawing = True
                        self.last_point = QPointF(x, y)
                        
                        # Draw a single dot
                        self.draw_at_point(x, y)
                    else:
                        print(f"Position out of bounds: ({x}, {y}) not in (0-{self.current_mask.shape[1]}, 0-{self.current_mask.shape[0]})")
                        
                        # Fallback: try using scene coordinates directly scaled to mask size
                        scene_rect = self.scene().itemsBoundingRect()
                        print(f"Scene bounding rect: {scene_rect}")
                        if not scene_rect.isEmpty():
                            # Calculate relative position within the scene
                            rel_x = (scene_pos.x() - scene_rect.x()) / scene_rect.width()
                            rel_y = (scene_pos.y() - scene_rect.y()) / scene_rect.height()
                            
                except RuntimeError as e:
                    print(f"Error accessing mask item (object deleted): {e}")
                    # Reset mask item reference since it's been deleted
                    self.mask_item = None
                    return
            else:
                print("No mask_item available")
        else:
            if event.button() != Qt.LeftButton:
                print(f"Not left button: {event.button()}")
            if self.current_mask is None:
                print("No current mask available")
                
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """Handle mouse move for continuous drawing"""
        if self.drawing and self.current_mask is not None and self.mask_item:
            print(f"Mouse move event: pos={event.pos()}")
            
            try:
                # Convert view coordinates to scene coordinates
                scene_pos = self.mapToScene(event.pos())
                
                # Convert scene coordinates to image coordinates
                item_pos = self.mask_item.mapFromScene(scene_pos)
                x, y = int(item_pos.x()), int(item_pos.y())
                
                print(f"Move to image coordinates: ({x}, {y})")
                
                # Check bounds
                if (0 <= x < self.current_mask.shape[1] and 
                    0 <= y < self.current_mask.shape[0]):
                    
                    current_point = QPointF(x, y)
                    
                    # Draw line from last point to current point
                    if self.last_point:
                        # Check if we've moved enough to warrant drawing a line
                        distance = math.sqrt((current_point.x() - self.last_point.x())**2 + 
                                           (current_point.y() - self.last_point.y())**2)
                        
                        # Only draw if we've moved at least 1 pixel (prevents excessive drawing)
                        if distance >= 1.0:
                            print(f"Drawing line, distance: {distance:.1f}")
                            self.draw_line(self.last_point, current_point)
                            self.last_point = current_point
                        else:
                            print(f"Skipping line draw, distance too small: {distance:.1f}")
                    else:
                        # First point - just draw a dot
                        print("First point in line, drawing dot")
                        self.draw_at_point(x, y, update_display=True)
                        self.last_point = current_point
                else:
                    print(f"Move position out of bounds: ({x}, {y})")
                    
            except RuntimeError as e:
                print(f"Error accessing mask item during mouse move (object deleted): {e}")
                # Reset mask item reference and stop drawing
                self.mask_item = None
                self.drawing = False
                return
                
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop drawing"""
        if event.button() == Qt.LeftButton:
            self.drawing = False
            self.last_point = None
            
            # Emit the updated mask
            if self.current_mask is not None:
                self.maskEdited.emit(self.current_mask.copy())
                
        super().mouseReleaseEvent(event)
        
    def draw_at_point(self, x, y, update_display=True):
        """Draw at a specific point with the current brush"""
        if self.current_mask is None:
            print("No current mask available for drawing")
            return
            
        print(f"Drawing at point ({x}, {y}) with brush size {self.brush_size}, color {self.draw_color.name()}, eraser {self.is_eraser}")
        
        # Calculate brush bounds
        radius = self.brush_size // 2
        
        # Get color to draw
        if self.is_eraser:
            color = [0, 0, 0]  # Black for eraser (background)
        else:
            color = [self.draw_color.red(), self.draw_color.green(), self.draw_color.blue()]
        
        print(f"Using color: {color}, radius: {radius}")
        
        # Draw circular brush
        pixels_drawn = 0
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                px, py = x + dx, y + dy
                
                # Check if point is within brush radius and image bounds
                if (0 <= px < self.current_mask.shape[1] and 
                    0 <= py < self.current_mask.shape[0] and
                    dx*dx + dy*dy <= radius*radius):
                    
                    self.current_mask[py, px] = color
                    pixels_drawn += 1
        
        print(f"Drew {pixels_drawn} pixels")
        
        # Update the display only if requested (to avoid excessive updates during line drawing)
        if update_display:
            self.update_mask_display()
        
    def draw_line(self, start_point, end_point):
        """Draw a line between two points"""
        if self.current_mask is None:
            return
            
        print(f"Drawing line from ({start_point.x():.1f}, {start_point.y():.1f}) to ({end_point.x():.1f}, {end_point.y():.1f})")
        
        # Use Bresenham's line algorithm to get points along the line
        x0, y0 = int(start_point.x()), int(start_point.y())
        x1, y1 = int(end_point.x()), int(end_point.y())
        
        # Calculate line length and step size based on brush size
        line_length = math.sqrt((x1 - x0)**2 + (y1 - y0)**2)
        
        if line_length == 0:
            print("Line length is 0, drawing single point")
            self.draw_at_point(x0, y0, update_display=True)
            return
            
        # Draw dots along the line with spacing based on brush size
        step_size = max(1, self.brush_size // 3)  # Smaller steps for smoother lines
        num_steps = max(1, int(line_length / step_size) + 1)
        
        print(f"Line length: {line_length:.1f}, step_size: {step_size}, num_steps: {num_steps}")
        
        # Limit the number of steps to prevent excessive computation
        max_steps = 100  # Reasonable limit
        if num_steps > max_steps:
            print(f"Limiting steps from {num_steps} to {max_steps}")
            num_steps = max_steps
        
        # Draw all points along the line without updating display each time
        for i in range(num_steps):
            if num_steps == 1:
                t = 0
            else:
                t = i / (num_steps - 1)
            x = int(x0 + t * (x1 - x0))
            y = int(y0 + t * (y1 - y0))
            
            # Draw without updating display for efficiency
            self.draw_at_point(x, y, update_display=False)
        
        # Update display once after drawing the entire line
        print("Updating display after drawing line")
        self.update_mask_display()
            
    def update_mask_display(self):
        """Update the displayed mask after editing"""
        print("Updating mask display after editing")
        
        if self.current_mask is not None and self.mask_item:
            print(f"Mask shape: {self.current_mask.shape}, mask_item exists: {self.mask_item is not None}")
            
            try:
                # Convert numpy array to QImage
                height, width = self.current_mask.shape[:2]
                bytes_per_line = 3 * width
                
                # Ensure the array is contiguous and in the right format
                mask_data = np.ascontiguousarray(self.current_mask, dtype=np.uint8)
                
                q_image = QImage(
                    mask_data.data,
                    width, height,
                    bytes_per_line,
                    QImage.Format_RGB888
                )
                
                print(f"Created QImage: {q_image.width()}x{q_image.height()}")
                
                # Convert to pixmap and update the display
                pixmap = QPixmap.fromImage(q_image)
                print(f"Created pixmap: {pixmap.width()}x{pixmap.height()}")
                
                self.mask_item.setPixmap(pixmap)
                print("Updated mask_item pixmap")
                
            except RuntimeError as e:
                print(f"Error updating mask display (object deleted): {e}")
                # Reset mask item reference since it's been deleted
                self.mask_item = None
        else:
            print(f"Cannot update display: current_mask={self.current_mask is not None}, mask_item={self.mask_item is not None}")

class MaskGenerator(QWidget):
    """Center-right panel: Generate and display segmentation mask based on sorted annotation types"""
    
    maskGenerated = pyqtSignal(np.ndarray)  # Emitted when mask is generated
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_image_path = None
        self.current_mask = None
        self.image_size = None
        self.manual_edits = None  # For storing manual edits
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the mask generator UI"""
        layout = QVBoxLayout(self)
        
        # Title and controls
        header_layout = QHBoxLayout()
        
        title = QLabel("Generated Mask")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        header_layout.addWidget(title)
        
        # Generate button
        self.generate_btn = QPushButton("Generate")
        self.generate_btn.clicked.connect(self.regenerate_mask)
        self.generate_btn.setMaximumWidth(80)
        header_layout.addWidget(self.generate_btn)
        
        # Export button
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_mask)
        self.export_btn.setMaximumWidth(80)
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # Interactive graphics view for mask display and editing
        self.graphics_view = InteractiveMaskView(self)
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        
        # Connect mask editing signal
        self.graphics_view.maskEdited.connect(self.on_mask_edited)
        
        layout.addWidget(self.graphics_view)
        
        # Placeholder label
        self.placeholder_label = QLabel("No mask generated")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(self.placeholder_label)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(self.status_label)
        
    def on_mask_edited(self, edited_mask):
        """Handle mask editing from the interactive view"""
        self.current_mask = edited_mask.copy()
        self.manual_edits = edited_mask.copy()  # Store the edits
        print("Mask edited manually")
        
    def set_drawing_tool(self, color, brush_size):
        """Set the drawing tool parameters"""
        self.graphics_view.set_draw_color(color)
        self.graphics_view.set_brush_size(brush_size)
        self.graphics_view.set_eraser_mode(False)  # Always disable eraser mode
        print(f"Drawing tool set: color={color.name()}, brush_size={brush_size}")
        
    def apply_manual_edits(self, edits):
        """Apply manual edits to the mask (for compatibility)"""
        self.manual_edits = edits
        self.on_mask_edited(edits)
        
    def load_image(self, image_path):
        """Load image for mask generation"""
        self.current_image_path = image_path
        
        if image_path and os.path.exists(image_path):
            # Load image to get dimensions
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                self.image_size = (pixmap.width(), pixmap.height())
                self.status_label.setText(f"Image loaded: {self.image_size[0]}x{self.image_size[1]}")
            else:
                self.image_size = None
                self.status_label.setText("Failed to load image")
        else:
            self.image_size = None
            self.status_label.setText("No image")
            
        # Clear previous mask
        self.current_mask = None
        self.manual_edits = None
        self.clear_mask()
        
        # Check for existing mask and load it if available
        self.load_existing_mask_if_available()
        
    def regenerate_mask(self, annotation_order=None):
        """Generate segmentation mask based on annotation order"""
        print(f"regenerate_mask called with annotation_order: {annotation_order}")
        print(f"Image size: {self.image_size}, Image path: {self.current_image_path}")
        
        if not self.image_size or not self.current_image_path:
            print("No image loaded - cannot generate mask")
            self.status_label.setText("No image loaded")
            return
            
        # Handle the case where button click passes False instead of None
        if annotation_order is None or annotation_order is False:
            if self.parent_window:
                annotation_order = self.parent_window.get_current_sort_order()
                print(f"Got annotation order from parent window: {annotation_order}")
            
        if not annotation_order:
            print("No annotation types to process")
            self.status_label.setText("No annotation types to process")
            return
            
        self.status_label.setText("Generating mask...")
        
        # Create mask array (RGB color image instead of grayscale)
        width, height = self.image_size
        mask = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Get actual annotations from parent window
        annotations = []
        if self.parent_window:
            annotations = self.parent_window.get_annotations_for_current_image()
        
        print(f"Total annotations found: {len(annotations)}")
        
        # Create a dictionary of annotations by label for easier lookup
        annotations_by_label = {}
        for ann in annotations:
            if hasattr(ann, 'label'):
                label_text = None
                if hasattr(ann.label, 'short_label_code'):
                    label_text = ann.label.short_label_code
                elif hasattr(ann.label, 'long_label_code'):
                    label_text = ann.label.long_label_code
                elif isinstance(ann.label, str):
                    label_text = ann.label
                else:
                    label_text = str(ann.label)
                
                if label_text:
                    if label_text not in annotations_by_label:
                        annotations_by_label[label_text] = []
                    annotations_by_label[label_text].append(ann)
        
        print(f"Available annotations by label: {list(annotations_by_label.keys())}")
        print(f"Annotation counts by label: {[(label, len(anns)) for label, anns in annotations_by_label.items()]}")
        print(f"Sort order from list: {annotation_order}")
        
        # Process each annotation type in order (like layers)
        # The first annotation type fills the entire background
        # Subsequent types only fill their polygon regions
        # NOTE: We process ALL types in the sort list, not just those with annotations
        total_polygons_filled = 0
        for i, annotation_type in enumerate(annotation_order):
            print(f"\nProcessing layer {i+1}: '{annotation_type}'")
            
            # Get the annotation color from the label system
            annotation_color = self.get_annotation_type_color(annotation_type)
            print(f"Using annotation color for '{annotation_type}': {annotation_color}")
            
            # Get annotations for this type (may be empty list)
            type_annotations = annotations_by_label.get(annotation_type, [])
            print(f"Found {len(type_annotations)} annotations for type '{annotation_type}'")
            
            if i == 0:
                # First annotation type: fill the entire mask as background
                print(f"Filling entire mask with background color for '{annotation_type}'")
                mask[:, :, 0] = annotation_color[0]  # Red channel
                mask[:, :, 1] = annotation_color[1]  # Green channel
                mask[:, :, 2] = annotation_color[2]  # Blue channel
                print(f"Background filled with color {annotation_color}")
                
                # Also process any polygons for the background type if they exist
                if type_annotations:
                    print(f"Found {len(type_annotations)} background annotations for type '{annotation_type}' - processing as polygons too")
                    for j, annotation in enumerate(type_annotations):
                        print(f"  Processing background annotation {j+1}/{len(type_annotations)} for type '{annotation_type}'")
                        points = self.get_annotation_points(annotation)
                        if points and len(points) >= 3:
                            print(f"    Filling background polygon with {len(points)} points in color {annotation_color}")
                            self.fill_polygon_in_color_mask(mask, points, annotation_color)
                            total_polygons_filled += 1
                else:
                    print(f"No specific polygons for background type '{annotation_type}' - background color only")
            else:
                # Subsequent annotation types: only fill their polygon regions
                if not type_annotations:
                    print(f"No annotations found for type '{annotation_type}', but included in sort list - no polygons to fill")
                    continue
                
                # Fill all polygons for this annotation type with its color
                polygons_filled_for_type = 0
                for j, annotation in enumerate(type_annotations):
                    print(f"  Processing annotation {j+1}/{len(type_annotations)} for type '{annotation_type}'")
                    points = self.get_annotation_points(annotation)
                    
                    if points and len(points) >= 3:
                        print(f"    Filling polygon with {len(points)} points in color {annotation_color}")
                        self.fill_polygon_in_color_mask(mask, points, annotation_color)
                        polygons_filled_for_type += 1
                        total_polygons_filled += 1
                    else:
                        print(f"    Skipping annotation - not enough points (has {len(points) if points else 0})")
                
                print(f"Filled {polygons_filled_for_type} polygons for type '{annotation_type}'")
        
        print(f"\nTotal polygons filled across all types: {total_polygons_filled}")
        
        # Check if any pixels were actually filled
        non_zero_pixels = np.count_nonzero(mask)
        print(f"Non-zero pixels in mask: {non_zero_pixels}")
        if non_zero_pixels == 0:
            print("WARNING: No pixels were filled in the mask!")
        
        # Apply manual edits if they exist
        if self.manual_edits is not None:
            mask = self.apply_manual_edits_to_mask(mask)
            
        self.current_mask = mask
        self.display_color_mask(mask)
        self.maskGenerated.emit(mask)
        self.status_label.setText(f"Mask generated with {len(annotation_order)} annotation types")
        self.status_label.setText(f"Mask generated with {len(annotation_order)} annotation types")
        
    def get_annotation_type_color(self, annotation_type):
        """Get the color for a specific annotation type from the label system"""
        # Default color (white)
        default_color = [255, 255, 255]
        
        try:
            # Try to get color from the main window's label system
            if (self.parent_window and 
                self.parent_window.main_window and
                hasattr(self.parent_window.main_window, 'label_window') and 
                hasattr(self.parent_window.main_window.label_window, 'labels')):
                
                labels_list = self.parent_window.main_window.label_window.labels
                
                for label in labels_list:
                    # Check if this label matches our annotation type
                    label_text = None
                    if hasattr(label, 'short_label_code'):
                        label_text = label.short_label_code
                    elif hasattr(label, 'long_label_code'):
                        label_text = label.long_label_code
                    
                    if label_text == annotation_type:
                        # Found matching label, get its color
                        if hasattr(label, 'color') and label.color:
                            color = label.color
                            
                            # Handle different color formats
                            if isinstance(color, (list, tuple)) and len(color) >= 3:
                                # RGB list/tuple
                                return [int(color[0]), int(color[1]), int(color[2])]
                            elif hasattr(color, 'red') and hasattr(color, 'green') and hasattr(color, 'blue'):
                                # QColor object
                                return [color.red(), color.green(), color.blue()]
                            elif isinstance(color, str) and color.startswith('#'):
                                # Hex color string
                                hex_color = color.lstrip('#')
                                if len(hex_color) == 6:
                                    return [int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)]
                            elif isinstance(color, int):
                                # Integer color value (convert from Qt RGB)
                                return [(color >> 16) & 255, (color >> 8) & 255, color & 255]
                        
                        print(f"Found label '{annotation_type}' but no valid color, using default")
                        return default_color
                
                print(f"Label '{annotation_type}' not found in label system, using default color")
            else:
                print("No label system available, using default color")
                
        except Exception as e:
            print(f"Error getting annotation type color for '{annotation_type}': {e}")
            
        return default_color
        
    def get_annotation_points(self, annotation):
        """Helper method to extract points from an annotation object"""
        points = None
        
        # Try different attribute names for polygon points
        if hasattr(annotation, 'polygon_points') and annotation.polygon_points:
            points = annotation.polygon_points
            print(f"    Found polygon_points: {len(points)} points")
        elif hasattr(annotation, 'points') and annotation.points:
            points = annotation.points
            print(f"    Found points: {len(points)} points")
        elif hasattr(annotation, 'vertices') and annotation.vertices:
            points = annotation.vertices
            print(f"    Found vertices: {len(points)} points")
        else:
            print(f"    No valid polygon points found for annotation")
            
        return points
        
    def create_sample_mask_region(self, mask, region_index, mask_value):
        """Create sample mask regions for demonstration"""
        height, width = mask.shape
        
        if region_index == 0:
            # Create a rectangular region
            mask[50:150, 50:200] = mask_value
        elif region_index == 1:
            # Create a circular region
            center_y, center_x = height // 2, width // 2
            y, x = np.ogrid[:height, :width]
            circle_mask = (x - center_x) ** 2 + (y - center_y) ** 2 <= 80 ** 2
            mask[circle_mask] = mask_value
        elif region_index == 2:
            # Create an irregular region
            mask[200:300, 300:450] = mask_value
            
    def fill_polygon_in_color_mask(self, mask, polygon_points, color):
        """Fill a polygon in the color mask with the specified RGB color"""
        try:
            if len(polygon_points) < 3:
                return
                
            height, width = mask.shape[:2]
            
            # Convert polygon points to integer coordinates
            points = []
            for point in polygon_points:
                try:
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
                        print(f"Unrecognized point format in polygon: {point}")
                        continue
                        
                    # Convert to integer and clamp to image bounds
                    x = max(0, min(width - 1, int(x)))
                    y = max(0, min(height - 1, int(y)))
                    points.append((x, y))
                    
                except (ValueError, TypeError, AttributeError) as e:
                    print(f"Error processing point {point}: {e}")
                    continue
                    
            if len(points) < 3:
                print(f"Not enough valid points for polygon fill: {len(points)}")
                return
                
            print(f"Filling polygon with {len(points)} points, color {color}")
                
            # Simple polygon fill using scanline algorithm
            # For each row, find intersection points and fill between pairs
            min_y = min(p[1] for p in points)
            max_y = max(p[1] for p in points)
            
            for y in range(max(0, min_y), min(height, max_y + 1)):
                intersections = []
                
                # Find intersections with polygon edges
                for i in range(len(points)):
                    p1 = points[i]
                    p2 = points[(i + 1) % len(points)]
                    
                    if p1[1] != p2[1]:  # Not horizontal line
                        # Check if scanline intersects this edge
                        if min(p1[1], p2[1]) <= y < max(p1[1], p2[1]):
                            # Calculate intersection x coordinate
                            x = p1[0] + (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])
                            intersections.append(int(x))
                
                # Sort intersections and fill between pairs
                intersections.sort()
                for i in range(0, len(intersections) - 1, 2):
                    x1 = max(0, min(width - 1, intersections[i]))
                    x2 = max(0, min(width - 1, intersections[i + 1]))
                    if x1 <= x2:
                        # Fill with RGB color
                        mask[y, x1:x2 + 1, 0] = color[0]  # Red
                        mask[y, x1:x2 + 1, 1] = color[1]  # Green
                        mask[y, x1:x2 + 1, 2] = color[2]  # Blue
                        
        except Exception as e:
            print(f"Error filling polygon with color: {e}")
            # Fall back to bounding box fill
            self.fill_bounding_box_in_color_mask(mask, polygon_points, color)
            
    def fill_bounding_box_in_color_mask(self, mask, polygon_points, color):
        """Fill bounding box of polygon with color as fallback"""
        try:
            if len(polygon_points) < 2:
                return
                
            # Extract all x,y coordinates
            x_coords = []
            y_coords = []
            for point in polygon_points:
                try:
                    if isinstance(point, (tuple, list)) and len(point) >= 2:
                        x, y = float(point[0]), float(point[1])
                    elif hasattr(point, 'x') and hasattr(point, 'y'):
                        x, y = float(point.x()), float(point.y())
                    elif hasattr(point, '__getitem__') and len(point) >= 2:
                        x, y = float(point[0]), float(point[1])
                    else:
                        continue
                        
                    x_coords.append(x)
                    y_coords.append(y)
                except (ValueError, TypeError, AttributeError):
                    continue
            
            if len(x_coords) < 2:
                return
                
            # Get bounding box
            min_x = max(0, min(width - 1, int(min(x_coords))))
            max_x = max(0, min(width - 1, int(max(x_coords))))
            min_y = max(0, min(height - 1, int(min(y_coords))))
            max_y = max(0, min(height - 1, int(max(y_coords))))
            
            height, width = mask.shape[:2]
            
            # Fill bounding box with color
            mask[min_y:max_y + 1, min_x:max_x + 1, 0] = color[0]
            mask[min_y:max_y + 1, min_x:max_x + 1, 1] = color[1]
            mask[min_y:max_y + 1, min_x:max_x + 1, 2] = color[2]
            
        except Exception as e:
            print(f"Error filling bounding box with color: {e}")
        
    def display_color_mask(self, mask):
        """Display the generated color mask"""
        if mask is None:
            self.clear_mask()
            return
            
        # Store the current mask for editing (ensure it's contiguous and right dtype)
        self.current_mask = np.ascontiguousarray(mask, dtype=np.uint8)
        print(f"Displaying mask: shape={self.current_mask.shape}, dtype={self.current_mask.dtype}")
        
        # Set the mask in the interactive view for editing
        self.graphics_view.set_mask(self.current_mask)
        
        # Convert to QPixmap (mask is already RGB)
        height, width, channels = self.current_mask.shape
        bytes_per_line = channels * width
        q_image = QImage(self.current_mask.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
        # Clear scene and add mask
        self.graphics_scene.clear()
        self.mask_item = QGraphicsPixmapItem(pixmap)
        self.graphics_scene.addItem(self.mask_item)
        
        # Store reference to mask item in the interactive view
        self.graphics_view.mask_item = self.mask_item
        print(f"Set mask_item in graphics_view, item bounds: {self.mask_item.boundingRect()}")
        
        # Fit in view
        self.graphics_view.fitInView(self.mask_item, Qt.KeepAspectRatio)
        
        # Hide placeholder
        self.placeholder_label.hide()
        
    def fill_polygon_in_mask(self, mask, polygon_points, mask_value):
        """Fill a polygon in the mask with the specified value"""
        try:
            if len(polygon_points) < 3:
                return
                
            height, width = mask.shape
            
            # Convert polygon points to integer coordinates
            points = []
            for point in polygon_points:
                try:
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
                        print(f"Unrecognized point format in polygon: {point}")
                        continue
                        
                    # Convert to integer and clamp to image bounds
                    x = max(0, min(width - 1, int(x)))
                    y = max(0, min(height - 1, int(y)))
                    points.append((x, y))
                    
                except (ValueError, TypeError, AttributeError) as e:
                    print(f"Error processing point {point}: {e}")
                    continue
                    
            if len(points) < 3:
                print(f"Not enough valid points for polygon fill: {len(points)}")
                return
                
            print(f"Filling polygon with {len(points)} points, mask value {mask_value}")
                
            # Simple polygon fill using scanline algorithm
            # For each row, find intersection points and fill between pairs
            min_y = min(p[1] for p in points)
            max_y = max(p[1] for p in points)
            
            for y in range(max(0, min_y), min(height, max_y + 1)):
                intersections = []
                
                # Find intersections with polygon edges
                for i in range(len(points)):
                    p1 = points[i]
                    p2 = points[(i + 1) % len(points)]
                    
                    if p1[1] != p2[1]:  # Not horizontal line
                        # Check if scanline intersects this edge
                        if min(p1[1], p2[1]) <= y < max(p1[1], p2[1]):
                            # Calculate intersection x coordinate
                            x = p1[0] + (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])
                            intersections.append(int(x))
                
                # Sort intersections and fill between pairs
                intersections.sort()
                for i in range(0, len(intersections) - 1, 2):
                    x1 = max(0, min(width - 1, intersections[i]))
                    x2 = max(0, min(width - 1, intersections[i + 1]))
                    if x1 <= x2:
                        mask[y, x1:x2 + 1] = mask_value
                        
        except Exception as e:
            print(f"Error filling polygon: {e}")
            # Fall back to bounding box fill
            self.fill_bounding_box_in_mask(mask, polygon_points, mask_value)
            
    def fill_bounding_box_in_mask(self, mask, polygon_points, mask_value):
        """Fill bounding box of polygon as fallback"""
        try:
            if len(polygon_points) < 2:
                return
                
            height, width = mask.shape
            
            # Get bounding box
            x_coords = [int(p[0]) for p in polygon_points if len(p) >= 2]
            y_coords = [int(p[1]) for p in polygon_points if len(p) >= 2]
            
            if not x_coords or not y_coords:
                return
                
            min_x = max(0, min(x_coords))
            max_x = min(width - 1, max(x_coords))
            min_y = max(0, min(y_coords))
            max_y = min(height - 1, max(y_coords))
            
            # Fill bounding box
            mask[min_y:max_y + 1, min_x:max_x + 1] = mask_value
            
        except Exception as e:
            print(f"Error filling bounding box: {e}")
        
    def display_mask(self, mask):
        """Display the generated mask (backward compatibility - delegates to color mask display)"""
        if mask is None:
            self.clear_mask()
            return
        
        # Check if this is already a color mask or needs conversion
        if len(mask.shape) == 3:
            # Already a color mask
            self.display_color_mask(mask)
        else:
            # Convert grayscale mask to colored image for display
            colored_mask = self.mask_to_colored_image(mask)
            self.display_color_mask(colored_mask)
        
    def mask_to_colored_image(self, mask):
        """Convert grayscale mask to colored image for visualization"""
        # Create color map
        colors = [
            [0, 0, 0],       # Background - black
            [255, 0, 0],     # Class 1 - red
            [0, 255, 0],     # Class 2 - green
            [0, 0, 255],     # Class 3 - blue
            [255, 255, 0],   # Class 4 - yellow
            [255, 0, 255],   # Class 5 - magenta
            [0, 255, 255],   # Class 6 - cyan
            [255, 128, 0],   # Class 7 - orange
            [128, 0, 255],   # Class 8 - purple
        ]
        
        # Extend colors if needed
        max_value = int(mask.max())
        while len(colors) <= max_value:
            colors.append([np.random.randint(0, 256) for _ in range(3)])
            
        # Create colored image
        colored = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
        for i in range(len(colors)):
            if i <= max_value:
                colored[mask == i] = colors[i]
                
        return colored
        
    def apply_manual_edits(self, edits):
        """Apply manual edits to the current mask"""
        self.manual_edits = edits
        if self.current_mask is not None:
            self.regenerate_mask()
            
    def apply_manual_edits_to_mask(self, mask):
        """Apply stored manual edits to a mask"""
        if self.manual_edits is None:
            return mask
            
        # TODO: Apply manual brush strokes/edits to the mask
        # This would involve applying the edits from the annotation editor
        return mask
        
    def export_mask(self):
        """Export the current mask to file"""
        if self.current_mask is None:
            QMessageBox.warning(self, "No Mask", "No mask to export. Generate a mask first.")
            return
            
        if not self.current_image_path:
            QMessageBox.warning(self, "No Image", "No current image loaded.")
            return
            
        try:
            # Generate mask filename based on the current image name
            import os
            image_dir = os.path.dirname(self.current_image_path)
            image_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
            
            # Create masks subdirectory if it doesn't exist
            masks_dir = os.path.join(image_dir, "masks")
            os.makedirs(masks_dir, exist_ok=True)
            
            # Generate mask filename with .png extension
            mask_filename = f"{image_name}_mask.png"
            file_path = os.path.join(masks_dir, mask_filename)
            
            # Save as PNG image (mask is already in RGB format)
            if len(self.current_mask.shape) == 3:
                # Color mask - save directly
                height, width, channels = self.current_mask.shape
                q_image = QImage(self.current_mask.data, width, height, 
                               width * channels, QImage.Format_RGB888)
            else:
                # Grayscale mask - convert to color first
                colored_mask = self.mask_to_colored_image(self.current_mask)
                height, width, channels = colored_mask.shape
                q_image = QImage(colored_mask.data, width, height, 
                               width * channels, QImage.Format_RGB888)
            
            q_image.save(file_path)
            
            self.status_label.setText(f"Mask exported to {mask_filename}")
            QMessageBox.information(self, "Export Success", f"Mask exported to:\n{file_path}")
            
            # Store the mask path in the parent window for JSON saving
            if self.parent_window and self.current_image_path:
                self.parent_window.set_mask_path(self.current_image_path, file_path)
                print(f"DEBUG: Called set_mask_path with current_image_path='{self.current_image_path}' and file_path='{file_path}'")
                print(f"Stored mask path for {self.current_image_path}: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export mask:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def load_existing_mask_if_available(self):
        """Check for existing mask and load it if available"""
        if not self.current_image_path or not self.parent_window:
            print("Cannot load existing mask: no image path or parent window")
            return
            
        try:
            # Get mask path from parent window
            mask_path = self.parent_window.get_mask_path(self.current_image_path)
            print(f"Checking for existing mask at: {mask_path}")
            
            if mask_path and os.path.exists(mask_path):
                print(f"Loading existing mask: {mask_path}")
                
                # Load the mask image
                mask_pixmap = QPixmap(mask_path)
                if not mask_pixmap.isNull():
                    # Convert QPixmap to numpy array for processing
                    q_image = mask_pixmap.toImage()
                    width = q_image.width()
                    height = q_image.height()
                    
                    # Convert to numpy array
                    ptr = q_image.bits()
                    ptr.setsize(height * width * 4)  # 4 bytes per pixel (RGBA)
                    arr = np.array(ptr).reshape(height, width, 4)
                    
                    # Convert RGBA to RGB and store as current mask
                    self.current_mask = arr[:, :, :3]  # Remove alpha channel
                    
                    # Display the loaded mask
                    self.display_mask(mask_pixmap)
                    
                    self.status_label.setText(f"Loaded existing mask: {os.path.basename(mask_path)}")
                    print(f"Successfully loaded existing mask: {mask_path}")
                else:
                    print(f"Failed to load mask image: {mask_path}")
            else:
                if mask_path:
                    print(f"Mask path exists in data but file not found: {mask_path}")
                else:
                    print("No existing mask found for this image")
                    
        except Exception as e:
            print(f"Error loading existing mask: {e}")
            import traceback
            traceback.print_exc()
    
    def display_mask(self, mask_pixmap):
        """Display a mask pixmap in the graphics view"""
        try:
            # Clear previous content
            self.graphics_scene.clear()
            
            # Hide placeholder
            self.placeholder_label.hide()
            
            # Add the mask pixmap to the scene
            self.graphics_scene.addPixmap(mask_pixmap)
            
            # Fit the view to the mask
            self.graphics_view.fitInView(self.graphics_scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            
        except Exception as e:
            print(f"Error displaying mask: {e}")
                
    def clear_mask(self):
        """Clear the displayed mask"""
        self.graphics_scene.clear()
        self.current_mask = None
        self.placeholder_label.show()
        
    def get_current_mask(self):
        """Get the current mask array"""
        return self.current_mask
