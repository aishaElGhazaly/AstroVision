from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QRadioButton, QLabel, QLineEdit, QCheckBox, QPushButton, QFileDialog, QFrame, QComboBox, QGridLayout
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from utilities import get_plate_mjd_fiber, get_specobj_id_pmf, get_specobj_details, fetch_spectrum_file
from astropy.io import fits


class SpectrogramInspector(QWidget):
    def __init__(self, parent_tab_widget):
        super().__init__()
        self.parent_tab_widget = parent_tab_widget

        layout = QHBoxLayout(self)

        # Left Section: Interactive Spectrum Plot
        left_section = QFrame()
        left_section.setStyleSheet("background-color: white; padding: 10px; border: 1px solid #5A5A5A;")
        layout.addWidget(left_section, stretch=3)
        self.init_left_section(left_section)

        # Right Section: Controls and Input Fields
        right_section = QFrame()
        right_section.setStyleSheet("background-color: #4E4E4E; padding: 10px; border: 1px solid #5A5A5A;")
        right_section.setFixedWidth(400)
        layout.addWidget(right_section, stretch=1)
        self.init_right_section(right_section)

    def init_left_section(self, parent):
        layout = QVBoxLayout(parent)

        # Interactive pyqtgraph Plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")  # Set white background
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)  # Enable gridlines
        self.plot_widget.setLabel("bottom", "Wavelength (Å)")  # Wavelength in Angstrom
        self.plot_widget.setLabel("left", "Flux (erg/cm^2/s/Å)")  # Flux with units
        self.plot_widget.setLimits(xMin=0, yMin=0)  # Enforce boundaries to prevent negative values

        # Tooltip-like hover text
        self.hover_text = pg.TextItem(anchor=(0, 1), color="blue", fill=pg.mkBrush(255, 255, 255, 150))
        self.plot_widget.addItem(self.hover_text)
        self.hover_text.setVisible(False)  # Hide initially

        self.data_points = None  # Store the data points for hover functionality

        # Mouse movement event to track hover
        self.plot_widget.scene().sigMouseMoved.connect(self.update_hover)

        layout.addWidget(self.plot_widget, stretch=5)

    def init_right_section(self, parent):
        # Create a scroll area
        scroll_area = QScrollArea(parent)
        scroll_area.setStyleSheet("background-color: #4E4E4E; border: none;")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout = QVBoxLayout(parent)
        layout.addWidget(scroll_area)

        # Create a container widget for the scrollable content
        scroll_widget = QWidget()
        scroll_area.setWidget(scroll_widget)

        # Layout for the scrollable content
        scroll_layout = QVBoxLayout(scroll_widget)

        # Spectrum Retrieval Options
        retrieval_label = QLabel("Spectrum Retrieval")
        retrieval_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        scroll_layout.addWidget(retrieval_label)

        # Spectrum Retrieval Mode Selection
        mode_layout = QHBoxLayout()
        mode_layout.setAlignment(Qt.AlignCenter)

        self.ra_dec_radio = QRadioButton("Use RA/DEC")
        self.ra_dec_radio.setStyleSheet("color: white; font-size: 14px; border: None")
        self.ra_dec_radio.setChecked(True)
        self.ra_dec_radio.toggled.connect(self.toggle_input_mode)
        mode_layout.addWidget(self.ra_dec_radio)

        self.plate_mjd_fiber_radio = QRadioButton("Use Plate-MJD-FiberID")
        self.plate_mjd_fiber_radio.setStyleSheet("color: white; font-size: 14px; border: None")
        self.plate_mjd_fiber_radio.toggled.connect(self.toggle_input_mode)
        mode_layout.addWidget(self.plate_mjd_fiber_radio)

        scroll_layout.addLayout(mode_layout)

        # RA/DEC Input Fields
        self.ra_dec_inputs = QWidget()
        ra_dec_layout = QVBoxLayout(self.ra_dec_inputs)

        self.ra_input = QLineEdit()
        self.ra_input.setStyleSheet("background-color: #3A3A3A; color: white; padding: 5px; font-size: 14px;")
        self.ra_input.setPlaceholderText("RA (degrees)")
        ra_dec_layout.addWidget(self.ra_input)

        self.dec_input = QLineEdit()
        self.dec_input.setStyleSheet("background-color: #3A3A3A; color: white; padding: 5px; font-size: 14px;")
        self.dec_input.setPlaceholderText("Dec (degrees)")
        ra_dec_layout.addWidget(self.dec_input)
        
        # Plate-MJD-FiberID Input Fields
        self.plate_mjd_fiber_inputs = QWidget()
        self.plate_mjd_fiber_inputs.setVisible(False)
        plate_mjd_fiber_layout = QVBoxLayout(self.plate_mjd_fiber_inputs)

        self.plate_input = QLineEdit()
        self.plate_input.setStyleSheet("background-color: #3A3A3A; color: white; padding: 5px; font-size: 14px;")
        self.plate_input.setPlaceholderText("Plate")
        plate_mjd_fiber_layout.addWidget(self.plate_input)

        self.mjd_input = QLineEdit()
        self.mjd_input.setStyleSheet("background-color: #3A3A3A; color: white; padding: 5px; font-size: 14px;")
        self.mjd_input.setPlaceholderText("MJD")
        plate_mjd_fiber_layout.addWidget(self.mjd_input)

        self.fiber_input = QLineEdit()
        self.fiber_input.setStyleSheet("background-color: #3A3A3A; color: white; padding: 5px; font-size: 14px;")
        self.fiber_input.setPlaceholderText("Fiber ID")
        plate_mjd_fiber_layout.addWidget(self.fiber_input)

        scroll_layout.addWidget(self.ra_dec_inputs)
        scroll_layout.addWidget(self.plate_mjd_fiber_inputs)

        # Fetch Spectrum Button
        fetch_button = QPushButton("Fetch Spectrum")
        fetch_button.setStyleSheet("background-color: #5A9; color: white; padding: 10px; font-size: 14px;")
        fetch_button.clicked.connect(self.fetch_spectrum)
        scroll_layout.addWidget(fetch_button)

        # Object Details Section
        object_details_label = QLabel("Object Details")
        object_details_label.setStyleSheet(
            """
            color: white;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
            padding: 5px;
            border-bottom: 1px solid #5A5A5A;
            """
        )
        scroll_layout.addWidget(object_details_label)

        # Create a grid layout for object details
        object_details_grid = QGridLayout()
        object_details_grid.setHorizontalSpacing(10)
        object_details_grid.setVerticalSpacing(10)

        # Define label width
        label_width = 100

        # Information fields
        fields = [
            ("SpecObj ID:", "specobj_id_value"),
            ("Class:", "class_value"),
            ("Subclass:", "subclass_value"),
            ("Redshift:", "redshift_value"),
            ("RA:", "ra_value"),
            ("DEC:", "dec_value"),
            ("MJD:", "mjd_value"),
            ("Plate:", "plate_value"),
            ("Fiber ID:", "fiber_id_value"),
        ]

        current_row = 0
        for label_text, attr_name in fields:
            label = QLabel(label_text)
            label.setStyleSheet("color: white; font-size: 14px;")
            label.setFixedWidth(label_width)

            value = QLabel("Not Retrieved")
            value.setStyleSheet(
                "color: white; font-size: 14px; padding: 5px; border: 1px solid #5A5A5A; background-color: #2E2E2E; border-radius: 4px;"
            )
            value.setWordWrap(True)

            setattr(self, attr_name, value)

            object_details_grid.addWidget(label, current_row, 0)
            object_details_grid.addWidget(value, current_row, 1)

            current_row += 1

            # Add separator conditionally after specific fields
            if label_text in ["Redshift:", "Fiber ID:"]:
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setFrameShadow(QFrame.Sunken)
                separator.setStyleSheet("background-color: #5A5A5A; height: 5px; margin: 10px 0;")
                object_details_grid.addWidget(separator, current_row, 0, 1, 2)
                current_row += 1

        # Add the object details grid to the scroll layout
        scroll_layout.addLayout(object_details_grid)

        # Save Options
        save_spectrum_label = QLabel("Save Options")
        save_spectrum_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; margin-top: 10px;")
        scroll_layout.addWidget(save_spectrum_label)

        save_image_button = QPushButton("Save as Image")
        save_image_button.setStyleSheet("background-color: #5A9; color: white; padding: 10px; font-size: 14px;")
        save_image_button.clicked.connect(self.save_as_image)
        scroll_layout.addWidget(save_image_button)

        save_data_button = QPushButton("Export Data")
        save_data_button.setStyleSheet("background-color: #5A9; color: white; padding: 10px; font-size: 14px;")
        save_data_button.clicked.connect(self.save_data)
        scroll_layout.addWidget(save_data_button)

        scroll_layout.addStretch()

    def toggle_input_mode(self):
        """Toggle between RA/DEC and Plate-MJD-FiberID modes."""
        self.ra_dec_inputs.setVisible(self.ra_dec_radio.isChecked())
        self.plate_mjd_fiber_inputs.setVisible(self.plate_mjd_fiber_radio.isChecked())

    def fetch_spectrum(self):
        """Fetch spectrum data using selected mode."""
        if self.ra_dec_radio.isChecked():
            ra = self.ra_input.text()
            dec = self.dec_input.text()
            if not ra or not dec:
                self.hover_text.setText("Error: RA and DEC are required.")
                return
            try:
                ra, dec = float(ra), float(dec)
                plate, mjd, fiber = get_plate_mjd_fiber(ra, dec)
                if plate and mjd and fiber:
                    spectrum_file = fetch_spectrum_file(plate, mjd, fiber)
                    specobj_id = get_specobj_id_pmf(plate, mjd, fiber)
                    if spectrum_file:
                        self.display_spectrum(spectrum_file)
                        self.fetch_metadata(specobj_id)
                    else:
                        self.hover_text.setText("Error: Spectrum not found.")
                else:
                    self.hover_text.setText("Error: No Plate-MJD-Fiber found.")
            except ValueError:
                self.hover_text.setText("Error: Invalid RA or DEC format.")

        elif self.plate_mjd_fiber_radio.isChecked():
            plate = self.plate_input.text()
            mjd = self.mjd_input.text()
            fiber = self.fiber_input.text()
            if not plate or not mjd or not fiber:
                self.hover_text.setText("Error: Plate, MJD, and Fiber ID are required.")
                return
            try:
                plate, mjd, fiber = int(plate), int(mjd), int(fiber)
                spectrum_file = fetch_spectrum_file(plate, mjd, fiber)
                specobj_id = get_specobj_id_pmf(plate, mjd, fiber)
                if spectrum_file:
                    self.display_spectrum(spectrum_file)
                    self.fetch_metadata(specobj_id)
                else:
                    self.hover_text.setText("Error: Spectrum not found.")
            except ValueError:
                self.hover_text.setText("Error: Invalid Plate, MJD, or Fiber ID format.")

    def display_spectrum(self, spectrum_file):
        """Display the spectrum from the FITS file."""
        try:
            with fits.open(spectrum_file) as hdul:
                data = hdul[1].data
                wavelengths = 10 ** data['loglam']  # Convert log(wavelength) to wavelength
                intensities = data['flux']
                self.plot_spectrum(wavelengths, intensities)
        except Exception as e:
            self.hover_text.setText(f"Error reading FITS file: {e}")

    def plot_spectrum(self, wavelengths, intensities):
        """Plot the spectrum on the interactive graph."""
        self.plot_widget.clear()
        self.plot_widget.setLimits(xMin=wavelengths.min(), xMax=wavelengths.max(), yMin=intensities.min(), yMax=intensities.max())  # Set graph boundaries
        self.plot_widget.plot(wavelengths, intensities, pen=pg.mkPen(color=(0, 0, 255), width=2))  # Blue line
        self.data_points = np.column_stack((wavelengths, intensities))  # Store data points

    def update_hover(self, event):
        """Update hover label with the current mouse position on the plot."""
        pos = self.plot_widget.plotItem.vb.mapSceneToView(event)
        x, y = pos.x(), pos.y()

        # Check distances to the nearest data point for hover functionality
        if self.data_points is not None:
            distances = np.sqrt((self.data_points[:, 0] - x) ** 2 + (self.data_points[:, 1] - y) ** 2)
            nearest_index = np.argmin(distances)
            if distances[nearest_index] < 5:  # Threshold for hover detection
                nearest_x, nearest_y = self.data_points[nearest_index]
                self.hover_text.setText(f"<b>Wavelength:</b> {nearest_x:.2f} Å<br><b>Flux:</b> {nearest_y:.2e} erg/cm²/s/Å")
                self.hover_text.setPos(nearest_x, nearest_y)
                self.hover_text.setVisible(True)
            else:
                self.hover_text.setVisible(False)
        else:
            self.hover_text.setVisible(False)
            
    def fetch_metadata(self, specobj_id):
        """Fetch and display metadata for the object based on SpecObjID."""
        if not specobj_id:
            self.show_metadata_error("Error: SpecObjID is required.")
            return

        try:
            metadata = get_specobj_details(specobj_id)
            if metadata:
                # Update the labels with fetched metadata
                self.specobj_id_value.setText(str(metadata["specObjID"]))
                self.class_value.setText(metadata["class"])
                self.subclass_value.setText(metadata.get("subclass", "N/A"))
                self.redshift_value.setText(f"{metadata['redshift']:.4f} ± {metadata['redshift_error']:.4f}")
                self.ra_value.setText(f"{metadata['ra']:.5f}")
                self.dec_value.setText(f"{metadata['dec']:.5f}")
                self.mjd_value.setText(str(metadata["mjd"]))
                self.plate_value.setText(str(metadata["plate"]))
                self.fiber_id_value.setText(str(metadata["fiberID"]))
            else:
                self.show_metadata_error("No metadata found for the given SpecObjID.")
        except Exception as e:
            self.show_metadata_error(f"Error fetching metadata: {e}")


    def show_metadata_error(self, message):
        """Helper function to clear metadata fields and display an error."""
        fields = [
            "specobj_id_value", "class_value", "subclass_value", "redshift_value",
            "ra_value", "dec_value", "mjd_value", "plate_value", "fiber_id_value"
        ]
        for field in fields:
            getattr(self, field).setText("Not Retrieved")
        self.metadata_display.setText(message)
                        
    def save_as_image(self):
        """Save the current spectrum as an image."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Spectrum as Image", "", "PNG Files (*.png);;JPEG Files (*.jpg)")
        if file_path:
            exporter = pg.exporters.ImageExporter(self.plot_widget.plotItem)
            exporter.export(file_path)

    def save_data(self):
        """Export spectrum data as CSV."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Spectrum Data", "", "CSV Files (*.csv)")
        if file_path:
            np.savetxt(file_path, self.data_points, delimiter=",", header="Wavelength (Å),Flux (erg/cm^2/s/Å)", comments="")
