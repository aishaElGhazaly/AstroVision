from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QRadioButton, QLabel, QLineEdit, QCheckBox, QPushButton, QProgressBar,
    QTextEdit, QFileDialog, QFrame, QListWidget, QListWidgetItem, QComboBox, QScrollArea, QGridLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from astropy.io import fits
import os

from utilities import validate_ra_dec, query_run_camcol_field, get_fits_urls, download_fits_files

class FITSDownloadThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()

    def __init__(self, run_camcol_field, bands):
        super().__init__()
        self.run_camcol_field = run_camcol_field
        self.bands = bands

    def run(self):
        download_fits_files(self.run_camcol_field, self.bands, self.progress_signal.emit)
        self.finished_signal.emit()


class FITSRetrieval(QWidget):
    def __init__(self, parent_tab_widget):
        super().__init__()
        self.parent_tab_widget = parent_tab_widget
        self.hdul_data = None
        self.current_file_path = None  # Store the path of the current FITS file
        self.last_directory = os.getcwd()  # Default to the program's current working directory

        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("FITS File Retrieval")
        title_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Notification Area
        self.notification_label = QLabel("")
        self.notification_label.setStyleSheet("color: #5A9; font-size: 14px; padding: 5px;")
        self.notification_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.notification_label)

        # Mode Selection
        mode_layout = QHBoxLayout()
        mode_layout.setAlignment(Qt.AlignCenter)

        self.ra_dec_radio = QRadioButton("Use RA/DEC")
        self.ra_dec_radio.setStyleSheet("color: white; font-size: 14px;")
        self.ra_dec_radio.setChecked(True)
        self.ra_dec_radio.toggled.connect(self.toggle_input_mode)
        mode_layout.addWidget(self.ra_dec_radio)

        self.run_camcol_field_radio = QRadioButton("Use Run-Camcol-Field")
        self.run_camcol_field_radio.setStyleSheet("color: white; font-size: 14px;")
        self.run_camcol_field_radio.toggled.connect(self.toggle_input_mode)
        mode_layout.addWidget(self.run_camcol_field_radio)

        self.directory_radio = QRadioButton("Retrieve FITS from Directory")
        self.directory_radio.setStyleSheet("color: white; font-size: 14px;")
        self.directory_radio.toggled.connect(self.toggle_input_mode)
        mode_layout.addWidget(self.directory_radio)

        layout.addLayout(mode_layout)

        # Input Section
        self.input_layout = QVBoxLayout()

        # RA/DEC Inputs
        self.ra_dec_inputs = QWidget()
        ra_dec_layout = QHBoxLayout(self.ra_dec_inputs)
        ra_dec_layout.setAlignment(Qt.AlignCenter)

        ra_label = QLabel("RA:")
        ra_label.setStyleSheet("color: white; font-size: 14px;")
        ra_label.setFixedWidth(30)

        self.ra_entry = QLineEdit()
        self.ra_entry.setPlaceholderText("Enter RA (0 to 360)")
        self.ra_entry.setStyleSheet("color: white; background-color: #3A3A3A; padding: 10px; font-size: 14px;")
        self.ra_entry.setFixedWidth(175)

        dec_label = QLabel("DEC:")
        dec_label.setStyleSheet("color: white; font-size: 14px;")
        dec_label.setFixedWidth(40)

        self.dec_entry = QLineEdit()
        self.dec_entry.setPlaceholderText("Enter DEC (-90 to 90)")
        self.dec_entry.setStyleSheet("color: white; background-color: #3A3A3A; padding: 10px; font-size: 14px;")
        self.dec_entry.setFixedWidth(175)

        ra_dec_layout.addWidget(ra_label)
        ra_dec_layout.addWidget(self.ra_entry)
        ra_dec_layout.addSpacing(10)
        ra_dec_layout.addWidget(dec_label)
        ra_dec_layout.addWidget(self.dec_entry)

        self.input_layout.addWidget(self.ra_dec_inputs)

        # Run-Camcol-Field Inputs
        self.run_camcol_field_inputs = QWidget()
        self.run_camcol_field_inputs.setVisible(False)
        run_camcol_field_layout = QHBoxLayout(self.run_camcol_field_inputs)
        run_camcol_field_layout.setAlignment(Qt.AlignCenter)

        run_label = QLabel("Run:")
        run_label.setStyleSheet("color: white; font-size: 14px;")
        run_label.setFixedWidth(40)
        self.run_entry = QLineEdit()
        self.run_entry.setPlaceholderText("Run")
        self.run_entry.setStyleSheet("color: white; background-color: #3A3A3A; padding: 10px; font-size: 14px;")
        self.run_entry.setFixedWidth(125)

        camcol_label = QLabel("Camcol:")
        camcol_label.setStyleSheet("color: white; font-size: 14px;")
        camcol_label.setFixedWidth(60)
        self.camcol_entry = QLineEdit()
        self.camcol_entry.setPlaceholderText("Camcol")
        self.camcol_entry.setStyleSheet("color: white; background-color: #3A3A3A; padding: 10px; font-size: 14px;")
        self.camcol_entry.setFixedWidth(125)

        field_label = QLabel("Field:")
        field_label.setStyleSheet("color: white; font-size: 14px;")
        field_label.setFixedWidth(40)
        self.field_entry = QLineEdit()
        self.field_entry.setPlaceholderText("Field")
        self.field_entry.setStyleSheet("color: white; background-color: #3A3A3A; padding: 10px; font-size: 14px;")
        self.field_entry.setFixedWidth(125)

        run_camcol_field_layout.addWidget(run_label)
        run_camcol_field_layout.addWidget(self.run_entry)
        run_camcol_field_layout.addSpacing(10)
        run_camcol_field_layout.addWidget(camcol_label)
        run_camcol_field_layout.addWidget(self.camcol_entry)
        run_camcol_field_layout.addSpacing(10)
        run_camcol_field_layout.addWidget(field_label)
        run_camcol_field_layout.addWidget(self.field_entry)

        self.input_layout.addWidget(self.run_camcol_field_inputs)
        layout.addLayout(self.input_layout)

        # Directory Selection Button (for Directory mode)
        self.directory_button = QPushButton("Select Directory")
        self.directory_button.setStyleSheet("background-color: #5A9; color: white; font-weight: bold; padding: 10px;")
        self.directory_button.setVisible(False)
        self.directory_button.clicked.connect(self.select_directory)
        layout.addWidget(self.directory_button)

        # Band Selection and Fetch Button (RA/DEC and Run-Camcol-Field only)
        self.band_fetch_layout = QVBoxLayout()

        band_line_layout = QHBoxLayout()
        band_line_layout.setAlignment(Qt.AlignCenter)

        self.band_label = QLabel("Select Bands:")
        self.band_label.setStyleSheet("color: white; font-size: 14px;")
        band_line_layout.addWidget(self.band_label)

        self.bands_checkboxes = {}
        for band in ["u", "g", "r", "i", "z"]:
            checkbox = QCheckBox(band)
            checkbox.setStyleSheet("color: white; font-size: 14px; margin: 5px;")
            checkbox.setChecked(True)
            self.bands_checkboxes[band] = checkbox
            band_line_layout.addWidget(checkbox)

        self.band_fetch_layout.addLayout(band_line_layout)

        fetch_button_layout = QHBoxLayout()
        fetch_button_layout.setAlignment(Qt.AlignCenter)

        self.fetch_button = QPushButton("Fetch FITS")
        self.fetch_button.setStyleSheet("background-color: #5A9; color: white; font-weight: bold; padding: 10px;")
        self.fetch_button.setFixedWidth(175)
        self.fetch_button.clicked.connect(self.start_fits_download)
        fetch_button_layout.addWidget(self.fetch_button)

        self.band_fetch_layout.addLayout(fetch_button_layout)
        layout.addLayout(self.band_fetch_layout)

        # Progress Bar (not visible in Directory mode)
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #3A3A3A;
                border: none;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #5A9;
            }
        """)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # FITS List (common to all modes in the correct position)
        self.fits_list = QListWidget()
        self.fits_list.setStyleSheet("color: white; background-color: #3A3A3A; font-size: 14px; padding: 10px;")
        self.fits_list.setFixedHeight(125)
        self.fits_list.itemClicked.connect(self.inspect_selected_fits)
        layout.addWidget(self.fits_list)

        # Metadata Display Area
        metadata_frame = QFrame()
        metadata_layout = QVBoxLayout(metadata_frame)
        metadata_frame.setStyleSheet("background-color: #2B2B2B; border: 1px solid #5A5A5A;")
        metadata_layout.setContentsMargins(10, 10, 10, 10)

        # Metadata Dropdown
        metadata_label = QLabel("FITS Inspection:")
        metadata_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; text-decoration: underline;")
        metadata_layout.addWidget(metadata_label)

        self.metadata_combo = QComboBox()
        self.metadata_combo.setStyleSheet("color: white; background-color: #3A3A3A; font-size: 14px; padding: 5px;")
        self.metadata_combo.currentIndexChanged.connect(self.update_metadata_display)
        metadata_layout.addWidget(self.metadata_combo)

        # Scrollable Metadata Area
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("background-color: #1E1E1E; border: none;")
        scroll_area.setWidgetResizable(True)

        self.metadata_grid = QWidget()
        self.metadata_grid_layout = QGridLayout(self.metadata_grid)
        self.metadata_grid_layout.setAlignment(Qt.AlignTop)
        self.metadata_grid_layout.setColumnStretch(1, 1)  # Ensure values stretch to use available space
        scroll_area.setWidget(self.metadata_grid)

        metadata_layout.addWidget(scroll_area)
        layout.addWidget(metadata_frame)

        self.setLayout(layout)

    def toggle_input_mode(self):
        """Toggle between RA/DEC, Run-Camcol-Field, and Directory modes."""
        self.ra_dec_inputs.setVisible(self.ra_dec_radio.isChecked())
        self.run_camcol_field_inputs.setVisible(self.run_camcol_field_radio.isChecked())
        is_directory_mode = self.directory_radio.isChecked()

        # Hide bands checklist, fetch button, progress bar, and "Select Bands" label in Directory mode
        for checkbox in self.bands_checkboxes.values():
            checkbox.setVisible(not is_directory_mode)
        self.fetch_button.setVisible(not is_directory_mode)
        self.progress_bar.setVisible(not is_directory_mode)
        self.band_label.setVisible(not is_directory_mode)
        self.directory_button.setVisible(is_directory_mode)

    def start_fits_download(self):
        """Start downloading FITS files."""
        self.fits_list.clear()  # Clear the FITS list before starting the download
        self.clear_metadata_display()  # Clear metadata display before starting a new download
        self.notification_label.setText("")  # Clear any existing messages
        
        # Determine input mode and validate inputs
        if self.ra_dec_radio.isChecked():
            ra = self.ra_entry.text()
            dec = self.dec_entry.text()
            if not validate_ra_dec(ra, dec):
                self.notification_label.setText("<span style='color: red;'>Invalid RA/DEC values. Please try again.</span>")
                return
            run_camcol_field = query_run_camcol_field(float(ra), float(dec))
            if not run_camcol_field:
                self.notification_label.setText("<span style='color: red;'>No Run-Camcol-Field found for the given RA/DEC.</span>")
                return
        elif self.run_camcol_field_radio.isChecked():
            # Check for missing fields in Run-Camcol-Field mode
            run = self.run_entry.text()
            camcol = self.camcol_entry.text()
            field = self.field_entry.text()
            if not (run and camcol and field):
                self.notification_label.setText("<span style='color: red;'>All Run, Camcol, and Field values are required.</span>")
                return
            run_camcol_field = f"{run}-{camcol}-{field}"

        # Get the selected bands
        selected_bands = [band for band, checkbox in self.bands_checkboxes.items() if checkbox.isChecked()]
        if not selected_bands:
            self.notification_label.setText("<span style='color: red;'>No bands selected. Please select at least one band.</span>")
            return

        # Generate FITS URLs using get_fits_urls
        fits_urls = get_fits_urls(run_camcol_field, selected_bands)
        if not fits_urls:
            self.notification_label.setText("<span style='color: red;'>Failed to generate FITS URLs. Please check your inputs.</span>")
            return

        # Display information about the download process
        self.notification_label.setText(f"<span style='color: #5A9;'>Starting download for: {run_camcol_field}</span>")

        # Start the download process in a separate thread
        self.thread = FITSDownloadThread(run_camcol_field, selected_bands)
        self.thread.progress_signal.connect(self.progress_bar.setValue)
        self.thread.finished_signal.connect(self.on_download_complete)
        self.thread.start()

    def on_download_complete(self):
        """Handle completion of FITS download."""
        # Update the last directory to the folder where FITS files were downloaded
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        data_dir = os.path.join(base_dir, 'data')
        downloaded_directory = os.path.join(data_dir, self.thread.run_camcol_field)  # Access run_camcol_field from the thread
        
        if os.path.exists(downloaded_directory):  # Ensure the directory exists
            self.last_directory = downloaded_directory
        
        self.notification_label.setText("Download complete!")
        
        # Reload the directory where files were saved
        self.load_fits_files(self.last_directory)

        
    def select_directory(self):
        """Select a directory to list FITS files."""
        directory = QFileDialog.getExistingDirectory(self, "Select FITS Directory", self.last_directory)
        if directory:
            self.last_directory = directory
            self.load_fits_files(directory)

    def load_fits_files(self, directory):
        """Load and display FITS files from the selected directory."""
        self.fits_list.clear()
        for file_name in os.listdir(directory):
            if file_name.lower().endswith(".fits"):
                self.fits_list.addItem(QListWidgetItem(file_name))

    def inspect_selected_fits(self, item):
        """Load the selected FITS file and populate dropdown options."""
        file_path = os.path.join(self.last_directory, item.text())  # Use self.last_directory
        self.current_file_path = file_path
        try:
            if self.hdul_data is not None:
                self.hdul_data.close()  # Close any previously opened FITS file

            self.hdul_data = fits.open(file_path)  # Open the FITS file and keep it open
            self.metadata_combo.clear()
            self.metadata_combo.addItems(["HDUL Info"] + [f"HDU {i}" for i in range(len(self.hdul_data))])
            self.update_metadata_display(0)
        except Exception as e:
            self.metadata_display.setText(f"Error reading FITS file: {e}")

    def add_metadata_entry(self, key, value):
        """Add a metadata key-value pair to the grid."""
        row = self.metadata_grid_layout.rowCount()
        key_label = QLabel(f"{key}:")
        key_label.setStyleSheet("color: #5A9; font-size: 16px; font-weight: bold; padding: 2px;")
        value_label = QLabel(str(value))
        value_label.setStyleSheet("color: white; font-size: 16px; padding: 2px;")
        self.metadata_grid_layout.addWidget(key_label, row, 0, Qt.AlignCenter)
        self.metadata_grid_layout.addWidget(value_label, row, 1, Qt.AlignCenter)
    
    def update_metadata_display(self, index):
        """Update the inspection display based on selected option."""
        self.clear_metadata_display()

        if not self.hdul_data:
            return

        if index == 0:  # HDUL Info
            for i, hdu in enumerate(self.hdul_data):
                hdu_info = f"{type(hdu).__name__}, {hdu.data.shape if hdu.data is not None else 'No Data'}"
                self.add_metadata_entry(f"HDU {i}", hdu_info)
        else:  # Specific HDU Header
            hdu = self.hdul_data[index - 1]
            for key, value in hdu.header.items():
                self.add_metadata_entry(key, value)
                
    def clear_metadata_display(self):
        """Clear the metadata grid layout."""
        while self.metadata_grid_layout.count():
            item = self.metadata_grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def closeEvent(self, event):
        """Handle widget close event to clean up resources."""
        if self.hdul_data is not None:
            self.hdul_data.close()
        event.accept()