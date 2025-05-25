
# AstroVision

![Python](https://img.shields.io/badge/python-3.13-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-Active-brightgreen)

AstroVision is a PyQt5-based desktop application for astronomical data exploration and visualization, powered by SDSS (Sloan Digital Sky Survey) data. It provides a modular, tabbed interface for searching, retrieving, visualizing, and processing astronomical images and spectra.

---

## 📖 Table of Contents
- [Features](#features)
- [Preview](#-preview)
- [Installation](#installation)
- [Usage](#usage)
- [Requirements](#requirements)
- [Modules Overview](#modules-overview)
- [Notes](#notes)
- [Contributing](#-contributing)

---

## Features

- **Search**: Query SDSS data using various filters and conditions, view results in a table, and export results.
- **Quick Look**: Fetch and display SDSS images by coordinates, with metadata and overlay options.
- **FITS Retrieval**: Download or inspect FITS files by RA/DEC, Run-Camcol-Field, or from a local directory. View metadata and inspect files.
- **Composite Creation**: Create RGB composite images from FITS files, with preprocessing, alignment, and export to image or FITS.
- **Spectrogram Inspector**: Retrieve and visualize spectra by RA/DEC or Plate-MJD-FiberID, with interactive plots and metadata.
- **Image Enhancement**: *(Coming soon)* Placeholder for future image processing tools.

---

## 📸 Preview

*Previews coming soon...*

---

## Installation

<details>
<summary><strong>Click to expand installation instructions</strong></summary>

1. **Clone the repository** and navigate to the project directory.
2. **Create a virtual environment** (optional but recommended):

    ```bash
    python -m venv AV-env
    ```

3. **Activate the environment**:
   - On Windows:
     ```bash
     AV-env\Scripts\activate
     ```

4. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

</details>

---

## Usage

To run the application:

```bash
python AV.py
```

The main window will open with navigation cards for each module.

---

## Requirements

- Python 3.11+ (recommended)
- See `requirements.txt` for all dependencies

**Notable packages:**
- PyQt5
- Astropy
- NumPy
- Matplotlib
- Reproject
- PyQtGraph
- Pillow

---

## Modules Overview

- `AV.py`: Main application entry point and window/tab management
- `search.py`: SDSS data search with advanced filtering and result export
- `quick_look.py`: Quick image fetch and display with metadata and overlays
- `fits_retrieval.py`: Download, inspect, and view FITS files and their metadata
- `composite_creation.py`: Build and export RGB composites from FITS images
- `spectrogram_inspector.py`: Fetch, plot, and export astronomical spectra
- `image_enhancement.py`: Placeholder for future enhancements
- `utilities.py`: Helper functions for data fetching, validation, and processing

---

## Notes

- The application uses a dark theme and custom-styled widgets for a modern look.
- The "Image Enhancement" module is currently a placeholder.
- The app icon is `icon.png`.

---

## 🤝 Contributing

I believe AstroVision can grow into a community-driven tool for astronomical exploration.  
If you're passionate about space, data or UI development, feel free to open an issue, suggest a feature, or contribute a module.

---

*Last updated: April 17, 2025*
