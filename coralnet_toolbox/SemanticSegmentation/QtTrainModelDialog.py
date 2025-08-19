from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTabWidget, QWidget, QGroupBox,
                             QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
                             QComboBox, QCheckBox, QTextEdit, QProgressBar,
                             QFileDialog, QMessageBox, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QIcon
from coralnet_toolbox.Icons import get_icon
import os


class TrainModelDialog(QDialog):
    """Dialog for training semantic segmentation models"""
    
    modelTrained = pyqtSignal(str)  # Emitted when model is successfully trained
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        
        self.setWindowTitle("Train Model - Semantic Segmentation")
        self.setWindowIcon(get_icon("coral.png"))
        self.setModal(True)
        self.resize(600, 750)
        
        # Set window settings to match QtDetect
        self.setWindowFlags(Qt.Window |
                            Qt.WindowCloseButtonHint |
                            Qt.WindowMinimizeButtonHint |
                            Qt.WindowMaximizeButtonHint |
                            Qt.WindowTitleHint)
        
        # For holding parameters
        self.params = {}
        self.custom_params = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface"""
        # Create the main layout
        self.layout = QVBoxLayout(self)
        
        # Create the info layout
        self.setup_info_layout()
        # Create the dataset layout
        self.setup_dataset_layout()
        # Create the model layout
        self.setup_model_layout()
        # Create the output layout
        self.setup_output_layout()
        # Create the parameters layout
        self.setup_parameters_layout()
        # Create the buttons layout
        self.setup_buttons_layout()
        
    def setup_info_layout(self):
        """Set up the layout and widgets for the info layout"""
        group_box = QGroupBox("Information")
        layout = QVBoxLayout()

        # Create a QLabel with explanatory text
        info_label = QLabel("Configure and train a semantic segmentation model using your prepared dataset.\n"
                           "Select model architecture, hyperparameters, and training settings.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        group_box.setLayout(layout)
        self.layout.addWidget(group_box)
        
    def setup_dataset_layout(self):
        """Setup the dataset layout"""
        group_box = QGroupBox("Dataset")
        layout = QFormLayout()

        # Dataset Directory
        self.dataset_edit = QLineEdit()
        self.dataset_button = QPushButton("Browse...")
        self.dataset_button.clicked.connect(self.browse_dataset_dir)

        dataset_layout = QHBoxLayout()
        dataset_layout.addWidget(self.dataset_edit)
        dataset_layout.addWidget(self.dataset_button)
        layout.addRow("Dataset Directory:", dataset_layout)

        group_box.setLayout(layout)
        self.layout.addWidget(group_box)
        
    def setup_model_layout(self):
        """Set up the layout and widgets for the model selection with a tabbed interface"""
        group_box = QGroupBox("Model Selection")
        layout = QVBoxLayout()

        # Create tabbed widget
        tab_widget = QTabWidget()

        # Tab 1: Select model from dropdown
        model_select_tab = QWidget()
        model_select_layout = QFormLayout(model_select_tab)

        # Model combo box
        self.model_combo = QComboBox()
        self.load_model_combobox()
        model_select_layout.addRow("Model:", self.model_combo)

        tab_widget.addTab(model_select_tab, "Select Model")

        # Tab 2: Use existing model
        model_existing_tab = QWidget()
        model_existing_layout = QFormLayout(model_existing_tab)

        # Existing Model
        self.model_edit = QLineEdit()
        self.model_button = QPushButton("Browse...")
        self.model_button.clicked.connect(self.browse_model_file)
        model_layout = QHBoxLayout()
        model_layout.addWidget(self.model_edit)
        model_layout.addWidget(self.model_button)
        model_existing_layout.addRow("Existing Model:", model_layout)

        tab_widget.addTab(model_existing_tab, "Use Existing Model")

        layout.addWidget(tab_widget)
        group_box.setLayout(layout)
        self.layout.addWidget(group_box)
        
    def setup_output_layout(self):
        """Set up the layout and widgets for the output directory"""
        group_box = QGroupBox("Output Parameters")
        form_layout = QFormLayout()

        # Project
        self.project_edit = QLineEdit()
        self.project_button = QPushButton("Browse...")
        self.project_button.clicked.connect(self.browse_project_dir)
        project_layout = QHBoxLayout()
        project_layout.addWidget(self.project_edit)
        project_layout.addWidget(self.project_button)
        form_layout.addRow("Project:", project_layout)

        # Name
        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)

        group_box.setLayout(form_layout)
        self.layout.addWidget(group_box)
        
    def setup_parameters_layout(self):
        """Set up the layout and widgets for the training parameters"""
        # Create helper function for boolean dropdowns
        def create_bool_combo():
            combo = QComboBox()
            combo.addItems(["True", "False"])
            return combo

        # Create parameters group box
        group_box = QGroupBox("Training Parameters")
        group_layout = QVBoxLayout(group_box)

        # Add import/export buttons at the top
        import_export_layout = QHBoxLayout()
        
        self.import_button = QPushButton("Import YAML")
        self.import_button.clicked.connect(self.import_parameters)
        import_export_layout.addWidget(self.import_button)

        self.export_button = QPushButton("Export YAML")
        self.export_button.clicked.connect(self.export_parameters)
        import_export_layout.addWidget(self.export_button)
        
        # Add stretch to push buttons to the left
        import_export_layout.addStretch()
        
        group_layout.addLayout(import_export_layout)

        # Create a widget to hold the form layout
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)

        # Create the scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(form_widget)
        
        group_layout.addWidget(scroll_area)

        # Create parameters
        # Epochs
        self.epochs_spinbox = QSpinBox()
        self.epochs_spinbox.setMinimum(1)
        self.epochs_spinbox.setMaximum(1000)
        self.epochs_spinbox.setValue(100)
        form_layout.addRow("Epochs:", self.epochs_spinbox)

        # Patience
        self.patience_spinbox = QSpinBox()
        self.patience_spinbox.setMinimum(1)
        self.patience_spinbox.setMaximum(1000)
        self.patience_spinbox.setValue(30)
        form_layout.addRow("Patience:", self.patience_spinbox)

        # Learning Rate
        self.learning_rate_spinbox = QDoubleSpinBox()
        self.learning_rate_spinbox.setMinimum(0.0001)
        self.learning_rate_spinbox.setMaximum(1.0)
        self.learning_rate_spinbox.setValue(0.001)
        self.learning_rate_spinbox.setDecimals(4)
        self.learning_rate_spinbox.setSingleStep(0.0001)
        form_layout.addRow("Learning Rate:", self.learning_rate_spinbox)

        # Batch Size
        self.batch_spinbox = QSpinBox()
        self.batch_spinbox.setMinimum(1)
        self.batch_spinbox.setMaximum(1024)
        self.batch_spinbox.setValue(8)
        form_layout.addRow("Batch Size:", self.batch_spinbox)

        # Workers
        self.workers_spinbox = QSpinBox()
        self.workers_spinbox.setMinimum(1)
        self.workers_spinbox.setMaximum(64)
        self.workers_spinbox.setValue(8)
        form_layout.addRow("Workers:", self.workers_spinbox)

        # Optimizer
        self.optimizer_combo = QComboBox()
        self.optimizer_combo.addItems(["auto", "SGD", "Adam", "AdamW", "NAdam", "RAdam", "RMSProp"])
        self.optimizer_combo.setCurrentText("Adam")
        form_layout.addRow("Optimizer:", self.optimizer_combo)

        # Loss Function
        self.loss_function_combo = QComboBox()
        self.loss_function_combo.addItems([
            "CrossEntropy",
            "Dice Loss",
            "Focal Loss",
            "IoU Loss",
            "Combined"
        ])
        form_layout.addRow("Loss Function:", self.loss_function_combo)

        # Validation
        self.val_combo = create_bool_combo()
        form_layout.addRow("Validation:", self.val_combo)

        # Verbose
        self.verbose_combo = create_bool_combo()
        form_layout.addRow("Verbose:", self.verbose_combo)

        # Add horizontal separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        form_layout.addRow("", separator)
        
        # Add parameter button at the top of custom parameters section
        self.add_param_button = QPushButton("Add Parameter")
        self.add_param_button.clicked.connect(self.add_parameter_pair)
        form_layout.addRow("", self.add_param_button)

        # Add custom parameters section
        self.custom_params_layout = QVBoxLayout()
        form_layout.addRow("", self.custom_params_layout)

        # Remove parameter button at the bottom
        self.remove_param_button = QPushButton("Remove Parameter")
        self.remove_param_button.clicked.connect(self.remove_parameter_pair)
        self.remove_param_button.setEnabled(False)  # Disabled until at least one parameter is added
        form_layout.addRow("", self.remove_param_button)

        self.layout.addWidget(group_box)
        
    def setup_buttons_layout(self):
        """Set up the buttons layout"""
        # Add OK and Cancel buttons
        self.buttons = QPushButton("Start Training")
        self.buttons.clicked.connect(self.start_training)
        self.layout.addWidget(self.buttons)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.layout.addWidget(self.cancel_button)
        
    def load_model_combobox(self):
        """Load the model combobox with the available models"""
        self.model_combo.clear()
        self.model_combo.setEditable(True)

        standard_models = [
            'mit-b0',
            'mit-b1',
            'mit-b2',
            'mit-b3',
            'mit-b4',
            'mit-b5',
            'segformer-b1-finetuned-ade-512-512',
        ]

        self.model_combo.addItems(standard_models)
        # Set the default model
        self.model_combo.setCurrentIndex(0)
        
    def add_parameter_pair(self):
        """Add a new parameter input group with name, value, and type selector"""
        param_layout = QHBoxLayout()

        # Parameter name field
        param_name = QLineEdit()
        param_name.setPlaceholderText("Parameter name")

        # Parameter value field
        param_value = QLineEdit()
        param_value.setPlaceholderText("Value")

        # Parameter type selector
        param_type = QComboBox()
        param_type.addItems(["string", "int", "float", "bool"])

        # Add widgets to layout
        param_layout.addWidget(param_name)
        param_layout.addWidget(param_value)
        param_layout.addWidget(param_type)

        # Store the widgets for later retrieval
        self.custom_params.append((param_name, param_value, param_type))
        self.custom_params_layout.addLayout(param_layout)

        # Enable the remove button since we now have at least one parameter
        self.remove_param_button.setEnabled(True)

    def remove_parameter_pair(self):
        """Remove the most recently added parameter pair"""
        if not self.custom_params:
            return

        # Get the last parameter group
        param_name, param_value, param_type = self.custom_params.pop()

        # Remove the layout containing these widgets
        layout_to_remove = self.custom_params_layout.itemAt(self.custom_params_layout.count() - 1)

        if layout_to_remove:
            # Remove and delete widgets from the layout
            while layout_to_remove.count():
                widget = layout_to_remove.takeAt(0).widget()
                if widget:
                    widget.deleteLater()

            # Remove the layout itself
            self.custom_params_layout.removeItem(layout_to_remove)

        # Disable the remove button if no more parameters
        if not self.custom_params:
            self.remove_param_button.setEnabled(False)
            
    def browse_dataset_dir(self):
        """Browse and select a dataset directory"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Dataset Directory")
        if dir_path:
            self.dataset_edit.setText(dir_path)
            
    def browse_model_file(self):
        """Browse for existing model file"""
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Model File",
            "",
            "Model files (*.pth *.pt *.h5 *.ckpt);;All files (*)"
        )
        if path:
            self.model_edit.setText(path)
            
    def browse_project_dir(self):
        """Browse for project directory"""
        path = QFileDialog.getExistingDirectory(
            self, 
            "Select Project Directory",
            ""
        )
        if path:
            self.project_edit.setText(path)
            
    def import_parameters(self):
        """Import parameters from YAML file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Parameters",
            "",
            "YAML files (*.yaml *.yml);;All files (*)"
        )
        if file_path:
            # TODO: Implement YAML parameter import
            QMessageBox.information(self, "Import Parameters", f"Import from {file_path} - Feature to be implemented")
            
    def export_parameters(self):
        """Export parameters to YAML file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Parameters",
            "",
            "YAML files (*.yaml *.yml);;All files (*)"
        )
        if file_path:
            # TODO: Implement YAML parameter export
            QMessageBox.information(self, "Export Parameters", f"Export to {file_path} - Feature to be implemented")
            
    def start_training(self):
        """Start model training with current settings"""
        # Validate inputs
        if not self.dataset_edit.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Please select a dataset directory.")
            return
            
        if not self.project_edit.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Please select a project directory.")
            return
            
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Please enter a project name.")
            return
            
        # segformer model selection
        model_name = self.model_combo.currentText()
        if model_name == "segformer-b1-finetuned-ade-512-512":
            model_name = "segformer-b1"
        # add model use here