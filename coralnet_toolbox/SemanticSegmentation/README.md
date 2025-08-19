# Semantic Segmentation Module

This module provides a comprehensive semantic segmentation interface for the CoralNet Toolbox.

## Overview

The Semantic Segmentation window consists of four main panels:

1. **Left Panel - Annotation Image Viewer**: Displays the current image with polygon annotations overlaid
2. **Center Panel - Sortable Annotation List**: Draggable list of annotation types that determines mask generation order
3. **Center-Right Panel - Mask Generator**: Generates and displays segmentation masks based on the sorted annotation types
4. **Right Panel - Image Selector**: Image browser similar to the main window for selecting images
5. **Bottom Panel - Annotation Editor**: Manual editing tools for refining masks with brush/eraser tools

## Features

### Annotation Image Viewer (`QtAnnotationImageViewer.py`)
- Displays images with polygon annotations overlaid
- TODO: Connect to main window's annotation system
- TODO: Load actual polygon data from project JSON

### Sortable Annotation List (`QtSortableAnnotationList.py`)
- Drag-and-drop reordering of annotation types
- Visual numbering to show priority order
- Emits signals when order changes to trigger mask regeneration

### Mask Generator (`QtMaskGenerator.py`)
- Generates segmentation masks based on annotation type priority
- First annotation type gets pixel value 1, second gets value 2, etc.
- Supports mask export (PNG, TIFF, NumPy)
- TODO: Implement actual polygon filling from annotation data
- TODO: Apply manual edits from annotation editor

### Image Selector (`QtImageSelector.py`)
- Browse and select images with thumbnail display
- Navigation controls (Previous/Next)
- TODO: Connect to main window's raster manager
- TODO: Sync with main window image selection

### Annotation Editor (`QtAnnotationEditor.py`)
- Manual editing tools with brush and eraser
- Adjustable brush size
- Color-coded annotation type buttons
- TODO: Implement actual brush stroke application to mask
- TODO: Save manual edits to project data

## TODOs for Integration

The following areas need connection to the main project system:

### Data Integration
1. **Project JSON Connection**: Connect to main window's project data structure
2. **Annotation Loading**: Load actual polygon annotations from the annotation system
3. **Image Synchronization**: Sync with main window's image management
4. **Label System**: Connect to the label/annotation type system

### Functionality Implementation
1. **Polygon Filling**: Implement actual polygon-to-mask conversion
2. **Manual Editing**: Implement brush stroke application to masks
3. **Data Persistence**: Save manual edits and mask data
4. **Export Integration**: Connect mask export to project workflow

### UI Enhancements
1. **Color Management**: Sync annotation colors with main window
2. **Tool Integration**: Connect with main window's annotation tools
3. **Progress Indicators**: Add progress bars for mask generation
4. **Error Handling**: Improve error handling and user feedback

## Usage

1. Open the Semantic Segmentation window from the main menu: `Semantic Segmentation > Open`
2. Select an image from the right panel image selector
3. Arrange annotation types in the center sortable list in desired priority order
4. Click "Generate" in the mask panel to create the segmentation mask
5. Use the bottom annotation editor to manually refine the mask
6. Export the final mask using the "Export" button

## File Structure

```
SemanticSegmentation/
├── __init__.py                          # Module exports
├── QtSemanticSegmentationWindow.py      # Main window class
├── QtAnnotationImageViewer.py           # Left panel - image with annotations
├── QtSortableAnnotationList.py          # Center panel - draggable annotation types
├── QtMaskGenerator.py                   # Center-right panel - mask generation
├── QtImageSelector.py                   # Right panel - image browser
├── QtAnnotationEditor.py                # Bottom panel - manual editing tools
└── README.md                           # This documentation
```

## Dependencies

- PyQt5 (GUI framework)
- NumPy (array operations for masks)
- Standard Python libraries (os, etc.)

## Notes

This is a comprehensive framework ready for integration with the main CoralNet Toolbox project data. The TODOs marked throughout the code indicate where connections to the existing project systems need to be established.
