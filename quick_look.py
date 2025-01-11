from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QWidget, QLineEdit, QPushButton, QMessageBox, QFileDialog, QGridLayout, QCheckBox, QApplication
)
from PyQt5.QtGui import QPixmap, QImage, QClipboard
from PyQt5.QtCore import Qt

# Import the fetch and other utility functions
from utilities import validate_ra_dec, fetch_sdss_image, get_object_id, get_object_details, get_run_camcol_field

class StyledMessageBox(QMessageBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet(
            "QMessageBox { background-color: #2B2B2B; color: white; font-size: 14px; } "
            "QPushButton { background-color: #5A9; color: white; border-radius: 5px; padding: 5px; }"
            "QPushButton:hover { background-color: #4A8; }"
        )

class QuickLook(QWidget):
    def __init__(self, parent_tab_widget):
        super().__init__()
        self.parent_tab_widget = parent_tab_widget
        self.tab_image_mapping = {}

        layout = QVBoxLayout(self)

        # Main frame for Quick Look
        main_frame = QFrame(self)
        main_frame.setStyleSheet("background-color: #2B2B2B;")
        layout.addWidget(main_frame)

        main_layout = QHBoxLayout(main_frame)

        # Left Section
        left_section = QFrame(main_frame)
        left_section.setStyleSheet("background-color: #4E4E4E; border: 1px solid #5A5A5A; padding: 10px;")
        left_section.setFixedWidth(350)
        main_layout.addWidget(left_section)

        # Initialize the left section
        self.init_left_section(left_section)

        # Center Section
        center_section = QTabWidget(main_frame)
        center_section.setStyleSheet("background-color: #3A3A3A; border: 1px solid #5A5A5A;")
        center_section.setTabsClosable(True)
        center_section.tabBar().setVisible(False)
        center_section.tabCloseRequested.connect(self.parent_tab_widget.tabCloseRequested)
        main_layout.addWidget(center_section, stretch=3)
        self.quick_look_center_section = center_section  # Save reference for dynamic tab updates

        # Right Section
        right_section = QFrame(main_frame)
        right_section.setStyleSheet("background-color: #4E4E4E; border: 1px solid #5A5A5A; padding: 10px;")
        right_section.setFixedWidth(350)
        main_layout.addWidget(right_section)

        # Initialize the right section
        self.init_right_section(right_section)

    def init_left_section(self, parent):
        layout = QVBoxLayout(parent)
        input_grid = QGridLayout()
        input_grid.setHorizontalSpacing(10)
        input_grid.setVerticalSpacing(15)

        # Input fields and labels
        for row, (label_text, placeholder, attr_name) in enumerate([
            ("RA (deg):", "Enter RA", "ra_entry"),
            ("DEC (deg):", "Enter DEC", "dec_entry"),
            ("Width:", "2048", "width_entry"),
            ("Height:", "1489", "height_entry"),
            ("Scale:", "0.2", "scale_entry")
        ]):
            label = QLabel(label_text)
            label.setStyleSheet("color: white; font-size: 14px;")
            label.setFixedWidth(100)

            field = QLineEdit()
            field.setPlaceholderText(placeholder)
            field.setStyleSheet(
                "padding: 5px; font-size: 14px; color: white; border: 1px solid gray; border-radius: 5px;"
            )
            field.setFixedWidth(150)

            setattr(self, attr_name, field)
            input_grid.addWidget(label, row, 0)
            input_grid.addWidget(field, row, 1)

        # Fetch and Save buttons
        self.fetch_button = QPushButton("Fetch Image")
        self.fetch_button.setStyleSheet("background-color: #5A9; color: white; padding: 10px; margin-top: 10px;")
        self.fetch_button.clicked.connect(self.display_image)

        self.save_button = QPushButton("Save Image")
        self.save_button.setStyleSheet("background-color: #5A9; color: white; padding: 10px; margin-top: 10px;")
        self.save_button.clicked.connect(self.save_image)
        self.save_button.setEnabled(False)

        layout.addLayout(input_grid)
        layout.addWidget(self.fetch_button)
        layout.addWidget(self.save_button)

        # Checkboxes for options
        self.photometric_checkbox = QCheckBox("Photometric Objects")
        self.photometric_checkbox.setStyleSheet("color: white; font-size: 14px;")
        self.photometric_checkbox.setChecked(False)
        layout.addWidget(self.photometric_checkbox)

        self.spectra_checkbox = QCheckBox("Objects with Spectra")
        self.spectra_checkbox.setStyleSheet("color: white; font-size: 14px;")
        self.spectra_checkbox.setChecked(False)
        layout.addWidget(self.spectra_checkbox)

        self.invert_checkbox = QCheckBox("Invert Image")
        self.invert_checkbox.setStyleSheet("color: white; font-size: 14px;")
        self.invert_checkbox.setChecked(False)
        layout.addWidget(self.invert_checkbox)

        layout.addStretch()

    def display_image(self):
        try:
            ra = self.ra_entry.text()
            dec = self.dec_entry.text()
            width = int(self.width_entry.text() or 2048)
            height = int(self.height_entry.text() or 1489)
            scale = float(self.scale_entry.text() or 0.2)

            # Use the validate_ra_dec function
            if not validate_ra_dec(ra, dec):
                print("Invalid RA/DEC values. RA should be between 0-360 and DEC between -90 to 90.")
                return

            # Convert RA/DEC to floats after validation
            ra = float(ra)
            dec = float(dec)

        except ValueError:
            print("Please enter valid numerical values.")
            return
        
        image = fetch_sdss_image(ra, dec, scale, width, height)
        if image:
            try:
                image = image.convert("RGB")
                qimage = QImage(image.tobytes("raw", "RGB"), image.width, image.height, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage)

                new_tab = QWidget()
                new_tab_layout = QVBoxLayout()
                image_label = QLabel()
                image_label.setPixmap(pixmap)
                image_label.setAlignment(Qt.AlignCenter)
                new_tab_layout.addWidget(image_label)

                # Fetch metadata
                obj_id = get_object_id(ra, dec)
                if obj_id:
                    details = get_object_details(obj_id)
                    run, camcol, field = get_run_camcol_field(details['ra'], details['dec'])

                    # Update right section with object details
                    self.object_id_value.setText(str(obj_id))
                    self.ra_value.setText(f"{details['ra']:.5f}" if details["ra"] else "Not Retrieved")
                    self.dec_value.setText(f"{details['dec']:.5f}" if details["dec"] else "Not Retrieved")
                    for band in ["u", "g", "r", "i", "z"]:
                        getattr(self, f"{band}_value").setText(f"{details[band]:.2f}" if details[band] else "Not Retrieved")
                    self.type_value.setText(f"{details['type']}")
                    
                    self.run_value.setText(str(run) if run else "Not Retrieved")
                    self.camcol_value.setText(str(camcol) if camcol else "Not Retrieved")
                    self.field_value.setText(str(field) if field else "Not Retrieved")

                new_tab.setLayout(new_tab_layout)
                tab_index = self.quick_look_center_section.addTab(new_tab, f"RA: {ra}, DEC: {dec}")
                self.quick_look_center_section.setCurrentWidget(new_tab)

                # Store the image in the tab-to-image mapping
                if not hasattr(self, "tab_image_mapping"):
                    self.tab_image_mapping = {}
                self.tab_image_mapping[tab_index] = image

                self.save_button.setEnabled(True)
            except Exception as e:
                print(f"Error displaying image: {e}")
        else:
            print("Failed to fetch image.")

    def save_image(self):
        # Ensure the mapping exists
        if not hasattr(self, "tab_image_mapping"):
            print("No images available to save.")
            return

        # Get the current tab index
        current_tab_index = self.quick_look_center_section.currentIndex()

        # Check if the current tab index has an associated image
        if current_tab_index not in self.tab_image_mapping:
            print("No image associated with the current tab.")
            return

        # Retrieve the image associated with the current tab
        image = self.tab_image_mapping[current_tab_index]
        if image:
            # Open a file dialog for the user to save the image
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)")
            if file_path:
                try:
                    # Save the image
                    image.save(file_path)
                    print(f"Image successfully saved to {file_path}")
                except Exception as e:
                    print(f"Error saving image: {e}")
            else:
                print("Save operation canceled.")
        else:
            print("No image found for the current tab.")


    def init_right_section(self, parent):
        layout = QVBoxLayout(parent)

        def make_copyable_label(text):
            label = QLabel(text)
            label.setStyleSheet("""
                padding: 5px;
                font-size: 14px;
                color: white;
                border: 1px solid #5A5A5A;
                background-color: #2E2E2E;
                border-radius: 4px;
            """)
            label.setWordWrap(True)

            def copy_to_clipboard(event):
                clipboard = QApplication.clipboard()
                clipboard.setText(label.text())
                print(f"Copied to clipboard: {label.text()}")  # Optional debug log

            label.mousePressEvent = copy_to_clipboard
            return label

        # Object Details Section
        object_details_label = QLabel("Object Details")
        object_details_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
            padding: 5px;
            border-bottom: 1px solid #5A5A5A;
        """)
        layout.addWidget(object_details_label)

        # Create a grid layout for object details
        object_details_grid = QGridLayout()
        object_details_grid.setHorizontalSpacing(10)
        object_details_grid.setVerticalSpacing(10)

        # Define label width
        label_width = 100

        # Object ID
        object_id_label = QLabel("Object ID:")
        object_id_label.setStyleSheet("color: white; font-size: 14px;")
        object_id_label.setFixedWidth(label_width)
        self.object_id_value = make_copyable_label("Not Retrieved")
        object_details_grid.addWidget(object_id_label, 0, 0)
        object_details_grid.addWidget(self.object_id_value, 0, 1)

        # RA and DEC
        ra_label = QLabel("RA:")
        ra_label.setStyleSheet("color: white; font-size: 14px;")
        ra_label.setFixedWidth(label_width)
        self.ra_value = make_copyable_label("Not Retrieved")
        dec_label = QLabel("DEC:")
        dec_label.setStyleSheet("color: white; font-size: 14px;")
        dec_label.setFixedWidth(label_width)
        self.dec_value = make_copyable_label("Not Retrieved")
        object_details_grid.addWidget(ra_label, 1, 0)
        object_details_grid.addWidget(self.ra_value, 1, 1)
        object_details_grid.addWidget(dec_label, 2, 0)
        object_details_grid.addWidget(self.dec_value, 2, 1)

        # Type
        type_label = QLabel("Type:")
        type_label.setStyleSheet("color: white; font-size: 14px;")
        type_label.setFixedWidth(label_width)
        self.type_value = make_copyable_label("Not Retrieved")
        object_details_grid.addWidget(type_label, 3, 0)
        object_details_grid.addWidget(self.type_value, 3, 1)

        # Magnitudes (u, g, r, i, z)
        for row, band in enumerate(["u", "g", "r", "i", "z"], start=4):
            band_label = QLabel(f"{band}-band:")
            band_label.setStyleSheet("color: white; font-size: 14px;")
            band_label.setFixedWidth(label_width)
            band_value = make_copyable_label("Not Retrieved")
            setattr(self, f"{band}_value", band_value)
            object_details_grid.addWidget(band_label, row, 0)
            object_details_grid.addWidget(band_value, row, 1)

        # Add the object details grid to the layout
        layout.addLayout(object_details_grid)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #5A5A5A; height: 1px; margin: 10px 0;")
        layout.addWidget(separator)

        # Run-Camcol-Field Section
        run_camcol_field_label = QLabel("Run-Camcol-Field")
        run_camcol_field_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
            padding: 5px;
            border-bottom: 1px solid #5A5A5A;
        """)
        layout.addWidget(run_camcol_field_label)

        # Create a grid layout for Run-Camcol-Field
        run_camcol_field_grid = QGridLayout()
        run_camcol_field_grid.setHorizontalSpacing(10)
        run_camcol_field_grid.setVerticalSpacing(10)

        # Run
        run_label = QLabel("Run:")
        run_label.setStyleSheet("color: white; font-size: 14px;")
        run_label.setFixedWidth(label_width)
        self.run_value = make_copyable_label("Not Retrieved")
        run_camcol_field_grid.addWidget(run_label, 0, 0)
        run_camcol_field_grid.addWidget(self.run_value, 0, 1)

        # Camcol
        camcol_label = QLabel("Camcol:")
        camcol_label.setStyleSheet("color: white; font-size: 14px;")
        camcol_label.setFixedWidth(label_width)
        self.camcol_value = make_copyable_label("Not Retrieved")
        run_camcol_field_grid.addWidget(camcol_label, 1, 0)
        run_camcol_field_grid.addWidget(self.camcol_value, 1, 1)

        # Field
        field_label = QLabel("Field:")
        field_label.setStyleSheet("color: white; font-size: 14px;")
        field_label.setFixedWidth(label_width)
        self.field_value = make_copyable_label("Not Retrieved")
        run_camcol_field_grid.addWidget(field_label, 2, 0)
        run_camcol_field_grid.addWidget(self.field_value, 2, 1)

        # Add the run-camcol-field grid to the layout
        layout.addLayout(run_camcol_field_grid)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #5A5A5A; height: 1px; margin: 10px 0;")
        layout.addWidget(separator)

        # Circular Info Button
        info_button = QPushButton("i")
        info_button.setStyleSheet("""
            QPushButton {
                background-color: #5A9;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 14px;
                width: 28px;
                height: 28px;
            }
            QPushButton:hover {
                background-color: #4A8;
            }
        """)
        info_button.clicked.connect(self.show_info)
        layout.addWidget(info_button, alignment=Qt.AlignRight)

        layout.addStretch()
    
    def show_info(self):
        message = (
            "The displayed image is a mosaic of overlapping SDSS fields, dynamically generated based on your input. "
            "Variations may occur due to moving objects, variable stars, or differences across observation runs."
        )
        msg_box = StyledMessageBox(self)
        msg_box.setText(message)
        msg_box.setWindowTitle("Image Information")
        msg_box.exec_()