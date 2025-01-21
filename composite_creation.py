from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QCheckBox, QFrame, QComboBox, QSlider, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from astropy.io import fits
from astropy.wcs import WCS
from astropy.visualization import make_lupton_rgb
from reproject import reproject_interp
import os
import re
import numpy as np
from PIL import Image
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class MatplotlibCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)

        # Make the background transparent
        self.setStyleSheet("background-color: transparent;")

        # Initially hide the axes and set transparent
        self.ax.axis('off')
        self.fig.patch.set_alpha(0)  # Make figure transparent

    def display_image(self, rgb_image):
        """Display the composite RGB image on the canvas."""
        self.ax.clear()  # Clear the axes
        self.ax.imshow(rgb_image, origin='lower', aspect='equal')  # Display the image without fixed aspect ratio
        self.ax.axis('off')  # Hide axes for a clean look
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)  # Remove any padding/margins
        self.draw()  # Render the updated canvas

    def reset_canvas(self):
        """Reset the canvas to its transparent state."""
        self.ax.clear()
        self.ax.axis('off')  # Hide axes
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)  # Reset margins
        self.draw()


class CompositeCreation(QWidget):
    def __init__(self, parent_tab_widget):
        super().__init__()
        self.parent_tab_widget = parent_tab_widget
        self.fits_files = {}
        self.selected_filters = []
        self.reference_file = None  # Reference file for alignment
        self.auto_scale = False  # Automatic scaling checkbox state

        layout = QHBoxLayout(self)

        # Left Section: Image Display
        left_section = QFrame()
        left_section.setStyleSheet("background-color: #2B2B2B; padding: 10px; border: 1px solid #5A5A5A;")
        layout.addWidget(left_section, stretch=3)
        self.init_left_section(left_section)

        # Right Section: FITS Upload and Configuration
        right_section = QFrame()
        right_section.setStyleSheet("background-color: #4E4E4E; padding: 10px; border: 1px solid #5A5A5A;")
        right_section.setFixedWidth(400)
        layout.addWidget(right_section, stretch=1)
        self.init_right_section(right_section)

    def init_left_section(self, parent):
        layout = QVBoxLayout(parent)

        # Matplotlib Canvas for Image Display
        self.canvas = MatplotlibCanvas(self)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Matplotlib Toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet("color: white;")
        self.toolbar.hide()  # Initially hide the toolbar
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, stretch=5)


    def init_right_section(self, parent):
        layout = QVBoxLayout(parent)

        # Directory Selection
        directory_label = QLabel("Select Directory")
        directory_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        layout.addWidget(directory_label)

        self.directory_input = QLineEdit()
        self.directory_input.setStyleSheet("background-color: #3A3A3A; color: white; padding: 5px; font-size: 14px;")
        self.directory_input.setPlaceholderText("Select FITS file directory")

        browse_button = QPushButton("Browse")
        browse_button.setStyleSheet("background-color: #5A9; color: white; padding: 5px;")
        browse_button.clicked.connect(self.select_directory)

        dir_row = QHBoxLayout()
        dir_row.addWidget(self.directory_input, stretch=1)
        dir_row.addWidget(browse_button)
        layout.addLayout(dir_row)

        # Warning Label
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: #5A9; font-size: 12px; margin-top: 5px;")
        layout.addWidget(self.warning_label)

        # Filter Selection for RGB
        filter_label = QLabel("Color Mapping")
        filter_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(filter_label)

        self.filter_dropdowns = {}
        colors = ["Red", "Green", "Blue"]
        for color in colors:
            row = QHBoxLayout()

            color_label = QLabel(f"{color} Channel:")
            color_label.setStyleSheet("color: white; font-size: 14px;")
            color_label.setFixedWidth(150)
            row.addWidget(color_label)

            dropdown = QComboBox()
            dropdown.setStyleSheet("background-color: #3A3A3A; color: white; padding: 5px; font-size: 14px;")
            dropdown.addItems(["Select Filter"])
            dropdown.setEnabled(False)  # Initially disabled
            dropdown.currentIndexChanged.connect(self.update_reference_dropdown)
            self.filter_dropdowns[color] = dropdown
            row.addWidget(dropdown, stretch=1)

            layout.addLayout(row)

        # Preprocessing Options
        preprocessing_label = QLabel("Preprocessing Options")
        preprocessing_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(preprocessing_label)

        reference_row = QHBoxLayout()

        reference_label = QLabel("Reference Frame:")
        reference_label.setStyleSheet("color: white; font-size: 14px;")
        reference_label.setFixedWidth(150)
        reference_row.addWidget(reference_label)

        self.reference_dropdown = QComboBox()
        self.reference_dropdown.setStyleSheet("background-color: #3A3A3A; color: white; padding: 5px; font-size: 14px;")
        self.reference_dropdown.addItems(["Select Reference File"])
        self.reference_dropdown.setEnabled(False)  # Initially disabled
        reference_row.addWidget(self.reference_dropdown, stretch=1)

        layout.addLayout(reference_row)

        # Stretch Factor
        stretch_row = QHBoxLayout()

        stretch_label = QLabel("Stretch:")
        stretch_label.setStyleSheet("color: white; font-size: 14px;")
        stretch_label.setFixedWidth(150)
        stretch_row.addWidget(stretch_label)

        self.stretch_slider = QSlider(Qt.Horizontal)
        self.stretch_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #5A5A5A;
                height: 8px;
                background: #3A3A3A;
                margin: 2px 0;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 1px solid #5A5A5A;
                width: 14px;
                height: 14px;
            }
            QSlider::handle:horizontal:hover {
                background: #7BB;
            }
            QSlider::sub-page:horizontal {
                background: #5A9;
            }
            QSlider::add-page:horizontal {
                background: #2B2B2B;
            }
        """)
        self.stretch_slider.setMinimum(1)  # Represents 0.1
        self.stretch_slider.setMaximum(100)  # Represents 10.0
        self.stretch_slider.setValue(5)  # Default is 1.0
        self.stretch_slider.valueChanged.connect(self.update_stretch_input)

        stretch_row.addWidget(self.stretch_slider, stretch=1)

        self.stretch_input = QLineEdit()
        self.stretch_input.setStyleSheet("background-color: #3A3A3A; color: white; padding: 5px; font-size: 14px; border: 1px solid #5A5A5A;")
        self.stretch_input.setText("0.5")
        self.stretch_input.setFixedWidth(60)
        self.stretch_input.setAlignment(Qt.AlignCenter)
        self.stretch_input.textChanged.connect(self.update_stretch_slider)  # Sync with slider
        stretch_row.addWidget(self.stretch_input)

        layout.addLayout(stretch_row)

        # Q Factor
        q_row = QHBoxLayout()

        q_label = QLabel("Q Factor:")
        q_label.setStyleSheet("color: white; font-size: 14px;")
        q_label.setFixedWidth(150)
        q_row.addWidget(q_label)

        self.q_slider = QSlider(Qt.Horizontal)
        self.q_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #5A5A5A;
                height: 8px;
                background: #3A3A3A;
                margin: 2px 0;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 1px solid #5A5A5A;
                width: 14px;
                height: 14px;
            }
            QSlider::handle:horizontal:hover {
                background: #7BB;
            }
            QSlider::sub-page:horizontal {
                background: #5A9;
            }
            QSlider::add-page:horizontal {
                background: #2B2B2B;
            }
        """)
        self.q_slider.setMinimum(1)
        self.q_slider.setMaximum(100)
        self.q_slider.setValue(10)
        self.q_slider.valueChanged.connect(self.update_q_input)

        q_row.addWidget(self.q_slider, stretch=1)

        self.q_input = QLineEdit()
        self.q_input.setStyleSheet("background-color: #3A3A3A; color: white; padding: 5px; font-size: 14px; border: 1px solid #5A5A5A;")
        self.q_input.setText("10")
        self.q_input.setFixedWidth(60)
        self.q_input.setAlignment(Qt.AlignCenter)
        self.q_input.textChanged.connect(self.update_q_slider)  # Sync with slider
        q_row.addWidget(self.q_input)

        layout.addLayout(q_row)

        # Generate Button
        generate_button = QPushButton("Generate Composite")
        generate_button.setStyleSheet("background-color: #5A9; color: white; font-weight: bold; padding: 10px;")
        generate_button.clicked.connect(self.generate_composite)
        layout.addWidget(generate_button)

        # Add Save as FITS Button
        save_fits_button = QPushButton("Save as FITS")
        save_fits_button.setStyleSheet("background-color: #5A9; color: white; font-weight: bold; padding: 10px;")
        save_fits_button.clicked.connect(self.save_as_fits)
        layout.addWidget(save_fits_button)
        
        # Add Save as Image Button
        save_image_button = QPushButton("Save as Image")
        save_image_button.setStyleSheet("background-color: #5A9; color: white; font-weight: bold; padding: 10px;")
        save_image_button.clicked.connect(self.save_as_image)
        layout.addWidget(save_image_button)

        layout.addStretch()

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select FITS Directory", "")
        if directory:
            self.directory_input.setText(directory)
            self.check_filters(directory)

    def check_filters(self, directory):
        """Enable preprocessing and populate dropdowns if enough FITS files are available."""
        available_filters = set()
        for file_name in os.listdir(directory):
            if file_name.lower().endswith(".fits"):
                for band in ["u", "g", "r", "i", "z"]:
                    if f"-{band}-" in file_name:
                        available_filters.add(band)

        # Enable dropdowns and preprocessing options if at least 3 filters are available
        if len(available_filters) >= 3:
            for dropdown in self.filter_dropdowns.values():
                dropdown.setEnabled(True)
                dropdown.clear()
                dropdown.addItems(["Select Filter"] + sorted(available_filters))

            self.reference_dropdown.setEnabled(True)
            self.reference_dropdown.clear()
            self.reference_dropdown.addItems(["Select Reference File"] + sorted(available_filters))

            self.warning_label.setText("")
        else:
            for dropdown in self.filter_dropdowns.values():
                dropdown.setEnabled(False)
                dropdown.clear()
                dropdown.addItem("Select Filter")

            self.reference_dropdown.setEnabled(False)
            self.reference_dropdown.clear()
            self.reference_dropdown.addItem("Select Reference File")

            self.warning_label.setText("Please select a directory with at least 3 FITS files.")

    def update_reference_dropdown(self):
        """Update the reference file dropdown based on selected RGB filters."""
        selected_filters = [
            dropdown.currentText() for dropdown in self.filter_dropdowns.values()
            if dropdown.currentText() != "Select Filter"
        ]

        if len(selected_filters) == 3:
            self.reference_dropdown.setEnabled(True)
            self.reference_dropdown.clear()
            self.reference_dropdown.addItems(["Select Reference File"] + selected_filters)
        else:
            self.reference_dropdown.setEnabled(False)
            self.reference_dropdown.clear()
            self.reference_dropdown.addItem("Select Reference File")
    
    def update_stretch_input(self, value):
        """Update the stretch input field when the slider changes."""
        stretch_value = value / 10.0
        self.stretch_input.setText(f"{stretch_value:.1f}")

    def update_stretch_slider(self, text):
        """Update the stretch slider when the input field changes."""
        try:
            stretch_value = float(text)
            if 0.1 <= stretch_value <= 10.0:
                self.stretch_slider.setValue(int(stretch_value * 10))
        except ValueError:
            pass  # Ignore invalid input

    def update_q_input(self, value):
        """Update the Q input field when the slider changes."""
        self.q_input.setText(str(value))

    def update_q_slider(self, text):
        """Update the Q slider when the input field changes."""
        try:
            q_value = int(text)
            if 1 <= q_value <= 100:
                self.q_slider.setValue(q_value)
        except ValueError:
            pass  # Ignore invalid input

    def generate_composite(self):
        """Generate the composite RGB image based on user input."""
        directory = self.directory_input.text()
        if not os.path.isdir(directory):
            self.warning_label.setText("Invalid directory. Please select a valid FITS directory.")
            return

        # Ensure all RGB channels are selected
        selected_filters = {
            color: dropdown.currentText()
            for color, dropdown in self.filter_dropdowns.items()
            if dropdown.currentText() != "Select Filter"
        }
        if len(selected_filters) < 3:
            self.warning_label.setText("Please select filters for all RGB channels.")
            return

        # Get the reference frame
        reference_filter = self.reference_dropdown.currentText()
        reference_file_path = None

        for file_name in os.listdir(directory):
            if re.match(rf"^frame-{reference_filter}-\d+-\d+-\d+\.fits$", file_name.lower()):
                reference_file_path = os.path.join(directory, file_name)
                break

        if not reference_file_path:
            self.warning_label.setText(f"Reference file for filter '{reference_filter}' not found in directory.")
            return

        # Fetch stretch and Q values
        try:
            stretch = float(self.stretch_input.text())
            q_factor = int(self.q_input.text())
        except ValueError:
            self.warning_label.setText("Invalid stretch or Q factor values.")
            return

        # Step 1: Load the reference FITS file
        try:
            reference_hdulist = fits.open(reference_file_path)
            reference_data = reference_hdulist[0].data
            reference_header = reference_hdulist[0].header
            reference_wcs = WCS(reference_header)
        except Exception as e:
            self.warning_label.setText(f"Error loading reference file: {e}")
            return

        # Step 2: Reproject and align all selected filters
        aligned_images = {}
        try:
            for color, filter_name in selected_filters.items():
                file_path = None
                for file_name in os.listdir(directory):
                    if re.match(rf"^frame-{filter_name}-\d+-\d+-\d+\.fits$", file_name.lower()):
                        file_path = os.path.join(directory, file_name)
                        break

                if not file_path:
                    self.warning_label.setText(f"File for filter '{filter_name}' not found in directory.")
                    return

                # Load and reproject
                hdulist = fits.open(file_path)
                data = hdulist[0].data
                header = hdulist[0].header
                wcs = WCS(header)

                reprojected_data, _ = reproject_interp(
                    (data, wcs), reference_wcs, shape_out=reference_data.shape
                )
                aligned_images[color] = np.nan_to_num(reprojected_data, nan=0.0)  # Handle NaNs
        except Exception as e:
            self.warning_label.setText(f"Error reprojecting images: {e}")
            return
        finally:
            reference_hdulist.close()


        # Step 3: Create the composite RGB image
        try:
            # Generate the composite RGB image
            rgb_image = make_lupton_rgb(
                aligned_images["Red"], aligned_images["Green"], aligned_images["Blue"],
                stretch=stretch, Q=q_factor
            )

            # Display the image on the Matplotlib canvas
            self.canvas.display_image(rgb_image)

            # Show the toolbar for interaction
            self.toolbar.show()
        except Exception as e:
            self.warning_label.setText(f"Error generating composite: {e}")
    
    def save_as_fits(self):
        """Save the current composite RGB image as a FITS file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save FITS File", "", "FITS Files (*.fits);;All Files (*)"
        )
        if file_path:
            try:
                # Retrieve the aligned images (R, G, B) used to create the composite
                red_data = self.aligned_images.get("Red")
                green_data = self.aligned_images.get("Green")
                blue_data = self.aligned_images.get("Blue")

                # Create Primary HDU with metadata
                primary_hdu = fits.PrimaryHDU()
                primary_hdu.header['COMMENT'] = "Composite RGB image"
                primary_hdu.header['STRETCH'] = self.stretch_input.text()
                primary_hdu.header['Q_FACTOR'] = self.q_input.text()

                # Create separate HDUs for each channel
                red_hdu = fits.ImageHDU(red_data, name="RED_CHANNEL")
                green_hdu = fits.ImageHDU(green_data, name="GREEN_CHANNEL")
                blue_hdu = fits.ImageHDU(blue_data, name="BLUE_CHANNEL")

                # Save the FITS file
                hdul = fits.HDUList([primary_hdu, red_hdu, green_hdu, blue_hdu])
                hdul.writeto(file_path, overwrite=True)

                self.warning_label.setText("FITS file saved successfully!")
            except Exception as e:
                self.warning_label.setText(f"Error saving FITS file: {e}")

    def save_as_image(self):
        """Save the current composite RGB image as an image file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "", "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
        )
        if file_path:
            try:
                # Retrieve the RGB image displayed on the canvas
                rgb_image = self.canvas.ax.images[0].get_array().data

                # Convert the RGB image to PIL format and save
                image = Image.fromarray((rgb_image * 255).astype(np.uint8))
                image.save(file_path)
                self.warning_label.setText("Image saved successfully!")
            except Exception as e:
                self.warning_label.setText(f"Error saving image: {e}")

