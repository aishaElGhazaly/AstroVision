from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox,
    QPushButton, QComboBox, QHeaderView, QFrame, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
import requests
import csv
import json

from utilities import fetch_sdss_image

class ImageFetcher(QThread):
    image_fetched = pyqtSignal(int, QPixmap)

    def __init__(self, row_idx, ra, dec, width=64, height=64, scale=0.2):
        super().__init__()
        self.row_idx = row_idx
        self.ra = ra
        self.dec = dec
        self.width = width
        self.height = height
        self.scale = scale

    def run(self):
        # Fetch the SDSS image using the utility function
        image = fetch_sdss_image(self.ra, self.dec, self.scale, self.width, self.height)
        if image:
            # Convert the PIL Image to QPixmap
            qimage = QImage(image.tobytes("raw", "RGB"), image.width, image.height, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            self.image_fetched.emit(self.row_idx, pixmap)

class Search(QWidget):
    def __init__(self, parent_tab_widget):
        super().__init__()
        self.parent_tab_widget = parent_tab_widget
        
        # Keep track of running threads
        self.active_threads = []
        
        self.conditions = []  # Store SQL conditions for the WHERE clause
        self.user_friendly_conditions = [] # Store user-friendly conditions for display

        # Mapping of display names to SQL column names
        self.COLUMN_MAPPING = {
            "Object ID": "p.objid",
            "RA": "p.ra",
            "DEC": "p.dec",
            "u-band": "p.u",
            "g-band": "p.g",
            "r-band": "p.r",
            "i-band": "p.i",
            "z-band": "p.z",
            "Run": "p.run",
            "Rerun": "p.rerun",
            "Camcol": "p.camcol",
            "Field": "p.field",
            "SpecObj ID": "s.specobjid",
            "Class": "s.class",
            "Redshift": "s.z",
            "Plate": "s.plate",
            "MJD": "s.mjd",
            "Fiber ID": "s.fiberid"
        }
        
        self.REVERSE_COLUMN_MAPPING = {v: k for k, v in self.COLUMN_MAPPING.items()}

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)  # Adjust outer margins
        layout.setSpacing(10)  # Reduce vertical spacing

        # Title
        title_label = QLabel("Search SDSS Data")
        title_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold; margin-bottom: 10px;")  # Reduced margin
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Input Section Container
        input_frame = QFrame()
        input_frame.setStyleSheet("background-color: #2E2E2E; border-radius: 10px; padding: 15px;")  # Reduced padding
        input_frame_layout = QVBoxLayout(input_frame)
        input_frame_layout.setAlignment(Qt.AlignCenter)
        input_frame_layout.setSpacing(8)  # Compact spacing between sections
        layout.addWidget(input_frame)

        # Results limit layout
        limit_layout = QHBoxLayout()
        limit_layout.setSpacing(10)
        limit_layout.setContentsMargins(0, 0, 0, 0)

        limit_label = QLabel("Results Limit:")
        limit_label.setStyleSheet("color: white; font-size: 14px;")
        limit_label.setFixedWidth(150)
        limit_layout.addWidget(limit_label)

        self.results_limit_input = QLineEdit()
        self.results_limit_input.setPlaceholderText("10")
        self.results_limit_input.setFixedWidth(60)
        self.results_limit_input.setStyleSheet(
            "padding: 5px; font-size: 14px; color: white; background-color: #3A3A3A; border: 1px solid #5A5A5A;"
        )
        limit_layout.addWidget(self.results_limit_input)

        input_frame_layout.addLayout(limit_layout)

        # Input Fields for Conditions
        condition_container = QFrame()
        condition_container.setStyleSheet("background-color: transparent;")
        condition_container.setFixedWidth(800)

        # Add the horizontal layout to the container
        condition_layout = QHBoxLayout(condition_container)
        condition_layout.setSpacing(5)
        condition_layout.setContentsMargins(0, 0, 0, 0)

        self.fields_dropdown = QComboBox()
        self.fields_dropdown.addItems(list(self.COLUMN_MAPPING.keys()))
        self.fields_dropdown.setStyleSheet("padding: 5px; font-size: 14px; background-color: #3A3A3A; color: white; border: 1px solid #5A5A5A; border-radius: 0;")
        self.fields_dropdown.setFixedHeight(30)
        self.fields_dropdown.setFixedWidth(150)

        self.operators_dropdown = QComboBox()
        self.operators_dropdown.addItems(["=", "BETWEEN", "<", "<=", ">", ">="])
        self.operators_dropdown.setStyleSheet("padding: 5px; font-size: 14px; background-color: #3A3A3A; color: white; border: 1px solid #5A5A5A; border-radius: 0;")
        self.operators_dropdown.setFixedHeight(30)
        self.operators_dropdown.setFixedWidth(120)
        self.operators_dropdown.currentIndexChanged.connect(self.toggle_input_fields)

        # Single input field
        self.single_input = QLineEdit()
        self.single_input.setPlaceholderText("Enter value")
        self.single_input.setStyleSheet("padding: 5px; font-size: 14px; background-color: #3A3A3A; color: white; border: 1px solid #5A5A5A; border-radius: 0;")
        self.single_input.setFixedHeight(30)
        self.single_input.setFixedWidth(150)

        # Range input fields
        self.min_input = QLineEdit()
        self.min_input.setPlaceholderText("Min value")
        self.min_input.setStyleSheet("padding: 5px; font-size: 14px; background-color: #3A3A3A; color: white; border: 1px solid #5A5A5A; border-radius: 0;")
        self.min_input.setFixedHeight(30)
        self.min_input.setFixedWidth(100)

        self.max_input = QLineEdit()
        self.max_input.setPlaceholderText("Max value")
        self.max_input.setStyleSheet("padding: 5px; font-size: 14px; background-color: #3A3A3A; color: white; border: 1px solid #5A5A5A; border-radius: 0;")
        self.max_input.setFixedHeight(30)
        self.max_input.setFixedWidth(100)

        # Add inputs to layout
        self.range_input_layout = QHBoxLayout()
        self.range_input_layout.addWidget(self.min_input)
        self.range_input_layout.addWidget(self.max_input)

        self.min_input.setVisible(False)
        self.max_input.setVisible(False)

        self.add_condition_button = QPushButton("Add Condition")
        self.add_condition_button.setStyleSheet("background-color: #5A9; color: white; font-weight: bold; padding: 5px 10px; border-radius: 0;")
        self.add_condition_button.setFixedHeight(30)
        self.add_condition_button.setFixedWidth(120)
        self.add_condition_button.clicked.connect(self.add_condition)

        condition_layout.addWidget(self.fields_dropdown, 1)
        condition_layout.addWidget(self.operators_dropdown, 1)
        condition_layout.addWidget(self.single_input, 2)
        condition_layout.addLayout(self.range_input_layout, 2)
        condition_layout.addWidget(self.add_condition_button, 1)

        input_frame_layout.addWidget(condition_container)

        # Filters and Reset Button
        filters_reset_container = QFrame()
        filters_reset_container.setStyleSheet("background-color: transparent;")
        filters_reset_container.setFixedWidth(850)  # Maintain the same width as the input section

        filters_reset_layout = QHBoxLayout(filters_reset_container)
        filters_reset_layout.setContentsMargins(0, 0, 0, 0)
        filters_reset_layout.setSpacing(5)

        # Filters label
        self.conditions_display = QLabel("Filters: None")
        self.conditions_display.setStyleSheet("color: white; font-size: 14px; background-color: #3A3A3A; padding: 5px; border-radius: 0;")
        self.conditions_display.setAlignment(Qt.AlignLeft)

        # Add stretch to the Filters label
        filters_reset_layout.addWidget(self.conditions_display, 1)

        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.setStyleSheet("background-color: #5A9; color: white; font-weight: bold; padding: 5px 10px; border-radius: 0;")
        self.reset_button.setFixedHeight(30)
        self.reset_button.setFixedWidth(80)
        self.reset_button.clicked.connect(self.reset_conditions)

        # Add the Reset button
        filters_reset_layout.addWidget(self.reset_button)

        # Add the Filters and Reset container to the input frame
        input_frame_layout.addWidget(filters_reset_container)

        # Search Button
        search_button = QPushButton("Search")
        search_button.setStyleSheet("background-color: #5A9; color: white; font-weight: bold; padding: 10px 20px; border-radius: 0;")
        search_button.setFixedHeight(40)
        search_button.clicked.connect(self.execute_query)
        input_frame_layout.addWidget(search_button)

        # Results Table
        self.results_table = QTableWidget()
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setColumnCount(19)
        self.results_table.setHorizontalHeaderLabels([
            "Image", "Object ID", "RA", "DEC", "u-band", "g-band", "r-band", "i-band", "z-band",
            "Run", "Rerun", "Camcol", "Field", "SpecObj ID", "Class", "Redshift", "Plate", "MJD", "Fiber ID"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setStyleSheet("color: white; font-size: 14px; background-color: #3A3A3A; gridline-color: #5A9;")
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.results_table.setStyleSheet(
            "QHeaderView::section {background-color: #2E2E2E; color: white; font-weight: bold; border: 1px solid #3A3A3A;}"
            "QTableWidget {background-color: #2E2E2E; alternate-background-color: #3A3A3A;}"
            "QTableWidget::item { color: white; }"
        )

        layout.addWidget(self.results_table)
        
        # Export Button
        export_button = QPushButton("Export Results")
        export_button.setStyleSheet("background-color: #5A9; color: white; font-weight: bold; padding: 10px 20px; border-radius: 0;")
        export_button.setFixedHeight(40)
        export_button.clicked.connect(self.export_results)
        layout.addWidget(export_button, alignment=Qt.AlignCenter)

        self.conditions = []  # Store the conditions for the WHERE clause
        self.setLayout(layout)

    def toggle_input_fields(self):
        if self.operators_dropdown.currentText() == "BETWEEN":
            self.single_input.setVisible(False)
            self.min_input.setVisible(True)
            self.max_input.setVisible(True)
        else:
            self.single_input.setVisible(True)
            self.min_input.setVisible(False)
            self.max_input.setVisible(False)

    def add_condition(self):
        field_display = self.fields_dropdown.currentText()
        operator = self.operators_dropdown.currentText()
        field_sql = self.COLUMN_MAPPING[field_display]

        if operator == "BETWEEN":
            min_value = self.min_input.text().strip()
            max_value = self.max_input.text().strip()
            if not min_value or not max_value:
                QMessageBox.warning(self, "Input Error", "Please enter both minimum and maximum values for the range.")
                return
            condition = f"{field_sql} {operator} {min_value} AND {max_value}"
            user_friendly_condition = f"{field_display} {operator} {min_value} AND {max_value}"
        else:
            value = self.single_input.text().strip()
            if not value:
                QMessageBox.warning(self, "Input Error", "Please enter a value for the condition.")
                return
            
            # Add double quotes around the value if the field is 'Class'
            if field_display == "Class":
                value = f'"{value.upper()}"'
                
            condition = f"{field_sql} {operator} {value}"
            user_friendly_condition = f"{field_display} {operator} {value}"

        # Add the SQL condition to the WHERE clause
        self.conditions.append(condition)
        # Add the user-friendly condition for display
        self.user_friendly_conditions.append(user_friendly_condition)
        self.update_conditions_display()

    def reset_conditions(self):
        """Reset all input fields and conditions."""
        self.conditions = []
        self.user_friendly_conditions = []  # Clear the user-friendly conditions
        self.update_conditions_display()
        self.single_input.clear()
        self.min_input.clear()
        self.max_input.clear()
        self.results_limit_input.clear()

    def update_conditions_display(self):
        if self.user_friendly_conditions:
            self.conditions_display.setText("Filters: " + " AND ".join(self.user_friendly_conditions))
        else:
            self.conditions_display.setText("Filters: None")


    def execute_query(self):
        if not self.conditions:
            QMessageBox.warning(self, "Input Error", "Please add at least one condition.")
            return

        where_clause = " AND ".join(self.conditions)
        results_limit = self.results_limit_input.text().strip() or "10"

        query = f"""
        SELECT TOP {results_limit}
            p.objid, p.ra, p.dec, p.u, p.g, p.r, p.i, p.z, 
            p.run, p.rerun, p.camcol, p.field, 
            s.specobjid, s.class, s.z as redshift,
            s.plate, s.mjd, s.fiberid
        FROM PhotoObj AS p
        JOIN SpecObj AS s ON s.bestobjid = p.objid
        WHERE {where_clause}
        """

        url = "http://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
        params = {"cmd": query, "format": "json"}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            # Debugging output
            # print("Query URL:", response.url)
            # print("Status Code:", response.status_code)
            # print("Response Headers:", response.headers)
            # print("Response Text Preview:", response.text[:500])

            data = response.json()
            rows = data[0]['Rows']
            self.populate_results(rows)
        except Exception as e:
            QMessageBox.critical(self, "Query Error", f"Failed to execute query: {e}")

    def populate_results(self, rows):
        if not rows:
            QMessageBox.information(self, "No Results", "No data found for the given query.")
            return

        self.results_table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            # Fetch thumbnails asynchronously for the first column
            ra, dec = row.get("ra"), row.get("dec")
            if ra and dec:
                fetcher = ImageFetcher(row_idx, ra, dec, width=64, height=64, scale=0.2)
                fetcher.image_fetched.connect(self.update_image_cell)
                fetcher.finished.connect(lambda: self.cleanup_thread(fetcher))
                self.active_threads.append(fetcher)
                fetcher.start()

            # Populate table data, starting from the second column
            for col_idx, col_name in enumerate([
                "objid", "ra", "dec", "u", "g", "r", "i", "z",
                "run", "rerun", "camcol", "field", "specobjid",
                "class", "redshift", "plate", "mjd", "fiberid"
            ]):
                value = row.get(col_name, "")
                self.results_table.setItem(row_idx, col_idx + 1, QTableWidgetItem(str(value)))  # Shift by +1 for image column

        self.results_table.resizeRowsToContents()
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def update_image_cell(self, row_idx, pixmap):
        """Update the image cell in the results table and resize the row to fit the image."""
        image_label = QLabel()

        if pixmap:
            image_label.setPixmap(pixmap)
        else:
            # Set a placeholder if the image is unavailable
            placeholder_pixmap = QPixmap(64, 64)
            placeholder_pixmap.fill(Qt.gray)
            image_label.setPixmap(placeholder_pixmap)

        image_label.setAlignment(Qt.AlignCenter)
        self.results_table.setCellWidget(row_idx, 0, image_label)  # Column 0 is for images

        # Resize the row to fit the image
        self.results_table.resizeRowToContents(row_idx)

    def cleanup_thread(self, thread):
        """Remove the thread from active threads after it finishes."""
        if thread in self.active_threads:
            self.active_threads.remove(thread)

    def closeEvent(self, event):
        """Ensure all threads are properly stopped when the widget is closed."""
        for thread in self.active_threads:
            thread.quit()
            thread.wait()  # Wait for the thread to finish
        self.active_threads.clear()
        super().closeEvent(event)

    # New export_results method
    def export_results(self):
        if self.results_table.rowCount() == 0:
            QMessageBox.warning(self, "Export Error", "No results available to export.")
            return

        # Open a file dialog for saving
        options = QFileDialog.Options()
        file_path, file_type = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            "",
            "CSV Files (*.csv);;JSON Files (*.json);;All Files (*)",
            options=options
        )

        if not file_path:
            return  # User canceled the dialog

        # Detect the chosen format
        if file_path.endswith(".csv"):
            self.export_to_csv(file_path)
        elif file_path.endswith(".json"):
            self.export_to_json(file_path)
        else:
            QMessageBox.warning(self, "Export Error", "Unsupported file format. Please choose CSV or JSON.")

    def export_to_csv(self, file_path):
        try:
            with open(file_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                
                # Write headers
                headers = [self.results_table.horizontalHeaderItem(col).text() for col in range(self.results_table.columnCount())]
                writer.writerow(headers)

                # Write table rows
                for row in range(self.results_table.rowCount()):
                    writer.writerow([self.results_table.item(row, col).text() if self.results_table.item(row, col) else "" 
                                     for col in range(self.results_table.columnCount())])

            QMessageBox.information(self, "Export Successful", f"Results exported successfully to {file_path}.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export results to CSV: {e}")

    def export_to_json(self, file_path):
        try:
            results = []
            
            # Get headers
            headers = [self.results_table.horizontalHeaderItem(col).text() for col in range(self.results_table.columnCount())]

            # Collect table data
            for row in range(self.results_table.rowCount()):
                row_data = {headers[col]: self.results_table.item(row, col).text() if self.results_table.item(row, col) else "" 
                            for col in range(self.results_table.columnCount())}
                results.append(row_data)

            # Write to JSON
            with open(file_path, mode="w", encoding="utf-8") as file:
                json.dump(results, file, indent=4)

            QMessageBox.information(self, "Export Successful", f"Results exported successfully to {file_path}.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export results to JSON: {e}")