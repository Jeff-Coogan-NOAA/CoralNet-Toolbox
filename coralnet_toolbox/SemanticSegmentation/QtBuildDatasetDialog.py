from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTabWidget, QWidget, QGroupBox,
                             QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
                             QComboBox, QCheckBox, QTextEdit, QProgressBar,
                             QFileDialog, QMessageBox, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QIcon
from coralnet_toolbox.Icons import get_icon
import os
import shutil
import numpy as np
from PIL import Image
import csv
import random


class BuildDatasetDialog(QDialog):
    """Dialog for building datasets for semantic segmentation training"""
    
    datasetBuilt = pyqtSignal(str)  # Emitted when dataset is successfully built
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        
        self.setWindowTitle("Build Dataset - Semantic Segmentation")
        self.setWindowIcon(get_icon("coral.png"))
        self.setModal(True)
        self.resize(800, 600)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Build Dataset for Semantic Segmentation")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Description
        description_label = QLabel(
            "Configure and build a dataset for training semantic segmentation models.\n"
            "This will process your annotated images and masks to create training data."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #666; margin: 10px 0;")
        layout.addWidget(description_label)
        
        # Create tabs for different configuration sections
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Dataset Configuration Tab
        dataset_tab = QWidget()
        self.setup_dataset_tab(dataset_tab)
        tab_widget.addTab(dataset_tab, "Dataset Config")
        
        # ...removed processing options tab...
        
        # Output Settings Tab
        output_tab = QWidget()
        self.setup_output_tab(output_tab)
        tab_widget.addTab(output_tab, "Output")
        
        # Progress section
        progress_group = QGroupBox("Build Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_text = QTextEdit()
        self.progress_text.setMaximumHeight(100)
        self.progress_text.setReadOnly(True)
        self.progress_text.setVisible(False)
        progress_layout.addWidget(self.progress_text)
        
        layout.addWidget(progress_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.build_button = QPushButton("Build Dataset")
        self.build_button.setIcon(get_icon("rocket.png"))
        self.build_button.clicked.connect(self.build_dataset)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.build_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def setup_dataset_tab(self, tab):
        """Set up the dataset configuration tab"""
        layout = QVBoxLayout(tab)
        
        # Scroll area for the content
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Dataset basics group
        basics_group = QGroupBox("Dataset Basics")
        basics_layout = QFormLayout(basics_group)
        
        self.dataset_name_edit = QLineEdit()
        self.dataset_name_edit.setPlaceholderText("Enter dataset name...")
        basics_layout.addRow("Dataset Name:", self.dataset_name_edit)
        
        self.dataset_description_edit = QTextEdit()
        self.dataset_description_edit.setMaximumHeight(80)
        self.dataset_description_edit.setPlaceholderText("Optional description...")
        basics_layout.addRow("Description:", self.dataset_description_edit)
        
        scroll_layout.addWidget(basics_group)
        
        # Colormap configuration group
        colormap_group = QGroupBox("Colormap Configuration")
        colormap_layout = QFormLayout(colormap_group)
        
        # Colormap source selection
        colormap_source_layout = QHBoxLayout()
        self.build_colormap_radio = QCheckBox("Build from current project annotations")
        self.build_colormap_radio.setChecked(True)
        colormap_source_layout.addWidget(self.build_colormap_radio)
        colormap_layout.addRow(colormap_source_layout)
        
        self.open_colormap_radio = QCheckBox("Load from existing CSV file")
        colormap_layout.addRow(self.open_colormap_radio)
        
        # Make radio buttons mutually exclusive
        self.build_colormap_radio.toggled.connect(lambda checked: self.open_colormap_radio.setChecked(not checked) if checked else None)
        self.open_colormap_radio.toggled.connect(lambda checked: self.build_colormap_radio.setChecked(not checked) if checked else None)
        
        # Colormap file selection
        colormap_file_layout = QHBoxLayout()
        self.colormap_path_edit = QLineEdit()
        self.colormap_path_edit.setPlaceholderText("Select colormap CSV file...")
        self.colormap_path_edit.setEnabled(False)
        colormap_browse_button = QPushButton("Browse...")
        colormap_browse_button.setEnabled(False)
        colormap_browse_button.clicked.connect(self.browse_colormap_file)
        colormap_file_layout.addWidget(self.colormap_path_edit)
        colormap_file_layout.addWidget(colormap_browse_button)
        colormap_layout.addRow("Colormap file:", colormap_file_layout)
        
        # Enable/disable colormap file widgets based on selection
        self.open_colormap_radio.toggled.connect(self.colormap_path_edit.setEnabled)
        self.open_colormap_radio.toggled.connect(colormap_browse_button.setEnabled)
        
        # Preview/Build colormap button
        colormap_action_layout = QHBoxLayout()
        self.preview_colormap_button = QPushButton("Preview Colormap")
        self.preview_colormap_button.clicked.connect(self.preview_colormap)
        self.build_colormap_button = QPushButton("Save Colormap")
        self.build_colormap_button.clicked.connect(self.build_and_save_colormap)
        colormap_action_layout.addWidget(self.preview_colormap_button)
        colormap_action_layout.addWidget(self.build_colormap_button)
        colormap_action_layout.addStretch()
        colormap_layout.addRow(colormap_action_layout)
        
        # Colormap preview area
        self.colormap_preview = QTextEdit()
        self.colormap_preview.setMaximumHeight(100)
        self.colormap_preview.setReadOnly(True)
        self.colormap_preview.setPlaceholderText("Colormap preview will appear here...")
        colormap_layout.addRow("Preview:", self.colormap_preview)
        
        scroll_layout.addWidget(colormap_group)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
    # ...removed setup_processing_tab and related UI...
        
    def setup_output_tab(self, tab):
        """Set up the output settings tab"""
        layout = QVBoxLayout(tab)
        
        # Scroll area for the content
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Output location group
        output_group = QGroupBox("Output Location")
        output_layout = QFormLayout(output_group)
        
        output_path_layout = QHBoxLayout()
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Select output directory...")
        output_path_button = QPushButton("Browse...")
        output_path_button.clicked.connect(self.browse_output_path)
        output_path_layout.addWidget(self.output_path_edit)
        output_path_layout.addWidget(output_path_button)
        output_layout.addRow("Output directory:", output_path_layout)
        
        scroll_layout.addWidget(output_group)
        
        # Dataset split group
        split_group = QGroupBox("Dataset Split")
        split_layout = QFormLayout(split_group)
        
        self.train_split_spinbox = QDoubleSpinBox()
        self.train_split_spinbox.setRange(0.1, 0.9)
        self.train_split_spinbox.setValue(0.8)
        self.train_split_spinbox.setSingleStep(0.1)
        split_layout.addRow("Training split:", self.train_split_spinbox)
        
        self.val_split_spinbox = QDoubleSpinBox()
        self.val_split_spinbox.setRange(0.05, 0.5)
        self.val_split_spinbox.setValue(0.15)
        self.val_split_spinbox.setSingleStep(0.05)
        split_layout.addRow("Validation split:", self.val_split_spinbox)
        
        self.test_split_spinbox = QDoubleSpinBox()
        self.test_split_spinbox.setRange(0.05, 0.5)
        self.test_split_spinbox.setValue(0.05)
        self.test_split_spinbox.setSingleStep(0.05)
        split_layout.addRow("Test split:", self.test_split_spinbox)
        
        scroll_layout.addWidget(split_group)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
    def browse_output_path(self):
        """Browse for output directory"""
        path = QFileDialog.getExistingDirectory(
            self, 
            "Select Output Directory",
            os.path.expanduser("~")
        )
        if path:
            self.output_path_edit.setText(path)
            
    def browse_colormap_file(self):
        """Browse for colormap CSV file"""
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Colormap CSV File",
            os.path.expanduser("~"),
            "CSV files (*.csv);;All files (*)"
        )
        if path:
            self.colormap_path_edit.setText(path)
            # Automatically preview the loaded colormap
            self.preview_colormap()
            
    def preview_colormap(self):
        """Preview the colormap configuration"""
        self.colormap_preview.clear()
        
        if self.build_colormap_radio.isChecked():
            # Build colormap from current project annotations
            try:
                colormap_data = self.get_project_colormap()
                if colormap_data:
                    preview_text = "Colormap from project annotations:\n"
                    preview_text += "Annotation Short Name, RGB Value, Class ID\n"
                    preview_text += "-" * 50 + "\n"
                    
                    for i, (short_name, rgb_value, class_id) in enumerate(colormap_data):
                        preview_text += f"{short_name}, {rgb_value}, {class_id}\n"
                        if i >= 10:  # Limit preview to first 10 entries
                            preview_text += f"... and {len(colormap_data) - 10} more entries\n"
                            break
                    
                    self.colormap_preview.setPlainText(preview_text)
                else:
                    self.colormap_preview.setPlainText("No annotations found in current project.")
            except Exception as e:
                self.colormap_preview.setPlainText(f"Error building colormap from project: {e}")
                
        elif self.open_colormap_radio.isChecked():
            # Load colormap from CSV file
            colormap_file = self.colormap_path_edit.text().strip()
            if not colormap_file:
                self.colormap_preview.setPlainText("Please select a colormap CSV file.")
                return
                
            try:
                import csv
                colormap_data = []
                with open(colormap_file, 'r', newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    header = next(reader, None)  # Skip header if present
                    
                    for row_num, row in enumerate(reader):
                        if len(row) >= 3:
                            colormap_data.append((row[0], row[1], row[2]))
                        if row_num >= 10:  # Limit preview
                            break
                
                if colormap_data:
                    preview_text = f"Colormap from file: {os.path.basename(colormap_file)}\n"
                    preview_text += "Annotation Short Name, RGB Value, Class ID\n"
                    preview_text += "-" * 50 + "\n"
                    
                    for short_name, rgb_value, class_id in colormap_data:
                        preview_text += f"{short_name}, {rgb_value}, {class_id}\n"
                    
                    # Count total entries
                    with open(colormap_file, 'r') as f:
                        total_lines = sum(1 for line in f) - 1  # Subtract header
                    
                    if total_lines > 10:
                        preview_text += f"... and {total_lines - 10} more entries\n"
                    
                    preview_text += f"\nTotal entries: {total_lines}"
                    self.colormap_preview.setPlainText(preview_text)
                else:
                    self.colormap_preview.setPlainText("No valid colormap data found in CSV file.")
                    
            except Exception as e:
                self.colormap_preview.setPlainText(f"Error loading colormap file: {e}")
                
    def get_project_colormap(self):
        """Extract colormap data from current project annotations"""
        colormap_data = []
        
        try:
            # Get labels from main window
            if (self.main_window and 
                hasattr(self.main_window, 'label_window') and 
                hasattr(self.main_window.label_window, 'labels')):
                
                labels = self.main_window.label_window.labels
                
                for class_id, label in enumerate(labels):
                    if hasattr(label, 'short_label_code') and hasattr(label, 'color'):
                        short_name = label.short_label_code
                        # Convert color to RGB string
                        if hasattr(label.color, 'red'):
                            # QColor object
                            rgb_value = f"({label.color.red()},{label.color.green()},{label.color.blue()})"
                        else:
                            # String color
                            rgb_value = str(label.color)
                        
                        colormap_data.append((short_name, rgb_value, class_id))
                
                return colormap_data
            else:
                return None
                
        except Exception as e:
            print(f"Error extracting project colormap: {e}")
            return None
            
    def build_and_save_colormap(self):
        """Build colormap and save it to a CSV file"""
        if self.build_colormap_radio.isChecked():
            # Build from project annotations
            colormap_data = self.get_project_colormap()
            if not colormap_data:
                QMessageBox.warning(self, "No Data", "No annotation data found in current project.")
                return
                
            # Ask user where to save the colormap
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Colormap CSV",
                os.path.expanduser("~/colormap.csv"),
                "CSV files (*.csv);;All files (*)"
            )
            
            if save_path:
                try:
                    import csv
                    with open(save_path, 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        # Write header
                        writer.writerow(['annotation_short_name', 'rgb_value', 'class_id'])
                        # Write data
                        for short_name, rgb_value, class_id in colormap_data:
                            writer.writerow([short_name, rgb_value, class_id])
                    
                    QMessageBox.information(
                        self, 
                        "Colormap Saved", 
                        f"Colormap saved successfully to:\n{save_path}\n\n"
                        f"Total entries: {len(colormap_data)}"
                    )
                    
                    # Optionally switch to "open" mode and load the saved file
                    self.open_colormap_radio.setChecked(True)
                    self.colormap_path_edit.setText(save_path)
                    self.preview_colormap()
                    
                except Exception as e:
                    QMessageBox.critical(self, "Save Error", f"Failed to save colormap:\n{e}")
        else:
            QMessageBox.information(
                self, 
                "Build Colormap", 
                "Please select 'Build from current project annotations' to build a new colormap."
            )
            
    def build_dataset(self):
        """Build the dataset with current settings"""
        # Validate inputs
        if not self.dataset_name_edit.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Please enter a dataset name.")
            return
            
        if not self.output_path_edit.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Please select an output directory.")
            return
            
        # Validate colormap configuration
        if self.open_colormap_radio.isChecked() and not self.colormap_path_edit.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Please select a colormap CSV file or switch to 'Build from current project annotations'.")
            return
            
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_text.setVisible(True)
        self.build_button.setEnabled(False)
        
        try:
            # Create dataset directory structure
            self.progress_text.append("Creating dataset directory structure...")
            dataset_path = os.path.join(self.output_path_edit.text(), self.dataset_name_edit.text())
            
            # Create main directories
            directories = [
                "training/images",
                "training/masks", 
                "validation/images",
                "validation/masks",
                "test/images",
                "test/masks"
            ]
            
            for directory in directories:
                dir_path = os.path.join(dataset_path, directory)
                os.makedirs(dir_path, exist_ok=True)
                self.progress_text.append(f"Created: {directory}")
            
            # Get colormap data
            self.progress_text.append("Loading colormap...")
            colormap_data = self.get_colormap_data()
            if not colormap_data:
                QMessageBox.warning(self, "Colormap Error", "Failed to load colormap data.")
                return
                
            self.progress_text.append(f"Colormap loaded with {len(colormap_data)} classes")
            
            # Get images with masks from the project
            self.progress_text.append("Collecting images with masks...")
            image_mask_pairs = self.get_image_mask_pairs()
            if not image_mask_pairs:
                QMessageBox.warning(self, "No Data", "No images with masks found in current project.")
                return
                
            self.progress_text.append(f"Found {len(image_mask_pairs)} images with masks")
            
            # Split dataset
            self.progress_text.append("Splitting dataset...")
            train_pairs, val_pairs, test_pairs = self.split_dataset(image_mask_pairs)
            self.progress_text.append(f"Split: Train={len(train_pairs)}, Val={len(val_pairs)}, Test={len(test_pairs)}")
            
            # Process each split
            splits = [
                ("training", train_pairs),
                ("validation", val_pairs), 
                ("test", test_pairs)
            ]
            
            total_images = len(image_mask_pairs)
            processed_images = 0
            
            for split_name, pairs in splits:
                if not pairs:
                    continue
                    
                self.progress_text.append(f"Processing {split_name} split...")
                
                for image_path, mask_path in pairs:
                    try:
                        # Copy and process image
                        image_filename = os.path.basename(image_path)
                        dest_image_path = os.path.join(dataset_path, split_name, "images", image_filename)
                        
                        # Always copy image as-is (no resizing)
                        shutil.copy2(image_path, dest_image_path)
                        
                        # Process mask
                        mask_filename = os.path.splitext(image_filename)[0] + "_mask.png"
                        dest_mask_path = os.path.join(dataset_path, split_name, "masks", mask_filename)
                        
                        # Convert colored mask to 8-bit class ID mask
                        self.convert_mask_to_class_ids(mask_path, dest_mask_path, colormap_data)
                        
                        processed_images += 1
                        progress_percent = int((processed_images / total_images) * 100)
                        self.progress_bar.setValue(progress_percent)
                        
                    except Exception as e:
                        self.progress_text.append(f"Error processing {image_filename}: {e}")
                        continue
            
            # Save colormap and dataset info
            self.save_dataset_metadata(dataset_path, colormap_data)
            
            self.progress_text.append("Dataset building completed successfully!")
            self.progress_bar.setValue(100)
            
            QMessageBox.information(
                self, 
                "Dataset Built Successfully", 
                f"Dataset '{self.dataset_name_edit.text()}' has been built successfully!\n\n"
                f"Location: {dataset_path}\n"
                f"Total images processed: {processed_images}\n"
                f"Training: {len(train_pairs)} images\n"
                f"Validation: {len(val_pairs)} images\n"
                f"Test: {len(test_pairs)} images"
            )
            
        except Exception as e:
            self.progress_text.append(f"Error building dataset: {e}")
            QMessageBox.critical(self, "Build Error", f"Failed to build dataset:\n{e}")
        
        finally:
            # Re-enable button
            self.build_button.setEnabled(True)
            
        # Emit signal
        self.datasetBuilt.emit(dataset_path if 'dataset_path' in locals() else self.output_path_edit.text())
        
    def get_colormap_data(self):
        """Get colormap data either from project or CSV file"""
        if self.build_colormap_radio.isChecked():
            return self.get_project_colormap()
        else:
            return self.load_colormap_from_csv(self.colormap_path_edit.text())
            
    def load_colormap_from_csv(self, csv_path):
        """Load colormap from CSV file"""
        try:
            colormap_data = []
            with open(csv_path, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader, None)  # Skip header
                
                for row in reader:
                    if len(row) >= 3:
                        short_name = row[0]
                        rgb_value = row[1]
                        class_id = int(row[2])
                        colormap_data.append((short_name, rgb_value, class_id))
                        
            return colormap_data
        except Exception as e:
            print(f"Error loading colormap from CSV: {e}")
            return None
            
    def get_image_mask_pairs(self):
        """Get list of (image_path, mask_path) pairs from the current project"""
        image_mask_pairs = []
        
        try:
            # Get semantic segmentation data from main window
            if (self.main_window and 
                hasattr(self.main_window, 'semantic_segmentation_data') and 
                'mask_paths' in self.main_window.semantic_segmentation_data):
                
                mask_paths = self.main_window.semantic_segmentation_data['mask_paths']
                
                for image_path, mask_path in mask_paths.items():
                    if os.path.exists(image_path) and os.path.exists(mask_path):
                        image_mask_pairs.append((image_path, mask_path))
                            
        except Exception as e:
            print(f"Error getting image mask pairs: {e}")
            
        return image_mask_pairs
            
    def split_dataset(self, image_mask_pairs):
        """Split dataset into train/validation/test sets"""
        # Shuffle the pairs
        pairs = image_mask_pairs.copy()
        random.shuffle(pairs)
        
        # Calculate split indices
        total = len(pairs)
        train_split = self.train_split_spinbox.value()
        val_split = self.val_split_spinbox.value()
        
        train_idx = int(total * train_split)
        val_idx = int(total * (train_split + val_split))
        
        # Split the data
        train_pairs = pairs[:train_idx]
        val_pairs = pairs[train_idx:val_idx]
        test_pairs = pairs[val_idx:]
        
        return train_pairs, val_pairs, test_pairs
        
    def resize_and_save_image(self, src_path, dest_path, target_size):
        """Resize image and save to destination"""
        try:
            with Image.open(src_path) as img:
                # Resize maintaining aspect ratio
                img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
                
                # Create new image with target size and paste resized image
                new_img = Image.new('RGB', (target_size, target_size), (0, 0, 0))
                x = (target_size - img.width) // 2
                y = (target_size - img.height) // 2
                new_img.paste(img, (x, y))
                
                new_img.save(dest_path)
                
        except Exception as e:
            # Fallback to copy if resize fails
            shutil.copy2(src_path, dest_path)
            
    def convert_mask_to_class_ids(self, src_mask_path, dest_mask_path, colormap_data):
        """Convert RGB mask to 8-bit class ID mask using colormap"""
        try:
            # Load the colored mask
            mask = Image.open(src_mask_path)
            mask_array = np.array(mask)
            
            # Create class ID mask (same dimensions but single channel)
            if len(mask_array.shape) == 3:
                class_mask = np.zeros((mask_array.shape[0], mask_array.shape[1]), dtype=np.uint8)
            else:
                class_mask = np.zeros_like(mask_array, dtype=np.uint8)
            
            # Convert each color to class ID
            for short_name, rgb_str, class_id in colormap_data:
                try:
                    # Parse RGB string like "(255,128,0)"
                    rgb_str = rgb_str.strip('()')
                    r, g, b = map(int, rgb_str.split(','))
                    
                    # Find pixels matching this color (with some tolerance)
                    if len(mask_array.shape) == 3:
                        color_mask = np.all(np.abs(mask_array - [r, g, b]) <= 5, axis=2)
                    else:
                        # Handle grayscale masks
                        gray_value = int(0.299 * r + 0.587 * g + 0.114 * b)
                        color_mask = np.abs(mask_array - gray_value) <= 5
                    
                    class_mask[color_mask] = class_id
                    
                except Exception as e:
                    print(f"Error processing color {rgb_str} for class {short_name}: {e}")
                    continue
            
            # Save as 8-bit grayscale PNG (no resizing)
            class_mask_img = Image.fromarray(class_mask, mode='L')
            class_mask_img.save(dest_mask_path)
                
        except Exception as e:
            print(f"Error converting mask {src_mask_path}: {e}")
            # Create empty mask as fallback (default size 512x512)
            empty_mask = np.zeros((512, 512), dtype=np.uint8)
            empty_mask_img = Image.fromarray(empty_mask, mode='L')
            empty_mask_img.save(dest_mask_path)
            
    def save_dataset_metadata(self, dataset_path, colormap_data):
        """Save dataset metadata including colormap"""
        try:
            # Save colormap
            colormap_path = os.path.join(dataset_path, "colormap.csv")
            with open(colormap_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['annotation_short_name', 'rgb_value', 'class_id'])
                for short_name, rgb_value, class_id in colormap_data:
                    writer.writerow([short_name, rgb_value, class_id])
            # Save dataset info
            info_path = os.path.join(dataset_path, "dataset_info.txt")
            with open(info_path, 'w') as f:
                f.write(f"Dataset Name: {self.dataset_name_edit.text()}\n")
                f.write(f"Description: {self.dataset_description_edit.toPlainText()}\n")
                f.write(f"Created: {os.path.basename(dataset_path)}\n")
                f.write(f"Number of Classes: {len(colormap_data)}\n")
                f.write(f"Train Split: {self.train_split_spinbox.value()}\n")
                f.write(f"Validation Split: {self.val_split_spinbox.value()}\n")
                f.write(f"Test Split: {self.test_split_spinbox.value()}\n")
                # Removed image size and normalize info
        except Exception as e:
            print(f"Error saving dataset metadata: {e}")
