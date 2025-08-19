from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QPushButton, QFrame, QButtonGroup,
                             QToolButton, QSizePolicy, QSlider, QSpinBox,
                             QColorDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QIcon
import numpy as np

class AnnotationButton(QToolButton):
    """Custom button for annotation type selection"""
    
    def __init__(self, annotation_type, color, parent=None):
        super().__init__(parent)
        self.annotation_type = annotation_type
        self.color = color
        
        self.setText(annotation_type)
        self.setCheckable(True)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
        # Create color icon
        self.update_icon()
        
    def update_icon(self):
        """Update the button icon with current color"""
        # Create a colored square icon
        pixmap = QPixmap(24, 24)
        pixmap.fill(self.color)
        
        # Add border
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.black, 1))
        painter.drawRect(0, 0, 23, 23)
        painter.end()
        
        self.setIcon(QIcon(pixmap))
        self.setIconSize(QSize(24, 24))

class BrushToolWidget(QWidget):
    """Widget for brush tool controls"""
    
    brushSizeChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up brush tool controls"""
        layout = QHBoxLayout(self)
        
        # Brush size label
        label = QLabel("Brush Size:")
        layout.addWidget(label)
        
        # Brush size slider
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(1, 50)
        self.size_slider.setValue(5)
        self.size_slider.valueChanged.connect(self.on_size_changed)
        layout.addWidget(self.size_slider)
        
        # Brush size spinbox
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setRange(1, 50)
        self.size_spinbox.setValue(5)
        self.size_spinbox.valueChanged.connect(self.size_slider.setValue)
        layout.addWidget(self.size_spinbox)
        
    def on_size_changed(self, value):
        """Handle brush size change"""
        self.size_spinbox.setValue(value)
        self.brushSizeChanged.emit(value)
        
    def get_brush_size(self):
        """Get current brush size"""
        return self.size_slider.value()

class AnnotationEditor(QWidget):
    """Bottom panel: Manual annotation editing tools"""
    
    maskEdited = pyqtSignal(np.ndarray)  # Emitted when mask is manually edited
    annotationSelected = pyqtSignal(str)  # Emitted when annotation type is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.annotation_types = []
        self.annotation_buttons = []
        self.current_annotation_type = None
        self.brush_size = 5
        self.manual_edits = None
        
        # Default colors for annotation types
        self.default_colors = [
            QColor(255, 0, 0),    # Red
            QColor(0, 255, 0),    # Green
            QColor(0, 0, 255),    # Blue
            QColor(255, 255, 0),  # Yellow
            QColor(255, 0, 255),  # Magenta
            QColor(0, 255, 255),  # Cyan
            QColor(255, 128, 0),  # Orange
            QColor(128, 0, 255),  # Purple
        ]
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the annotation editor UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Manual Annotation Editor")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title)
        
        # Tool controls row - keep simple and stable
        tools_layout = QHBoxLayout()
        
        # Brush tool controls - always first
        self.brush_widget = BrushToolWidget(self)
        self.brush_widget.brushSizeChanged.connect(self.set_brush_size)
        tools_layout.addWidget(self.brush_widget)
        
        # Spacer to keep brush controls on the left
        tools_layout.addStretch()
        
        layout.addLayout(tools_layout)
        
        # Scrollable annotation buttons area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setMaximumHeight(120)
        scroll_area.setFrameStyle(QFrame.StyledPanel)
        
        # Widget to hold annotation buttons
        self.buttons_widget = QWidget()
        self.buttons_layout = QHBoxLayout(self.buttons_widget)
        self.buttons_layout.setAlignment(Qt.AlignLeft)
        
        scroll_area.setWidget(self.buttons_widget)
        layout.addWidget(scroll_area)
        
        # Button group for exclusive selection
        self.button_group = QButtonGroup(self)
        self.button_group.buttonClicked.connect(self.on_annotation_button_clicked)
        
        # Status label
        self.status_label = QLabel("Select an annotation type to start editing")
        self.status_label.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(self.status_label)
        
    def update_annotation_types(self, annotation_types):
        """Update available annotation types"""
        self.annotation_types = annotation_types
        
        # Clear existing layout completely
        while self.buttons_layout.count():
            child = self.buttons_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.spacerItem():
                # Remove spacer item
                del child
                
        # Clear button tracking
        for button in self.annotation_buttons:
            self.button_group.removeButton(button)
        self.annotation_buttons = []
        
        # Create new buttons
        for i, ann_type in enumerate(annotation_types):
            # Try to get the actual color from the main window's label system
            color = self.get_label_color_from_main_window(ann_type)
            
            # Fallback to default color if not found
            if color is None:
                color = self.default_colors[i % len(self.default_colors)]
            
            button = AnnotationButton(ann_type, color, self)
            
            # Add to layout and group
            self.buttons_layout.addWidget(button)
            self.button_group.addButton(button)
            self.annotation_buttons.append(button)
            
            # Connect double-click for color change
            button.mouseDoubleClickEvent = lambda event, btn=button: self.change_button_color(btn)
            
        # Add stretch to push buttons to left (only once)
        self.buttons_layout.addStretch()
        
        # Update status
        if annotation_types:
            self.status_label.setText(f"{len(annotation_types)} annotation types available")
        else:
            self.status_label.setText("No annotation types available")
            
        # Update mask generator tool if we have a current selection
        if self.current_annotation_type:
            self.update_mask_generator_tool()
            
    def on_annotation_button_clicked(self, button):
        """Handle annotation button selection"""
        if isinstance(button, AnnotationButton):
            self.current_annotation_type = button.annotation_type
            
            self.status_label.setText(f"Selected: {button.annotation_type} (brush size: {self.brush_size})")
            self.annotationSelected.emit(button.annotation_type)
            
            # Update the mask generator's drawing tool
            self.update_mask_generator_tool()
            
    def update_mask_generator_tool(self):
        """Update the mask generator with current drawing tool settings"""
        try:
            # Get the parent semantic segmentation window
            if (self.parent_window and 
                hasattr(self.parent_window, 'mask_generator')):
                
                mask_generator = self.parent_window.mask_generator
                
                if self.current_annotation_type:
                    # Drawing mode with selected annotation color
                    color = self.get_annotation_color(self.current_annotation_type)
                    mask_generator.set_drawing_tool(
                        color=color,
                        brush_size=self.brush_size
                    )
                    
        except Exception as e:
            print(f"Error updating mask generator tool: {e}")
            
    def change_button_color(self, button):
        """Change color of an annotation button"""
        color = QColorDialog.getColor(button.color, self, f"Choose color for {button.annotation_type}")
        if color.isValid():
            button.color = color
            button.update_icon()
            
            # Update mask generator if this is the current annotation type
            if self.current_annotation_type == button.annotation_type:
                self.update_mask_generator_tool()
            
    def set_brush_size(self, size):
        """Set brush size for editing"""
        self.brush_size = size
        self.update_status_text()
        
        # Update the mask generator tool
        self.update_mask_generator_tool()
        
    def update_status_text(self):
        """Update status text with current tool info"""
        if self.current_annotation_type:
            self.status_label.setText(f"Selected: {self.current_annotation_type} (brush size: {self.brush_size})")
        else:
            self.status_label.setText("Select an annotation type to start editing")
            
    def apply_brush_stroke(self, points, annotation_type=None):
        """Apply a brush stroke to the manual edits"""
        # TODO: Implement brush stroke application
        # This would modify the manual_edits array based on brush strokes
        if annotation_type is None:
            annotation_type = self.current_annotation_type
            
        # For now, just update status
        if annotation_type:
            self.status_label.setText(f"Applied brush stroke for {annotation_type}")
        else:
            self.status_label.setText("No annotation type selected")
            
        # TODO: Emit the updated edits
        # self.maskEdited.emit(self.manual_edits)
        
    def get_current_tool(self):
        """Get information about the currently selected tool"""
        return {
            'annotation_type': self.current_annotation_type,
            'brush_size': self.brush_size
        }
        
    def refresh_annotation_colors(self):
        """Refresh the colors of annotation buttons to match current label colors"""
        try:
            for button in self.annotation_buttons:
                # Get the current color from the main window's label system
                new_color = self.get_label_color_from_main_window(button.annotation_type)
                
                if new_color is not None and new_color != button.color:
                    print(f"Updating color for {button.annotation_type}: {button.color.name()} -> {new_color.name()}")
                    button.color = new_color
                    button.update_icon()
                    
            # Update mask generator tool if current annotation type changed color
            if self.current_annotation_type:
                self.update_mask_generator_tool()
                    
        except Exception as e:
            print(f"Error refreshing annotation colors: {e}")
    
    def update_annotation_types_with_order(self, annotation_types, preserve_order=True):
        """Update annotation types while optionally preserving button order"""
        if preserve_order and self.annotation_types:
            # Try to maintain existing order and just update colors
            existing_types = set(self.annotation_types)
            new_types = set(annotation_types)
            
            # If the types are the same, just refresh colors
            if existing_types == new_types:
                self.refresh_annotation_colors()
                return
        
        # Full update if types have changed or preserve_order is False
        self.update_annotation_types(annotation_types)
    
    def get_label_color_from_main_window(self, annotation_type):
        """Get the actual color for an annotation type from the main window's label system"""
        try:
            # Get the parent semantic segmentation window
            if (self.parent_window and 
                hasattr(self.parent_window, 'main_window') and 
                self.parent_window.main_window):
                
                main_window = self.parent_window.main_window
                
                # Try to get color from label window's labels
                if (hasattr(main_window, 'label_window') and 
                    hasattr(main_window.label_window, 'labels')):
                    
                    labels_list = main_window.label_window.labels
                    
                    for label in labels_list:
                        # Check both short and long label codes
                        if (hasattr(label, 'short_label_code') and 
                            label.short_label_code == annotation_type):
                            return label.color
                        elif (hasattr(label, 'long_label_code') and 
                              label.long_label_code == annotation_type):
                            return label.color
                            
            print(f"Could not find color for annotation type: {annotation_type}")
            return None
            
        except Exception as e:
            print(f"Error getting label color for {annotation_type}: {e}")
            return None
    
    def get_annotation_color(self, annotation_type):
        """Get the color for a specific annotation type"""
        for button in self.annotation_buttons:
            if button.annotation_type == annotation_type:
                return button.color
        return QColor(128, 128, 128)  # Default gray
        
    def set_manual_edits(self, edits):
        """Set the manual edits array"""
        self.manual_edits = edits
        
    def get_manual_edits(self):
        """Get the current manual edits"""
        return self.manual_edits
