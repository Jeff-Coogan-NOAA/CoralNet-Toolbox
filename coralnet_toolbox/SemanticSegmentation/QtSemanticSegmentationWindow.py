from PyQt5.QtWidgets import (QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout, 
                             QSplitter, QListWidget, QListWidgetItem, QPushButton, 
                             QScrollArea, QFrame, QButtonGroup, QToolButton, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QDrag

from .QtAnnotationImageViewer import AnnotationImageViewer
from .QtSortableAnnotationList import SortableAnnotationList
from .QtMaskGenerator import MaskGenerator
from .QtImageSelector import ImageSelector
from .QtAnnotationEditor import AnnotationEditor

class SemanticSegmentationWindow(QMainWindow):
    # Signal emitted when the window is closed
    windowClosed = pyqtSignal()
    def __init__(self, main_window, parent=None):
        super(SemanticSegmentationWindow, self).__init__(parent)
        print("Initializing Semantic Segmentation Window...")
        
        # Set proper window attributes
        self.setAttribute(Qt.WA_DeleteOnClose)  # Ensure proper cleanup
        self.setWindowModality(Qt.NonModal)     # Make sure it's not modal
        
        self.main_window = main_window
        self.setWindowTitle("Semantic Segmentation")
        self.setGeometry(100, 100, 1400, 800)
        
        # TODO: Connect to project JSON data
        self.current_image_path = None
        self.annotations = []
        self.annotation_types = []
        
        # New data structures for semantic segmentation
        self.annotation_order_dict = {}  # Store annotation order by image path
        self.mask_path_dict = {}  # Store mask paths by image path
        
        print("Setting up UI...")
        self.setup_ui()
        
        print("Connecting signals...")
        self.connect_signals()
        
        print("Semantic Segmentation Window initialized successfully")
        
    def setup_ui(self):
        """Set up the main UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create main splitter for resizable panels
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Image with annotations
        self.annotation_viewer = AnnotationImageViewer(self)
        main_splitter.addWidget(self.annotation_viewer)
        
        # Center panel: Sortable annotation types
        center_frame = QFrame()
        center_frame.setFrameStyle(QFrame.StyledPanel)
        center_layout = QVBoxLayout(center_frame)
        
        sort_label = QLabel("Sort")
        sort_label.setAlignment(Qt.AlignCenter)
        sort_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        center_layout.addWidget(sort_label)
        
        self.sortable_list = SortableAnnotationList(self)
        center_layout.addWidget(self.sortable_list)
        
        main_splitter.addWidget(center_frame)
        
        # Center-right panel: Generated mask
        self.mask_generator = MaskGenerator(self)
        main_splitter.addWidget(self.mask_generator)
        
        # Right panel: Image selector
        self.image_selector = ImageSelector(self)
        main_splitter.addWidget(self.image_selector)
        
        # Set splitter proportions (left: 30%, center: 15%, mask: 30%, right: 25%)
        main_splitter.setSizes([420, 210, 420, 350])
        
        # Create vertical splitter for main content and bottom panel
        vertical_splitter = QSplitter(Qt.Vertical)
        vertical_splitter.addWidget(main_splitter)
        
        # Bottom panel: Annotation editor
        self.annotation_editor = AnnotationEditor(self)
        vertical_splitter.addWidget(self.annotation_editor)
        
        # Set vertical proportions (main: 70%, bottom: 30%)
        vertical_splitter.setSizes([560, 240])
        
        main_layout.addWidget(vertical_splitter)
        
    def connect_signals(self):
        """Connect signals between components"""
        # Connect sortable list changes to mask regeneration
        self.sortable_list.orderChanged.connect(self.mask_generator.regenerate_mask)
        
        # Connect image selection to update views
        self.image_selector.imageSelected.connect(self.load_image)
        
        # Connect annotation editor to mask updates
        self.annotation_editor.maskEdited.connect(self.mask_generator.apply_manual_edits)
        
        # Connect annotation type updates between components
        self.sortable_list.orderChanged.connect(lambda order: self.annotation_editor.update_annotation_types_with_order(order, preserve_order=True))
        
        # Connect to save annotation order when it changes
        self.sortable_list.orderChanged.connect(self.save_annotation_order)
        
        # TODO: Connect to main window's project data
        # self.main_window.projectLoaded.connect(self.load_project_data)
        # self.main_window.imageChanged.connect(self.update_current_image)
        
        # Load initial data from main window if available (deferred)
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self.load_from_main_window)
        
        # Add debug option (temporary)
        QTimer.singleShot(200, self.debug_main_window_data)
        
    def load_image(self, image_path):
        """Load an image and its annotations"""
        print(f"Loading image: {image_path}")
        
        # Check if this is actually a different image
        if self.current_image_path == image_path:
            print(f"Same image path, but refreshing annotations: {image_path}")
            # Even if it's the same path, refresh the annotations in case they've changed
            self.annotation_viewer.refresh_annotations()
            return
            
        self.current_image_path = image_path
        
        try:
            # Update annotation viewer
            print("Updating annotation viewer...")
            self.annotation_viewer.load_image(image_path)
            
            # Update mask generator
            print("Updating mask generator...")
            self.mask_generator.load_image(image_path)
            
            # Update sortable list with annotation types - check for saved order first
            print("Updating annotation types...")
            self.load_annotation_order_from_image(image_path)
            
            # Refresh annotation editor colors to match current labels
            self.annotation_editor.refresh_annotation_colors()
            
            # Update image selector to match current selection (without triggering signals)
            if (hasattr(self.image_selector, 'image_paths') and 
                self.image_selector.image_paths and 
                image_path in self.image_selector.image_paths):
                
                print("Updating image selector selection...")
                current_index = self.image_selector.image_paths.index(image_path)
                self.image_selector.blockSignals(True)
                self.image_selector.select_image_by_index(current_index)
                self.image_selector.blockSignals(False)
                
            print(f"Successfully loaded image: {image_path}")
            
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            import traceback
            traceback.print_exc()
        
    def update_annotation_types(self):
        """Update the sortable list with annotation types - prioritize ALL label types from main window"""
        print("Updating annotation types...")
        
        annotation_types = []
        
        # FIRST: Try to get ALL label types from main window (this should be the primary source)
        if self.load_annotation_types_from_main_window():
            print("Successfully loaded annotation types from main window labels")
            return
        
        # FALLBACK: If no labels in main window, try to get from current image annotations
        if self.current_image_path:
            try:
                annotations = self.get_annotations_for_current_image()
                if annotations:
                    # Extract unique annotation types from current image
                    # Handle the case where label is a Label object with short_label_code
                    annotation_types = []
                    for ann in annotations:
                        if hasattr(ann, 'label') and ann.label:
                            label_text = None
                            if hasattr(ann.label, 'short_label_code'):
                                label_text = ann.label.short_label_code
                            elif hasattr(ann.label, 'long_label_code'):
                                label_text = ann.label.long_label_code
                            elif isinstance(ann.label, str):
                                label_text = ann.label
                            else:
                                label_text = str(ann.label)
                            
                            if label_text and label_text not in annotation_types:
                                annotation_types.append(label_text)
                    
                    if annotation_types:
                        print(f"Found annotation types from current image (fallback): {annotation_types}")
                        self.sortable_list.update_types(annotation_types)
                        self.annotation_editor.update_annotation_types_with_order(annotation_types, preserve_order=False)
                        return
            except Exception as e:
                print(f"Error getting annotation types from current image: {e}")
            
        # Final fallback - placeholder annotation types
        print("Using placeholder annotation types")
        annotation_types = ["Coral", "Sand", "Rock", "Algae", "Fish"]
        self.sortable_list.update_types(annotation_types)
        self.annotation_editor.update_annotation_types_with_order(annotation_types, preserve_order=False)
        
    def get_annotations_for_current_image(self):
        """Get annotations for the currently loaded image"""
        if not self.current_image_path or not self.main_window:
            print("No current image or main window")
            return []
            
        try:
            print(f"Getting annotations for image: {self.current_image_path}")
            
            # Access main window's annotation system - use image_annotations_dict not annotations_dict
            if (hasattr(self.main_window, 'annotation_window') and 
                hasattr(self.main_window.annotation_window, 'image_annotations_dict')):
                
                image_annotations_dict = self.main_window.annotation_window.image_annotations_dict
                print(f"Found image_annotations_dict with {len(image_annotations_dict)} entries")
                
                # Check if current image path exists in annotations
                current_path = self.current_image_path
                
                # Print all available paths for debugging
                print(f"Current image path: '{current_path}'")
                print("Available annotation paths:")
                for i, path in enumerate(list(image_annotations_dict.keys())[:10]):  # Show first 10
                    print(f"  [{i}] '{path}'")
                if len(image_annotations_dict) > 10:
                    print(f"  ... and {len(image_annotations_dict) - 10} more")
                
                # Try exact match first
                if current_path in image_annotations_dict:
                    annotations = image_annotations_dict[current_path]
                    print(f"Found {len(annotations)} annotations for current image (exact match)")
                    self.print_annotation_details(annotations)
                    return annotations
                
                # Try to find similar paths with different separators
                import os
                current_path_normalized = os.path.normpath(current_path)
                for path, annotations in image_annotations_dict.items():
                    path_normalized = os.path.normpath(path)
                    if current_path_normalized == path_normalized:
                        print(f"Found {len(annotations)} annotations for current image (normalized path match)")
                        print(f"Matched path: '{path}' -> '{path_normalized}'")
                        self.print_annotation_details(annotations)
                        return annotations
                
                # Try basename matching
                current_basename = os.path.basename(current_path)
                for path, annotations in image_annotations_dict.items():
                    if os.path.basename(path) == current_basename:
                        print(f"Found {len(annotations)} annotations for current image (basename match)")
                        print(f"Matched path: '{path}' (basename: '{current_basename}')")
                        self.print_annotation_details(annotations)
                        return annotations
                
                # Try case-insensitive matching
                current_path_lower = current_path.lower()
                for path, annotations in image_annotations_dict.items():
                    if path.lower() == current_path_lower:
                        print(f"Found {len(annotations)} annotations for current image (case-insensitive match)")
                        print(f"Matched path: '{path}'")
                        self.print_annotation_details(annotations)
                        return annotations
                
                print(f"No annotations found for image: {current_path}")
                    
            else:
                print("No annotation window or image_annotations_dict found")
                
            return []
            
        except Exception as e:
            print(f"Error getting annotations: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def print_annotation_details(self, annotations):
        """Print details about annotations for debugging"""
        if not annotations:
            print("No annotations to print details for")
            return
            
        print(f"Annotation details for {len(annotations)} annotations:")
        for i, ann in enumerate(annotations[:5]):  # Show first 5 annotations
            try:
                ann_type = type(ann).__name__ if ann else "Unknown"
                label = getattr(ann, 'label', 'No label') if ann else 'No label'
                
                # Check for different point attributes
                points_info = "No points"
                points_count = 0
                
                if hasattr(ann, 'polygon_points') and ann.polygon_points:
                    points_count = len(ann.polygon_points)
                    points_info = f"polygon_points: {points_count} points"
                elif hasattr(ann, 'points') and ann.points:
                    points_count = len(ann.points)
                    points_info = f"points: {points_count} points"
                elif hasattr(ann, 'vertices') and ann.vertices:
                    points_count = len(ann.vertices)
                    points_info = f"vertices: {points_count} points"
                
                # Check for other common attributes
                other_attrs = []
                for attr in ['x', 'y', 'width', 'height', 'center_x', 'center_y', 'radius']:
                    if hasattr(ann, attr):
                        value = getattr(ann, attr)
                        other_attrs.append(f"{attr}={value}")
                
                other_info = f", other: {', '.join(other_attrs)}" if other_attrs else ""
                
                print(f"  [{i}] Type: {ann_type}, Label: '{label}', {points_info}{other_info}")
                
                # Show first few points if available
                if points_count > 0:
                    points = None
                    if hasattr(ann, 'polygon_points') and ann.polygon_points:
                        points = ann.polygon_points
                    elif hasattr(ann, 'points') and ann.points:
                        points = ann.points
                    elif hasattr(ann, 'vertices') and ann.vertices:
                        points = ann.vertices
                    
                    if points:
                        print(f"      First few points: {points[:3]}...")
                        
            except Exception as e:
                print(f"  [{i}] Error printing annotation details: {e}")
        
        if len(annotations) > 5:
            print(f"  ... and {len(annotations) - 5} more annotations")
        
    def get_annotation_types_for_image(self, image_path):
        """Get unique annotation types for a specific image"""
        annotation_types = []
        
        try:
            # Get annotations for the specified image
            if (self.main_window and 
                hasattr(self.main_window, 'annotation_window') and 
                hasattr(self.main_window.annotation_window, 'image_annotations_dict')):
                
                image_annotations_dict = self.main_window.annotation_window.image_annotations_dict
                
                # Try exact match first
                annotations = None
                if image_path in image_annotations_dict:
                    annotations = image_annotations_dict[image_path]
                else:
                    # Try normalized path matching
                    import os
                    image_path_normalized = os.path.normpath(image_path)
                    for path, anns in image_annotations_dict.items():
                        if os.path.normpath(path) == image_path_normalized:
                            annotations = anns
                            break
                
                if annotations:
                    # Extract unique annotation types
                    for ann in annotations:
                        if hasattr(ann, 'label') and ann.label:
                            label_text = None
                            if hasattr(ann.label, 'short_label_code'):
                                label_text = ann.label.short_label_code
                            elif hasattr(ann.label, 'long_label_code'):
                                label_text = ann.label.long_label_code
                            elif isinstance(ann.label, str):
                                label_text = ann.label
                            else:
                                label_text = str(ann.label)
                            
                            if label_text and label_text not in annotation_types:
                                annotation_types.append(label_text)
                                
        except Exception as e:
            print(f"Error getting annotation types for image {image_path}: {e}")
            
        return annotation_types
        
    def get_current_sort_order(self):
        """Get the current sort order from the sortable list"""
        order = self.sortable_list.get_sort_order()
        print(f"SemanticSegmentationWindow.get_current_sort_order: {order}")
        return order
        
    def save_mask_edits(self, mask_data):
        """Save manual mask edits"""
        # TODO: Save mask edits to project JSON or separate mask file
        pass
    
    def load_from_main_window(self):
        """Load initial data from the main window"""
        if not self.main_window:
            print("No main window available")
            return
            
        try:
            print("Loading data from main window...")
            
            # Load images from main window's raster manager
            image_paths = []
            current_image = None
            
            if (hasattr(self.main_window, 'image_window') and 
                hasattr(self.main_window.image_window, 'raster_manager')):
                
                raster_manager = self.main_window.image_window.raster_manager
                
                if (hasattr(raster_manager, 'image_paths') and 
                    raster_manager.image_paths):
                    
                    image_paths = raster_manager.image_paths
                    print(f"Found {len(image_paths)} images")
                    
                    # Get current image
                    if (hasattr(raster_manager, 'current_image_path') and 
                        raster_manager.current_image_path):
                        current_image = raster_manager.current_image_path
                        print(f"Current image: {current_image}")
                    elif image_paths:
                        current_image = image_paths[0]
                        print(f"Using first image: {current_image}")
                else:
                    print("No image paths found in raster manager")
            else:
                print("No raster manager found")
            
            # Load images into the image selector (without triggering signals)
            if image_paths:
                self.image_selector.blockSignals(True)
                self.image_selector.load_image_list(image_paths)
                self.image_selector.blockSignals(False)
            
            # Load existing semantic segmentation data (mask paths and annotation orders)
            if hasattr(self.main_window, 'semantic_segmentation_data') and self.main_window.semantic_segmentation_data:
                print("Loading existing semantic segmentation data...")
                self.load_semantic_segmentation_data(self.main_window.semantic_segmentation_data)
            
            # Load annotation types from labels
            annotation_types_loaded = self.load_annotation_types_from_main_window()
            
            # Load current image last to avoid circular updates
            if current_image:
                print(f"Loading current image: {current_image}")
                self.load_image(current_image)
            elif not annotation_types_loaded:
                print("Loading fallback annotation types")
                # Only load fallback if no real annotation types were found
                self.update_annotation_types()
            
            # Additional fallback: ensure sortable list has content
            if self.sortable_list.count() == 0:
                print("Sortable list is empty - forcing annotation type update")
                self.update_annotation_types()
            
        except Exception as e:
            print(f"Error loading from main window: {e}")
            import traceback
            traceback.print_exc()
            # Fall back to placeholder data
            self.update_annotation_types()
            
    def load_annotation_types_from_main_window(self):
        """Load annotation types from the main window's label system"""
        try:
            print("Loading annotation types from main window labels...")
            
            # Try to get labels from the label window's labels list (not labels_dict)
            if (hasattr(self.main_window, 'label_window') and 
                hasattr(self.main_window.label_window, 'labels')):
                
                labels_list = self.main_window.label_window.labels
                print(f"Found labels list with {len(labels_list)} entries")
                
                # Extract label codes from the label objects
                annotation_types = []
                for label in labels_list:
                    if hasattr(label, 'short_label_code') and label.short_label_code:
                        annotation_types.append(label.short_label_code)
                        print(f"Found label: '{label.short_label_code}' (color: {label.color})")
                    elif hasattr(label, 'long_label_code') and label.long_label_code:
                        annotation_types.append(label.long_label_code)
                        print(f"Found label: '{label.long_label_code}' (color: {label.color})")
                
                if annotation_types:
                    print(f"Found annotation types from labels: {annotation_types}")
                    self.annotation_types = annotation_types
                    self.sortable_list.update_types(annotation_types)
                    self.annotation_editor.update_annotation_types_with_order(annotation_types, preserve_order=False)
                    return True
                else:
                    print("No valid annotation types found in labels list")
            else:
                print("No label window or labels list found")
            
            # Alternative: Try to get annotation types from all annotations in the project
            print("Trying to extract annotation types from all project annotations...")
            if (hasattr(self.main_window, 'annotation_window') and 
                hasattr(self.main_window.annotation_window, 'image_annotations_dict')):
                
                image_annotations_dict = self.main_window.annotation_window.image_annotations_dict
                print(f"Found {len(image_annotations_dict)} images with annotations")
                
                all_labels = set()
                annotation_count = 0
                
                for image_path, annotations in image_annotations_dict.items():
                    print(f"  Image: {image_path} has {len(annotations)} annotations")
                    for annotation in annotations:
                        annotation_count += 1
                        if hasattr(annotation, 'label') and annotation.label:
                            # Extract string from Label object
                            label_text = None
                            if hasattr(annotation.label, 'short_label_code'):
                                label_text = annotation.label.short_label_code
                            elif hasattr(annotation.label, 'long_label_code'):
                                label_text = annotation.label.long_label_code
                            elif isinstance(annotation.label, str):
                                label_text = annotation.label
                            else:
                                label_text = str(annotation.label)
                            
                            if label_text:
                                all_labels.add(label_text)
                                print(f"    Found label: '{label_text}' (type: {type(annotation).__name__})")
                
                print(f"Total annotations processed: {annotation_count}")
                print(f"Unique labels found: {list(all_labels)}")
                
                annotation_types = list(all_labels)
                if annotation_types:
                    print(f"Found annotation types from project annotations: {annotation_types}")
                    self.annotation_types = annotation_types
                    self.sortable_list.update_types(annotation_types)
                    self.annotation_editor.update_annotation_types_with_order(annotation_types, preserve_order=False)
                    return True
                else:
                    print("No labels found in any annotations")
                    
            return False
            
        except Exception as e:
            print(f"Error loading annotation types: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def sync_with_main_window_image(self):
        """Sync the current image with the main window's current image"""
        try:
            if (self.main_window and 
                hasattr(self.main_window, 'image_window') and
                hasattr(self.main_window.image_window, 'raster_manager')):
                
                raster_manager = self.main_window.image_window.raster_manager
                
                if (hasattr(raster_manager, 'current_image_path') and 
                    raster_manager.current_image_path):
                    
                    current_path = raster_manager.current_image_path
                    if current_path != self.current_image_path:
                        self.load_image(current_path)
                        
        except Exception as e:
            print(f"Error syncing with main window image: {e}")
    
    def save_annotation_order(self, annotation_order):
        """Save the annotation order for the current image"""
        print(f"save_annotation_order called with: {annotation_order}")
        print(f"Current image path: {self.current_image_path}")
        print(f"Annotation order is truthy: {bool(annotation_order)}")
        
        if self.current_image_path and annotation_order:
            self.annotation_order_dict[self.current_image_path] = annotation_order[:]
            print(f"Saved annotation order for {self.current_image_path}: {annotation_order}")
            
            # Also update the main window's persistent data
            if (self.main_window and 
                hasattr(self.main_window, 'semantic_segmentation_data')):
                self.main_window.semantic_segmentation_data['annotation_order'][self.current_image_path] = annotation_order[:]
                print(f"Updated main window persistent annotation order data")
        else:
            if not self.current_image_path:
                print("WARNING: No current image path - cannot save annotation order")
            if not annotation_order:
                print("WARNING: Empty annotation order - not saving")
    
    def get_annotation_order(self, image_path=None):
        """Get the annotation order for the specified image (or current image)"""
        if not image_path:
            image_path = self.current_image_path
        
        if image_path in self.annotation_order_dict:
            return self.annotation_order_dict[image_path][:]
        return []
    
    def set_mask_path(self, image_path, mask_path):
        """Set the mask path for the specified image"""
        self.mask_path_dict[image_path] = mask_path
        print(f"DEBUG: set_mask_path called with image_path='{image_path}', mask_path='{mask_path}'")
        print(f"DEBUG: mask_path_dict now has {len(self.mask_path_dict)} entries")
        
        # Also update the main window's persistent data
        if (self.main_window and 
            hasattr(self.main_window, 'semantic_segmentation_data')):
            self.main_window.semantic_segmentation_data['mask_paths'][image_path] = mask_path
            print(f"DEBUG: Updated main window persistent mask path data")
            print(f"DEBUG: Main window semantic_segmentation_data['mask_paths'] now has {len(self.main_window.semantic_segmentation_data['mask_paths'])} entries")
        else:
            print(f"DEBUG: Could not update main window persistent data - main_window={bool(self.main_window)}, has_semantic_data={hasattr(self.main_window, 'semantic_segmentation_data') if self.main_window else False}")
    
    def get_mask_path(self, image_path=None):
        """Get the mask path for the specified image (or current image)"""
        if not image_path:
            image_path = self.current_image_path
        
        return self.mask_path_dict.get(image_path, "")
    
    def load_annotation_order_from_image(self, image_path):
        """Load annotation order for an image when it's selected"""
        if image_path in self.annotation_order_dict:
            saved_order = self.annotation_order_dict[image_path]
            print(f"Loading saved annotation order for {image_path}: {saved_order}")
            
            # Get ALL available annotation types (from labels first, then from image)
            all_annotation_types = []
            
            # First, try to get annotation types from main window labels
            if (hasattr(self, 'main_window') and self.main_window and 
                hasattr(self.main_window, 'label_window') and self.main_window.label_window and
                hasattr(self.main_window.label_window, 'labels') and self.main_window.label_window.labels):
                
                labels_list = self.main_window.label_window.labels
                all_annotation_types = []
                for label in labels_list:
                    if hasattr(label, 'short_label_code') and label.short_label_code:
                        all_annotation_types.append(label.short_label_code)
                    elif hasattr(label, 'long_label_code') and label.long_label_code:
                        all_annotation_types.append(label.long_label_code)
                        
                print(f"Found annotation types from main window labels: {all_annotation_types}")
            
            # If no label types available, fall back to current image annotation types
            if not all_annotation_types:
                all_annotation_types = self.get_annotation_types_for_image(image_path)
                print(f"Using annotation types from image: {all_annotation_types}")
            
            # Create final order: start with saved order items that are still valid
            final_order = [ann_type for ann_type in saved_order if ann_type in all_annotation_types]
            
            # Add any annotation types that aren't in the saved order to the bottom
            for ann_type in all_annotation_types:
                if ann_type not in final_order:
                    final_order.append(ann_type)
                    print(f"Added annotation type '{ann_type}' to bottom of order")
            
            # If we have no annotation types at all, try to get them from labels
            if not final_order:
                print("No annotation types found, trying to load from main window labels...")
                if self.load_annotation_types_from_main_window():
                    return
                else:
                    # Ultimate fallback
                    final_order = ["Coral", "Sand", "Rock", "Algae", "Fish"]
                    print("Using placeholder annotation types")
            
            print(f"Final annotation order: {final_order}")
            self.sortable_list.update_types(final_order)
            self.annotation_editor.update_annotation_types_with_order(final_order, preserve_order=True)
        else:
            # No saved order, use default order from annotations
            print(f"No saved order for {image_path}, using default annotation order")
            self.update_annotation_types()
            
    def get_semantic_segmentation_data(self):
        """Get all semantic segmentation data for saving to JSON"""
        data = {
            'annotation_order': self.annotation_order_dict.copy(),
            'mask_paths': self.mask_path_dict.copy()
        }
        print(f"get_semantic_segmentation_data returning: annotation_order={data['annotation_order']}, mask_paths={data['mask_paths']}")
        return data
    
    def load_semantic_segmentation_data(self, data):
        """Load semantic segmentation data from JSON"""
        if 'annotation_order' in data:
            self.annotation_order_dict = data['annotation_order'].copy()
            print(f"Loaded annotation orders for {len(self.annotation_order_dict)} images")
            
        if 'mask_paths' in data:
            self.mask_path_dict = data['mask_paths'].copy()
            print(f"Loaded mask paths for {len(self.mask_path_dict)} images")
            
        # If current image is loaded, update its order
        if self.current_image_path:
            self.load_annotation_order_from_image(self.current_image_path)
        else:
            print("No current image set yet - will load annotation order when image is selected")
            
    def debug_main_window_data(self):
        """Debug function to print all available data structures in the main window"""
        print("\n" + "="*80)
        print("DEBUG: Main Window Data Structures")
        print("="*80)
        
        if not self.main_window:
            print("No main window available")
            return
        
        try:
            # Check main window attributes
            print(f"Main window type: {type(self.main_window).__name__}")
            
            # Check label window
            if hasattr(self.main_window, 'label_window'):
                label_window = self.main_window.label_window
                print(f"\nLabel window type: {type(label_window).__name__}")
                
                if hasattr(label_window, 'labels'):
                    labels = label_window.labels
                    print(f"Labels list: {len(labels)} items")
                    for i, label in enumerate(labels[:5]):  # Show first 5
                        if hasattr(label, 'short_label_code') and hasattr(label, 'long_label_code'):
                            print(f"  [{i}] Short: '{label.short_label_code}', Long: '{label.long_label_code}'")
                        else:
                            print(f"  [{i}] Label object: {type(label).__name__}")
                    if len(labels) > 5:
                        print(f"  ... and {len(labels) - 5} more labels")
                else:
                    print("No 'labels' attribute found in label window")
            else:
                print("No label_window found in main window")
            
            # Check annotation window
            if hasattr(self.main_window, 'annotation_window'):
                annotation_window = self.main_window.annotation_window
                print(f"\nAnnotation window type: {type(annotation_window).__name__}")
                
                if hasattr(annotation_window, 'image_annotations_dict'):
                    image_annotations_dict = annotation_window.image_annotations_dict
                    print(f"Image annotations dict: {len(image_annotations_dict)} entries")
                    for i, (path, annotations) in enumerate(list(image_annotations_dict.items())[:3]):
                        print(f"  [{i}] '{path}': {len(annotations)} annotations")
                        for j, ann in enumerate(annotations[:2]):  # Show first 2 annotations per image
                            ann_type = type(ann).__name__
                            label = getattr(ann, 'label', 'No label')
                            print(f"    [{j}] Type: {ann_type}, Label: '{label}'")
                    if len(image_annotations_dict) > 3:
                        print(f"  ... and {len(image_annotations_dict) - 3} more images")
                else:
                    print("No 'image_annotations_dict' attribute found in annotation window")
                    
                if hasattr(annotation_window, 'annotations_dict'):
                    annotations_dict = annotation_window.annotations_dict
                    print(f"Annotations dict (by UUID): {len(annotations_dict)} entries")
                else:
                    print("No 'annotations_dict' attribute found in annotation window")
            else:
                print("No annotation_window found in main window")
            
            # Check image window
            if hasattr(self.main_window, 'image_window'):
                image_window = self.main_window.image_window
                print(f"\nImage window type: {type(image_window).__name__}")
                
                if hasattr(image_window, 'raster_manager'):
                    raster_manager = image_window.raster_manager
                    print(f"Raster manager type: {type(raster_manager).__name__}")
                    
                    if hasattr(raster_manager, 'image_paths'):
                        image_paths = raster_manager.image_paths
                        print(f"Image paths: {len(image_paths) if image_paths else 0} entries")
                        if image_paths:
                            for i, path in enumerate(image_paths[:3]):
                                print(f"  [{i}] '{path}'")
                            if len(image_paths) > 3:
                                print(f"  ... and {len(image_paths) - 3} more images")
                    
                    if hasattr(raster_manager, 'current_image_path'):
                        current_path = raster_manager.current_image_path
                        print(f"Current image path: '{current_path}'")
                else:
                    print("No raster_manager found in image window")
            else:
                print("No image_window found in main window")
                
        except Exception as e:
            print(f"Error during debug: {e}")
            import traceback
            traceback.print_exc()
        
        print("="*80)
        print("END DEBUG")
        print("="*80 + "\n")
        
    def closeEvent(self, event):
        """Handle window close event to properly re-enable main window"""
        print("Semantic Segmentation window closing...")
        
        try:
            # Emit signal to notify main window
            self.windowClosed.emit()
            
            # Re-enable the main window
            if self.main_window:
                print("Re-enabling main window...")
                self.main_window.set_main_window_enabled_state(
                    enable_list=[self.main_window.toolbar, 
                                self.main_window.menu_bar, 
                                self.main_window.image_window, 
                                self.main_window.confidence_window,
                                self.main_window.annotation_window,
                                self.main_window.label_window],
                    disable_list=[]
                )
                
                # Clear the reference in main window
                self.main_window.semantic_segmentation_window = None
                
                # Activate the main window and ensure it gets focus
                self.main_window.activateWindow()
                self.main_window.raise_()
                self.main_window.setFocus()
                
                # Force Qt to process pending events to ensure focus is transferred
                from PyQt5.QtWidgets import QApplication
                QApplication.processEvents()
                
                print("Main window re-enabled successfully")
        
        except Exception as e:
            print(f"Error during close event: {e}")
            import traceback
            traceback.print_exc()
        
        # Accept the close event
        event.accept()
        print("Semantic Segmentation window closed")
