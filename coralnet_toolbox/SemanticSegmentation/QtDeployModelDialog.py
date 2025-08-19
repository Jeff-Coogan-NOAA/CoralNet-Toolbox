from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTabWidget, QWidget, QGroupBox,
                             QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
                             QComboBox, QCheckBox, QTextEdit, QProgressBar,
                             QFileDialog, QMessageBox, QScrollArea, QListWidget,
                             QListWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QIcon
from coralnet_toolbox.Icons import get_icon
import os


class DeployModelDialog(QDialog):
    """Dialog for deploying trained semantic segmentation models"""
    
    modelDeployed = pyqtSignal(str)  # Emitted when model is successfully deployed
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        
        self.setWindowTitle("Deploy Model - Semantic Segmentation")
        self.setWindowIcon(get_icon("coral.png"))
        self.setModal(True)
        self.resize(800, 600)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Deploy Semantic Segmentation Model")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Description
        description_label = QLabel(
            "Deploy a trained semantic segmentation model for inference.\n"
            "Select model, configure inference parameters, and apply to new images."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #666; margin: 10px 0;")
        layout.addWidget(description_label)
        
        # Create tabs for different configuration sections
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Model Selection Tab
        model_tab = QWidget()
        self.setup_model_tab(model_tab)
        tab_widget.addTab(model_tab, "Model Selection")
        
        # Inference Settings Tab
        inference_tab = QWidget()
        self.setup_inference_tab(inference_tab)
        tab_widget.addTab(inference_tab, "Inference")
        
        # Output & Post-processing Tab
        output_tab = QWidget()
        self.setup_output_tab(output_tab)
        tab_widget.addTab(output_tab, "Output")
        
        # Progress section
        progress_group = QGroupBox("Deployment Progress")
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
        
        self.deploy_button = QPushButton("Deploy Model")
        self.deploy_button.setIcon(get_icon("rocket.png"))
        self.deploy_button.clicked.connect(self.deploy_model)
        
        self.test_button = QPushButton("Test Model")
        self.test_button.setIcon(get_icon("settings.png"))
        self.test_button.clicked.connect(self.test_model)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.test_button)
        button_layout.addWidget(self.deploy_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def setup_model_tab(self, tab):
        """Set up the model selection tab"""
        layout = QVBoxLayout(tab)
        
        # Scroll area for the content
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Model file group
        model_group = QGroupBox("Model File")
        model_layout = QFormLayout(model_group)
        
        model_path_layout = QHBoxLayout()
        self.model_path_edit = QLineEdit()
        self.model_path_edit.setPlaceholderText("Select trained model file...")
        model_path_button = QPushButton("Browse...")
        model_path_button.clicked.connect(self.browse_model_path)
        model_path_layout.addWidget(self.model_path_edit)
        model_path_layout.addWidget(model_path_button)
        model_layout.addRow("Model file:", model_path_layout)
        
        scroll_layout.addWidget(model_group)
        
        # Model info group
        info_group = QGroupBox("Model Information")
        info_layout = QFormLayout(info_group)
        
        self.model_info_text = QTextEdit()
        self.model_info_text.setMaximumHeight(120)
        self.model_info_text.setReadOnly(True)
        self.model_info_text.setPlaceholderText("Model information will appear here when a model is selected...")
        info_layout.addRow("Details:", self.model_info_text)
        
        scroll_layout.addWidget(info_group)
        
        # Hardware group
        hardware_group = QGroupBox("Hardware Settings")
        hardware_layout = QFormLayout(hardware_group)
        
        self.device_combo = QComboBox()
        self.device_combo.addItems([
            "Auto (GPU if available)",
            "CPU only",
            "CUDA GPU",
            "MPS (Apple Silicon)"
        ])
        hardware_layout.addRow("Device:", self.device_combo)
        
        self.batch_size_spinbox = QSpinBox()
        self.batch_size_spinbox.setRange(1, 32)
        self.batch_size_spinbox.setValue(4)
        hardware_layout.addRow("Inference batch size:", self.batch_size_spinbox)
        
        scroll_layout.addWidget(hardware_group)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
    def setup_inference_tab(self, tab):
        """Set up the inference settings tab"""
        layout = QVBoxLayout(tab)
        
        # Scroll area for the content
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Input processing group
        input_group = QGroupBox("Input Processing")
        input_layout = QFormLayout(input_group)
        
        self.input_size_spinbox = QSpinBox()
        self.input_size_spinbox.setRange(128, 2048)
        self.input_size_spinbox.setValue(512)
        input_layout.addRow("Input image size:", self.input_size_spinbox)
        
        self.normalize_checkbox = QCheckBox("Normalize inputs")
        self.normalize_checkbox.setChecked(True)
        input_layout.addRow(self.normalize_checkbox)
        
        self.tta_checkbox = QCheckBox("Test-time augmentation")
        input_layout.addRow(self.tta_checkbox)
        
        scroll_layout.addWidget(input_group)
        
        # Prediction settings group
        pred_group = QGroupBox("Prediction Settings")
        pred_layout = QFormLayout(pred_group)
        
        self.confidence_threshold_spinbox = QDoubleSpinBox()
        self.confidence_threshold_spinbox.setRange(0.0, 1.0)
        self.confidence_threshold_spinbox.setValue(0.5)
        self.confidence_threshold_spinbox.setSingleStep(0.05)
        pred_layout.addRow("Confidence threshold:", self.confidence_threshold_spinbox)
        
        self.overlap_threshold_spinbox = QDoubleSpinBox()
        self.overlap_threshold_spinbox.setRange(0.0, 1.0)
        self.overlap_threshold_spinbox.setValue(0.3)
        self.overlap_threshold_spinbox.setSingleStep(0.05)
        pred_layout.addRow("Overlap threshold:", self.overlap_threshold_spinbox)
        
        scroll_layout.addWidget(pred_group)
        
        # Target images group
        target_group = QGroupBox("Target Images")
        target_layout = QVBoxLayout(target_group)
        
        target_selection_layout = QHBoxLayout()
        self.use_current_images_checkbox = QCheckBox("Use current project images")
        self.use_current_images_checkbox.setChecked(True)
        target_selection_layout.addWidget(self.use_current_images_checkbox)
        target_layout.addLayout(target_selection_layout)
        
        custom_images_layout = QHBoxLayout()
        custom_images_layout.addWidget(QLabel("Custom image directory:"))
        self.custom_images_path_edit = QLineEdit()
        self.custom_images_path_edit.setEnabled(False)
        custom_images_button = QPushButton("Browse...")
        custom_images_button.setEnabled(False)
        custom_images_button.clicked.connect(self.browse_custom_images)
        custom_images_layout.addWidget(self.custom_images_path_edit)
        custom_images_layout.addWidget(custom_images_button)
        target_layout.addLayout(custom_images_layout)
        
        # Connect checkbox to enable/disable custom path
        self.use_current_images_checkbox.toggled.connect(
            lambda checked: [
                self.custom_images_path_edit.setEnabled(not checked),
                custom_images_button.setEnabled(not checked)
            ]
        )
        
        scroll_layout.addWidget(target_group)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
    def setup_output_tab(self, tab):
        """Set up the output and post-processing tab"""
        layout = QVBoxLayout(tab)
        
        # Scroll area for the content
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Output settings group
        output_group = QGroupBox("Output Settings")
        output_layout = QFormLayout(output_group)
        
        output_path_layout = QHBoxLayout()
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Select output directory...")
        output_path_button = QPushButton("Browse...")
        output_path_button.clicked.connect(self.browse_output_path)
        output_path_layout.addWidget(self.output_path_edit)
        output_path_layout.addWidget(output_path_button)
        output_layout.addRow("Output directory:", output_path_layout)
        
        self.save_masks_checkbox = QCheckBox("Save prediction masks")
        self.save_masks_checkbox.setChecked(True)
        output_layout.addRow(self.save_masks_checkbox)
        
        self.save_overlays_checkbox = QCheckBox("Save overlay images")
        self.save_overlays_checkbox.setChecked(True)
        output_layout.addRow(self.save_overlays_checkbox)
        
        self.save_confidence_checkbox = QCheckBox("Save confidence maps")
        output_layout.addRow(self.save_confidence_checkbox)
        
        scroll_layout.addWidget(output_group)
        
        # Post-processing group
        postproc_group = QGroupBox("Post-processing")
        postproc_layout = QFormLayout(postproc_group)
        
        self.apply_crf_checkbox = QCheckBox("Apply CRF smoothing")
        postproc_layout.addRow(self.apply_crf_checkbox)
        
        self.min_object_size_spinbox = QSpinBox()
        self.min_object_size_spinbox.setRange(0, 10000)
        self.min_object_size_spinbox.setValue(100)
        postproc_layout.addRow("Min object size (pixels):", self.min_object_size_spinbox)
        
        self.fill_holes_checkbox = QCheckBox("Fill small holes")
        postproc_layout.addRow(self.fill_holes_checkbox)
        
        scroll_layout.addWidget(postproc_group)
        
        # Integration group
        integration_group = QGroupBox("Integration")
        integration_layout = QFormLayout(integration_group)
        
        self.add_to_project_checkbox = QCheckBox("Add predictions to current project")
        self.add_to_project_checkbox.setChecked(True)
        integration_layout.addRow(self.add_to_project_checkbox)
        
        self.replace_existing_checkbox = QCheckBox("Replace existing annotations")
        integration_layout.addRow(self.replace_existing_checkbox)
        
        scroll_layout.addWidget(integration_group)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
    def browse_model_path(self):
        """Browse for trained model file"""
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Trained Model",
            os.path.expanduser("~"),
            "Model files (*.pth *.pt *.h5 *.ckpt *.onnx);;All files (*)"
        )
        if path:
            self.model_path_edit.setText(path)
            self.load_model_info(path)
            
    def load_model_info(self, model_path):
        """Load and display model information"""
        # TODO: Implement actual model info loading
        info_text = f"Model file: {os.path.basename(model_path)}\n"
        info_text += f"Size: {os.path.getsize(model_path) / (1024*1024):.1f} MB\n"
        info_text += "Architecture: [To be determined from model file]\n"
        info_text += "Classes: [To be determined from model file]\n"
        info_text += "Training date: [To be extracted from metadata]"
        self.model_info_text.setPlainText(info_text)
        
    def browse_custom_images(self):
        """Browse for custom images directory"""
        path = QFileDialog.getExistingDirectory(
            self, 
            "Select Custom Images Directory",
            os.path.expanduser("~")
        )
        if path:
            self.custom_images_path_edit.setText(path)
            
    def browse_output_path(self):
        """Browse for output directory"""
        path = QFileDialog.getExistingDirectory(
            self, 
            "Select Output Directory",
            os.path.expanduser("~")
        )
        if path:
            self.output_path_edit.setText(path)
            
    def test_model(self):
        """Test the model on a sample image"""
        if not self.model_path_edit.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Please select a model file.")
            return
            
        # TODO: Implement model testing functionality
        QMessageBox.information(
            self, 
            "Model Testing", 
            "Model testing functionality will be implemented here.\n"
            "This will allow you to test the model on a sample image before deployment."
        )
        
    def deploy_model(self):
        """Deploy the model with current settings"""
        # Validate inputs
        if not self.model_path_edit.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Please select a model file.")
            return
            
        if not self.output_path_edit.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Please select an output directory.")
            return
            
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_text.setVisible(True)
        self.deploy_button.setEnabled(False)
        self.test_button.setEnabled(False)
        
        # TODO: Implement actual model deployment logic
        self.progress_text.append("Model deployment functionality will be implemented here...")
        self.progress_text.append(f"Model: {self.model_path_edit.text()}")
        self.progress_text.append(f"Device: {self.device_combo.currentText()}")
        self.progress_text.append(f"Output: {self.output_path_edit.text()}")
        self.progress_text.append("This is a placeholder implementation.")
        
        self.progress_bar.setValue(100)
        
        QMessageBox.information(
            self, 
            "Model Deployment", 
            "Model deployment interface is ready.\n"
            "Implementation of actual deployment logic is pending."
        )
        
        # Re-enable buttons
        self.deploy_button.setEnabled(True)
        self.test_button.setEnabled(True)
        
        # Emit signal
        self.modelDeployed.emit(self.output_path_edit.text())
