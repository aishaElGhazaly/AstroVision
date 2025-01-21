from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QWidget, QLineEdit, QPushButton, QFileDialog, QGridLayout, QCheckBox, QMessageBox, 
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
)
from PyQt5.QtGui import QPixmap, QImage, QPen
from PyQt5.QtCore import Qt
from utilities import validate_ra_dec, fetch_sdss_image, get_object_id, get_object_details, get_run_rerun_camcol_field


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
        self.tab_scene_mapping = {}  # Map tab indices to QGraphicsScenes
        self.tab_view_mapping = {}   # Map tab indices to QGraphicsViews
        self.overlay_item_mapping = {}  # Map tab indices to overlay items
        
        # Initialize QGraphicsScene and QGraphicsView
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)  # Link the view to the scene
        self.image_item = None
        self.overlay_item = None
        
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
            ("Width:", "1085", "width_entry"),
            ("Height:", "825", "height_entry"),
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
        self.label_checkbox = QCheckBox("Label")
        self.label_checkbox.setStyleSheet("color: white; font-size: 15px;")
        self.label_checkbox.setChecked(False)
        self.label_checkbox.stateChanged.connect(self.toggle_overlay)
        layout.addWidget(self.label_checkbox)
        
        self.photometric_checkbox = QCheckBox("Photometric Objects")
        self.photometric_checkbox.setStyleSheet("color: white; font-size: 15px;")
        self.photometric_checkbox.setChecked(False)
        layout.addWidget(self.photometric_checkbox)

        self.spectra_checkbox = QCheckBox("Objects with Spectra")
        self.spectra_checkbox.setStyleSheet("color: white; font-size: 15px;")
        self.spectra_checkbox.setChecked(False)
        layout.addWidget(self.spectra_checkbox)

        layout.addStretch()

    def init_right_section(self, parent):
        layout = QVBoxLayout(parent)

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
        layout.addWidget(object_details_label)

        # Create a grid layout for object details
        object_details_grid = QGridLayout()
        object_details_grid.setHorizontalSpacing(10)
        object_details_grid.setVerticalSpacing(10)

        # Define label width
        label_width = 100
        
        # Information fields
        fields = [
            ("Object ID:", "object_id_value"),
            ("RA:", "ra_value"),
            ("DEC:", "dec_value"),
            ("u-band:", "u_value"),
            ("g-band:", "g_value"),
            ("r-band:", "r_value"),
            ("i-band:", "i_value"),
            ("z-band:", "z_value"),
            ("SpecObj ID:", "specobj_id_value"),
            ("Class:", "class_value"),
            ("Redshift:", "redshift_value"),
            ("Run:", "run_value"),
            ("Rerun:", "rerun_value"),
            ("Camcol:", "camcol_value"),
            ("Field:", "field_value"),
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
            if label_text in ["z-band:", "Redshift:", "Field:"]:
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setFrameShadow(QFrame.Sunken)
                separator.setStyleSheet("background-color: #5A5A5A; height: 5px; margin: 10px 0;")
                object_details_grid.addWidget(separator, current_row, 0, 1, 2)
                current_row += 1

        # Add the object details grid to the layout
        layout.addLayout(object_details_grid)
        layout.addStretch()

    def display_image(self):
        try:
            # Parse and validate user inputs
            ra = float(self.ra_entry.text())
            dec = float(self.dec_entry.text())
            width = int(self.width_entry.text() or 1085)
            height = int(self.height_entry.text() or 825)
            scale = float(self.scale_entry.text() or 0.2)
        except ValueError:
            print("Please enter valid numerical values.")
            return

        # Fetch the SDSS image
        image = fetch_sdss_image(ra, dec, scale, width, height)
        if image:
            try:
                # Convert the fetched image to QPixmap
                qimage = QImage(image.tobytes("raw", "RGB"), image.width, image.height, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage)

                # Create a new scene and add the image
                scene = QGraphicsScene()
                image_item = QGraphicsPixmapItem(pixmap)
                scene.addItem(image_item)

                # Create a new view for the scene
                view = QGraphicsView(scene)

                # Create a new tab and add the view
                new_tab = QWidget()
                layout = QVBoxLayout(new_tab)
                layout.addWidget(view)

                tab_index = self.quick_look_center_section.addTab(new_tab, f"RA: {ra}, DEC: {dec}")
                self.quick_look_center_section.setCurrentIndex(tab_index)

                # Map the scene, view, and overlay for the current tab
                self.tab_scene_mapping[tab_index] = scene
                self.tab_view_mapping[tab_index] = view
                self.overlay_item_mapping[tab_index] = None

                # Fetch metadata and update the right section
                obj_id = get_object_id(ra, dec)
                if obj_id:
                    details = get_object_details(obj_id)
                    run, rerun, camcol, field = get_run_rerun_camcol_field(details['ra'], details['dec'])

                    self.object_id_value.setText(str(obj_id))
                    self.ra_value.setText(f"{details['ra']:.5f}" if details["ra"] else "Not Retrieved")
                    self.dec_value.setText(f"{details['dec']:.5f}" if details["dec"] else "Not Retrieved")
                    for band in ["u", "g", "r", "i", "z"]:
                        getattr(self, f"{band}_value").setText(f"{details[band]:.2f}" if details[band] else "Not Retrieved")
                    self.run_value.setText(str(run) if run else "Not Retrieved")
                    self.rerun_value.setText(str(rerun) if rerun else "Not Retrieved")
                    self.camcol_value.setText(str(camcol) if camcol else "Not Retrieved")
                    self.field_value.setText(str(field) if field else "Not Retrieved")
                    self.specobj_id_value.setText(str(details['specObjID']) if details['specObjID'] else "Not Retrieved")
                    self.class_value.setText(details['class'] if details['class'] else "Not Retrieved")
                    self.redshift_value.setText(f"{details['redshift']:.5f}" if details['redshift'] else "Not Retrieved")

                self.save_button.setEnabled(True)
            except Exception as e:
                print(f"Error displaying image: {e}")
        else:
            print("Failed to fetch image.")

            
    def toggle_overlay(self):
        # Get the current tab index
        current_index = self.quick_look_center_section.currentIndex()
        if current_index == -1 or current_index not in self.tab_scene_mapping:
            return

        # Get the associated scene for the current tab
        scene = self.tab_scene_mapping[current_index]

        # Remove the existing overlay if present
        if self.overlay_item_mapping[current_index]:
            scene.removeItem(self.overlay_item_mapping[current_index])
            self.overlay_item_mapping[current_index] = None

        # Add overlay if the checkbox is checked
        if self.label_checkbox.isChecked():
            # Get the image item from the scene
            image_item = next((item for item in scene.items() if isinstance(item, QGraphicsPixmapItem)), None)
            if not image_item:
                return

            # Get the dimensions of the pixmap
            pixmap = image_item.pixmap()
            pixmap_width = pixmap.width()
            pixmap_height = pixmap.height()

            # Calculate the center of the pixmap
            center_x = pixmap_width // 2
            center_y = pixmap_height // 2
            box_size = 50  # Size of the overlay box

            # Create a rectangle for the overlay
            rect = QGraphicsRectItem(
                center_x - box_size // 2, center_y - box_size // 2, box_size, box_size
            )
            rect.setPen(QPen(Qt.green, 3))  # Green border with thickness 3

            # Add the rectangle to the scene and map it
            scene.addItem(rect)
            self.overlay_item_mapping[current_index] = rect

    def save_image(self):
        current_tab_index = self.quick_look_center_section.currentIndex()
        image = self.tab_image_mapping.get(current_tab_index)
        if not image:
            print("No image found for the current tab.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)")
        if file_path:
            try:
                image.save(file_path)
                print(f"Image successfully saved to {file_path}")
            except Exception as e:
                print(f"Error saving image: {e}")
            return