from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, 
                             QListWidgetItem, QFrame, QHBoxLayout, QPushButton,
                             QScrollArea, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QIcon
import os

class ImageListItem(QListWidgetItem):
    """Custom list item for image display"""
    
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.setToolTip(image_path)
        
        # Create thumbnail
        self.create_thumbnail()
        
    def create_thumbnail(self):
        """Create thumbnail for the image"""
        if os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                # Scale to thumbnail size
                thumbnail = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.setIcon(QIcon(thumbnail))
                
                # Set text to filename
                filename = os.path.basename(self.image_path)
                self.setText(filename)
            else:
                self.setText("Invalid Image")
        else:
            self.setText("File Not Found")

class ImageSelector(QWidget):
    """Right panel: Image selection similar to main window"""
    
    imageSelected = pyqtSignal(str)  # Emitted when image is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.image_paths = []
        self.current_image_index = -1
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the image selector UI"""
        layout = QVBoxLayout(self)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        
        title = QLabel("Images")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        header_layout.addWidget(title)
        
        # Load images button
        self.load_btn = QPushButton("Load")
        self.load_btn.clicked.connect(self.load_images)
        self.load_btn.setMaximumWidth(60)
        header_layout.addWidget(self.load_btn)
        
        layout.addLayout(header_layout)
        
        # Image list
        self.image_list = QListWidget()
        self.image_list.setIconSize(QSize(64, 64))
        self.image_list.setGridSize(QSize(80, 90))
        self.image_list.setViewMode(QListWidget.IconMode)
        self.image_list.setResizeMode(QListWidget.Adjust)
        self.image_list.setFrameStyle(QFrame.StyledPanel)
        
        # Connect selection signal
        self.image_list.itemClicked.connect(self.on_image_selected)
        
        layout.addWidget(self.image_list)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.select_previous)
        self.prev_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.select_next)
        self.next_btn.setEnabled(False)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        
        # Status label
        self.status_label = QLabel("No images loaded")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(self.status_label)
        
        # Load images from main window if available
        self.load_from_main_window()
        
    def load_images(self):
        """Load images from directory or files"""
        # First try to load from main window, fall back to manual loading
        if self.load_from_main_window():
            return
            
        # Manual loading as fallback
        image_dir = QFileDialog.getExistingDirectory(
            self, 
            "Select Image Directory",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if image_dir:
            self.load_images_from_directory(image_dir)
            
    def load_images_from_directory(self, directory):
        """Load all images from a directory"""
        if not os.path.exists(directory):
            return
            
        # Supported image extensions
        extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
        
        # Find all image files
        image_files = []
        for filename in os.listdir(directory):
            if any(filename.lower().endswith(ext) for ext in extensions):
                image_files.append(os.path.join(directory, filename))
                
        image_files.sort()  # Sort alphabetically
        
        if image_files:
            self.load_image_list(image_files)
        else:
            QMessageBox.information(self, "No Images", "No image files found in the selected directory.")
            
    def load_image_list(self, image_paths):
        """Load a list of image paths"""
        self.image_paths = image_paths
        self.current_image_index = -1
        
        # Clear existing items
        self.image_list.clear()
        
        # Add image items
        for image_path in image_paths:
            item = ImageListItem(image_path)
            self.image_list.addItem(item)
            
        # Update status
        self.status_label.setText(f"{len(image_paths)} images loaded")
        
        # Enable navigation if we have images
        self.update_navigation_buttons()
        
        # Select first image if available
        if image_paths:
            self.select_image_by_index(0)
            
    def on_image_selected(self, item):
        """Handle image selection from list"""
        if isinstance(item, ImageListItem):
            # Find index of selected item
            for i in range(self.image_list.count()):
                if self.image_list.item(i) == item:
                    self.select_image_by_index(i)
                    break
                    
    def select_image_by_index(self, index):
        """Select image by index"""
        if 0 <= index < len(self.image_paths):
            self.current_image_index = index
            image_path = self.image_paths[index]
            
            # Update list selection
            self.image_list.setCurrentRow(index)
            
            # Update navigation buttons
            self.update_navigation_buttons()
            
            # Update status
            filename = os.path.basename(image_path)
            self.status_label.setText(f"{index + 1}/{len(self.image_paths)}: {filename}")
            
            # Emit signal
            self.imageSelected.emit(image_path)
            
    def select_previous(self):
        """Select previous image"""
        if self.current_image_index > 0:
            self.select_image_by_index(self.current_image_index - 1)
            
    def select_next(self):
        """Select next image"""
        if self.current_image_index < len(self.image_paths) - 1:
            self.select_image_by_index(self.current_image_index + 1)
            
    def update_navigation_buttons(self):
        """Update the state of navigation buttons"""
        has_images = len(self.image_paths) > 0
        self.prev_btn.setEnabled(has_images and self.current_image_index > 0)
        self.next_btn.setEnabled(has_images and self.current_image_index < len(self.image_paths) - 1)
        
    def get_current_image_path(self):
        """Get the currently selected image path"""
        if 0 <= self.current_image_index < len(self.image_paths):
            return self.image_paths[self.current_image_index]
        return None
        
    def load_from_main_window(self):
        """Load images from main window's image manager"""
        try:
            if (self.parent_window and 
                hasattr(self.parent_window, 'main_window') and 
                self.parent_window.main_window):
                
                main_window = self.parent_window.main_window
                
                # Access the raster manager from the image window
                if (hasattr(main_window, 'image_window') and 
                    hasattr(main_window.image_window, 'raster_manager') and
                    hasattr(main_window.image_window.raster_manager, 'image_paths')):
                    
                    raster_manager = main_window.image_window.raster_manager
                    image_paths = raster_manager.image_paths
                    
                    if image_paths:
                        self.load_image_list(image_paths)
                        
                        # Set current image to match main window's current image
                        if hasattr(raster_manager, 'current_image_path') and raster_manager.current_image_path:
                            current_path = raster_manager.current_image_path
                            if current_path in image_paths:
                                current_index = image_paths.index(current_path)
                                self.select_image_by_index(current_index)
                        
                        return True
                        
            return False
            
        except Exception as e:
            print(f"Error loading from main window: {e}")
            return False
        
    def refresh_from_main_window(self):
        """Refresh image list from main window"""
        self.load_from_main_window()
        
    def clear_images(self):
        """Clear all loaded images"""
        self.image_paths = []
        self.current_image_index = -1
        self.image_list.clear()
        self.status_label.setText("No images loaded")
        self.update_navigation_buttons()
