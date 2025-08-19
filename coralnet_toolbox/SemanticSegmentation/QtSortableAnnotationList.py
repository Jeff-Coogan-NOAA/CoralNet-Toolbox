from PyQt5.QtWidgets import (QListWidget, QListWidgetItem, QVBoxLayout, QWidget,
                             QLabel, QFrame, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData
from PyQt5.QtGui import QDrag, QPainter, QColor, QPen

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
        self.drag_start_position = None
        
        self.setup_ui()
        self.setup_drag_drop()
        
    def setup_ui(self):
        """Set up the sortable list UI"""
        self.setFrameStyle(QFrame.StyledPanel)
        self.setMinimumWidth(150)
        self.setMaximumWidth(200)
        
        # Style the list with extra padding at top to help with drag-and-drop
        self.setStyleSheet("""
            QListWidget {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 20px 5px 5px 5px;  /* Extra padding at top for easier drag-to-top */
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
        # Use simpler, more reliable drag-drop settings
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        # Set selection mode to allow dragging
        self.setSelectionMode(QListWidget.SingleSelection)
        
        # Make the viewport margins larger to create better drop zones
        self.setViewportMargins(0, 15, 0, 15)  # Top and bottom margins for easier dropping
        
        # Connect to the built-in signal for item moves
        self.model().rowsMoved.connect(self.on_rows_moved)
        
        # Track drag state for visual feedback
        self.drag_in_progress = False
    
    def paintEvent(self, event):
        """Override paint event to draw drop zone indicator"""
        super().paintEvent(event)
        
        # Draw a subtle drop zone indicator at the top when dragging
        if self.drag_in_progress:
            painter = QPainter(self.viewport())
            pen = QPen(QColor(33, 150, 243, 100))  # Light blue, semi-transparent
            pen.setWidth(2)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            
            # Draw a dashed line in the top margin area
            painter.drawLine(5, 10, self.width() - 10, 10)
            painter.drawText(10, 25, "Drop here for top position")
            painter.end()
    
    def dragEnterEvent(self, event):
        """Track when drag starts"""
        self.drag_in_progress = True
        self.update()  # Trigger repaint
        super().dragEnterEvent(event)
    
    def dragLeaveEvent(self, event):
        """Track when drag ends"""
        self.drag_in_progress = False
        self.update()  # Trigger repaint
        super().dragLeaveEvent(event)
        
    def update_types(self, annotation_types):
        """Update the list with new annotation types"""
        print(f"SortableAnnotationList.update_types called with: {annotation_types}")
        self.annotation_types = annotation_types[:]  # Make a copy
        self.clear()
        
        for i, ann_type in enumerate(annotation_types):
            item = DraggableListItem(f"{i+1}. {ann_type}", ann_type)
            # Set different colors for visual distinction
            if i < 5:  # Limit colors to first 5 items
                colors = ["#ffebee", "#e8f5e8", "#e3f2fd", "#fff3e0", "#f3e5f5"]
                item.setBackground(QColor(colors[i]))
            self.addItem(item)
        print(f"SortableAnnotationList: Added {self.count()} items to list, now has {self.count()} total items")
    
    def on_rows_moved(self, parent, start, end, destination, row):
        """Handle when rows are moved (drag-drop completed)"""
        print(f"Rows moved: start={start}, end={end}, destination={destination}, row={row}")
        # Verify we still have all items
        current_count = self.count()
        expected_count = len(self.annotation_types)
        if current_count != expected_count:
            print(f"WARNING: Item count mismatch! Current: {current_count}, Expected: {expected_count}")
            # Restore from backup
            self.restore_from_backup()
            return
        
        # Update item numbers and emit signal after move
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(10, self.update_after_move)
    
    def restore_from_backup(self):
        """Restore the list from the annotation_types backup"""
        print("Restoring list from backup...")
        self.update_types(self.annotation_types)
    
    def update_after_move(self):
        """Update item numbers and emit signal after a successful move"""
        print("Updating after move...")
        self.update_item_numbers()
        self.emit_order_changed()
    
    def dropEvent(self, event):
        """Override drop event to add safety checks and improve top-drop handling"""
        # Reset drag state
        self.drag_in_progress = False
        self.update()  # Trigger repaint to remove drop indicator
        
        if event.source() != self:
            event.ignore()
            return
        
        # Store current state in case we need to restore
        original_count = self.count()
        print(f"Drop event: original count = {original_count}")
        
        # Check if we're dropping in the top margin area (first 20 pixels)
        drop_pos = event.pos()
        if drop_pos.y() <= 20 and self.count() > 0:
            # Force drop at position 0 (top of list)
            print("Forcing drop to top of list due to top margin drop")
            source_item = self.currentItem()
            if source_item:
                # Get the annotation type before removing
                annotation_type = getattr(source_item, 'annotation_type', None)
                if annotation_type:
                    # Remove the item from its current position
                    current_row = self.row(source_item)
                    self.takeItem(current_row)
                    
                    # Insert at position 0
                    new_item = DraggableListItem(f"1. {annotation_type}", annotation_type)
                    self.insertItem(0, new_item)
                    
                    # Update all item numbers
                    self.update_item_numbers()
                    self.emit_order_changed()
                    event.accept()
                    return
        
        # Let the parent handle the drop normally
        super().dropEvent(event)
        
        # Check if we lost any items
        new_count = self.count()
        print(f"After drop: new count = {new_count}")
        
        if new_count != original_count:
            print(f"ERROR: Items lost during drop! {original_count} -> {new_count}")
            event.ignore()
            self.restore_from_backup()
        else:
            event.accept()
            
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
            if item and hasattr(item, 'annotation_type') and item.annotation_type:
                new_order.append(item.annotation_type)
        
        print(f"New order: {new_order}")
        print(f"Order length: {len(new_order)}, Expected: {len(self.annotation_types)}")
        
        # Verify we have all the expected items
        if len(new_order) == len(self.annotation_types):
            # Update our internal list to match the new order
            self.annotation_types = new_order[:]
            self.orderChanged.emit(new_order)
        else:
            print("WARNING: Order mismatch detected, not emitting signal")
            self.restore_from_backup()
        
    def get_sort_order(self):
        """Get the current sort order of annotation types"""
        order = []
        for i in range(self.count()):
            item = self.item(i)
            if hasattr(item, 'annotation_type'):
                order.append(item.annotation_type)
        print(f"SortableAnnotationList.get_sort_order: {order} (from {self.count()} items)")
        return order
        
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
