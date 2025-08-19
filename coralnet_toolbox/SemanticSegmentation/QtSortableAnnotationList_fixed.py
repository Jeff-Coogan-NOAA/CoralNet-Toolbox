from PyQt5.QtWidgets import (QListWidget, QListWidgetItem, QVBoxLayout, QWidget,
                             QLabel, QFrame, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData
from PyQt5.QtGui import QDrag, QPainter, QColor

class DraggableListItem(QListWidgetItem):
    """Custom list widget item that can be dragged and reordered"""
    
    def __init__(self, text, annotation_type=None):
        super().__init__(text)
        self.annotation_type = annotation_type
        # Set the flags to enable dragging and dropping
        self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | 
                     Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)

class SortableAnnotationList(QListWidget):
    """Center panel: Draggable list of annotation types for sorting"""
    
    orderChanged = pyqtSignal(list)  # Emitted when order changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.annotation_types = []
        
        self.setup_ui()
        self.setup_drag_drop()
        
    def setup_ui(self):
        """Set up the sortable list UI"""
        self.setFrameStyle(QFrame.StyledPanel)
        self.setMinimumWidth(150)
        self.setMaximumWidth(200)
        
        # Style the list
        self.setStyleSheet("""
            QListWidget {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 8px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                border-color: #2196f3;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
                border-color: #999;
            }
        """)
        
    def setup_drag_drop(self):
        """Set up drag and drop functionality"""
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        # Set selection mode to allow dragging
        self.setSelectionMode(QListWidget.SingleSelection)
        
    def update_types(self, annotation_types):
        """Update the list with new annotation types"""
        self.annotation_types = annotation_types
        self.clear()
        
        for i, ann_type in enumerate(annotation_types):
            item = DraggableListItem(f"{i+1}. {ann_type}", ann_type)
            # Set different colors for visual distinction
            if i < 5:  # Limit colors to first 5 items
                colors = ["#ffebee", "#e8f5e8", "#e3f2fd", "#fff3e0", "#f3e5f5"]
                item.setBackground(QColor(colors[i]))
            self.addItem(item)
            
    def mousePressEvent(self, event):
        """Handle mouse press event for drag initiation"""
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            print(f"Mouse press at {self.start_pos}")
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move event for drag detection"""
        if (event.buttons() & Qt.LeftButton) and hasattr(self, 'start_pos'):
            distance = (event.pos() - self.start_pos).manhattanLength()
            if distance >= QApplication.startDragDistance():
                print(f"Drag distance threshold reached: {distance}")
        super().mouseMoveEvent(event)
            
    def dropEvent(self, event):
        """Handle drop event and emit order change signal"""
        print(f"Drop event: source={event.source()}, actions={event.possibleActions()}")
        if event.source() == self and event.possibleActions() & Qt.MoveAction:
            super().dropEvent(event)
            self.update_item_numbers()
            self.emit_order_changed()
            event.accept()
            print("Drop event accepted and processed")
        else:
            event.ignore()
            print("Drop event ignored")
    
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        print(f"Drag enter event: source={event.source()}")
        if event.source() == self:
            event.accept()
            print("Drag enter accepted")
        else:
            event.ignore()
            print("Drag enter ignored")
    
    def dragMoveEvent(self, event):
        """Handle drag move event"""
        if event.source() == self:
            event.accept()
        else:
            event.ignore()
                
    def update_item_numbers(self):
        """Update the numbering of items after reordering"""
        for i in range(self.count()):
            item = self.item(i)
            if hasattr(item, 'annotation_type'):
                item.setText(f"{i+1}. {item.annotation_type}")
        print("Item numbers updated")
                
    def emit_order_changed(self):
        """Emit signal with new order of annotation types"""
        new_order = []
        for i in range(self.count()):
            item = self.item(i)
            if hasattr(item, 'annotation_type'):
                new_order.append(item.annotation_type)
        
        print(f"New order: {new_order}")
        self.orderChanged.emit(new_order)
        
    def get_sort_order(self):
        """Get the current sort order of annotation types"""
        order = []
        for i in range(self.count()):
            item = self.item(i)
            if hasattr(item, 'annotation_type'):
                order.append(item.annotation_type)
        return order
        
    def startDrag(self, supportedActions):
        """Start drag operation with visual feedback"""
        item = self.currentItem()
        if item:
            print(f"Starting drag for item: {item.text()}")
            # Use the parent class implementation which handles internal moves
            super().startDrag(supportedActions)
            
    def add_annotation_type(self, annotation_type):
        """Add a new annotation type to the list"""
        if annotation_type not in self.annotation_types:
            self.annotation_types.append(annotation_type)
            self.update_types(self.annotation_types)
            
    def remove_annotation_type(self, annotation_type):
        """Remove an annotation type from the list"""
        if annotation_type in self.annotation_types:
            self.annotation_types.remove(annotation_type)
            self.update_types(self.annotation_types)
            
    def clear_types(self):
        """Clear all annotation types"""
        self.annotation_types = []
        self.clear()
