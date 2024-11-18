import sys
import os
import requests
from PIL import Image
from io import BytesIO
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton


# Function to fetch SDSS image based on RA and DEC (updated for DR18)
def fetch_sdss_image(ra, dec, scale=0.2, width=512, height=512):
    url = f"https://skyserver.sdss.org/dr18/SkyServerWS/ImgCutout/getjpeg?ra={ra}&dec={dec}&scale={scale}&width={width}&height={height}"
    response = requests.get(url)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        print("Failed to fetch image.")
        return None


# Function to get SDSS object ID based on RA and DEC
def get_object_id(ra, dec):
    url = "http://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
    query = f"""
    SELECT TOP 1 objID
    FROM PhotoObj
    WHERE RA BETWEEN {ra} - 0.0001 AND {ra} + 0.0001
    AND DEC BETWEEN {dec} - 0.0001 AND {dec} + 0.0001
    """
    params = {"cmd": query, "format": "json"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        try:
            return data[0]['Rows'][0]['objID']
        except (IndexError, KeyError):
            print("No objID found.")
            return None
    else:
        print(f"Error: {response.status_code}")
        return None


# Function to fetch run-camcol-field identifier based on RA and DEC
def get_run_camcol_field(ra, dec):
    url = "http://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
    query = f"""
    SELECT TOP 1 run, camcol, field
    FROM PhotoObj
    WHERE RA BETWEEN {ra} - 0.0001 AND {ra} + 0.0001
    AND DEC BETWEEN {dec} - 0.0001 AND {dec} + 0.0001
    """
    params = {"cmd": query, "format": "json"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        try:
            row = data[0]['Rows'][0]
            return f"{row['run']}-{row['camcol']}-{row['field']}"
        except (IndexError, KeyError):
            print("No run-camcol-field identifier found.")
            return None
    else:
        print(f"Error: {response.status_code}")
        return None

# Function to get FITS file URLs for all filters based on run-camcol-field
def get_fits_files(run_camcol_field):
    try:
        # Parse the run-camcol-field string
        run, camcol, field = run_camcol_field.split("-")
        
        # Base URL for FITS files
        base_url = "https://dr18.sdss.org/sas/dr18/prior-surveys/sdss4-dr17-eboss/photoObj/frames/301"
        
        # Filters to download
        filters = ['u', 'g', 'r', 'i', 'z']
        
        # Construct URLs for each filter
        fits_urls = [
            f"{base_url}/{run}/{camcol}/frame-{flt}-{run.zfill(6)}-{camcol}-{field.zfill(4)}.fits.bz2"
            for flt in filters
        ]
        return fits_urls
    except ValueError:
        print("Invalid run-camcol-field format.")
        return []


# Function to download FITS files
def download_fits_files(run_camcol_field):
    directory = run_camcol_field
    if not os.path.exists(directory):
        os.makedirs(directory)

    fits_files = get_fits_files(run_camcol_field)

    for fits_url in fits_files:
        print(f"Attempting to download: {fits_url}")
        try:
            response = requests.get(fits_url, stream=True)
            if response.status_code == 200:
                file_name = fits_url.split("/")[-1]
                file_path = os.path.join(directory, file_name)
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=5 * 1024 * 1024):
                        f.write(chunk)
                print(f"Downloaded: {file_name}")
            else:
                print(f"Failed to download {fits_url} - HTTP {response.status_code}")
        except Exception as e:
            print(f"Error downloading {fits_url}: {e}")

# SDSS Image Viewer Application
class SDSSImageViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDSS Image Viewer - DR18")

        self.setStyleSheet("""
        QWidget { background-color: #2e2e2e; color: white; }
        QLabel { color: white; }
        QLineEdit { background-color: #555555; color: white; border: 1px solid #444444; padding: 5px; }
        QPushButton { background-color: #444444; color: white; border: 1px solid #333333; padding: 5px; }
        QPushButton:hover { background-color: #666666; }
        """)
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        input_layout = QHBoxLayout()
        ra_label = QLabel("RA (deg):")
        self.ra_entry = QLineEdit()
        self.ra_entry.setFixedWidth(80)
        dec_label = QLabel("DEC (deg):")
        self.dec_entry = QLineEdit()
        self.dec_entry.setFixedWidth(80)

        input_layout.addStretch(1)
        input_layout.addWidget(ra_label)
        input_layout.addWidget(self.ra_entry)
        input_layout.addWidget(dec_label)
        input_layout.addWidget(self.dec_entry)
        input_layout.addStretch(1)

        main_layout.addLayout(input_layout)

        button_layout = QHBoxLayout()
        self.fetch_button = QPushButton("Fetch Image")
        self.fetch_button.clicked.connect(self.display_image)
        button_layout.addStretch(1)
        button_layout.addWidget(self.fetch_button)
        button_layout.addStretch(1)

        main_layout.addLayout(button_layout)

        self.obj_id_label = QLabel("")
        self.obj_id_label.setAlignment(Qt.AlignCenter)
        self.obj_id_label.setVisible(False)

        self.run_camcol_field_label = QLabel("")
        self.run_camcol_field_label.setAlignment(Qt.AlignCenter)
        self.run_camcol_field_label.setVisible(False)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setVisible(False)

        main_layout.addWidget(self.obj_id_label)
        main_layout.addWidget(self.run_camcol_field_label)
        main_layout.addWidget(self.image_label)

        self.setLayout(main_layout)

    def display_image(self):
        try:
            ra = float(self.ra_entry.text())
            dec = float(self.dec_entry.text())
        except ValueError:
            print("Please enter valid numerical values for RA and DEC.")
            return

        image = fetch_sdss_image(ra, dec)
        if image:
            obj_id = get_object_id(ra, dec)
            run_camcol_field = get_run_camcol_field(ra, dec)

            if obj_id:
                self.obj_id_label.setText(f"Object ID: {obj_id}")
                self.obj_id_label.setVisible(True)
            else:
                self.obj_id_label.setText("Object ID: Not found")
                self.obj_id_label.setVisible(True)

            if run_camcol_field:
                self.run_camcol_field_label.setText(f"Run-Camcol-Field: {run_camcol_field}")
                self.run_camcol_field_label.setVisible(True)
                download_fits_files(run_camcol_field)
            else:
                self.run_camcol_field_label.setText("Run-Camcol-Field: Not found")
                self.run_camcol_field_label.setVisible(True)

            image = image.convert("RGB")
            data = image.tobytes("raw", "RGB")
            qimage = QImage(data, image.width, image.height, image.width * 3, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)

            self.image_label.setPixmap(pixmap.scaled(512, 512, Qt.KeepAspectRatio))
            self.image_label.setVisible(True)
        else:
            self.obj_id_label.setText("Object ID: Not found")
            self.obj_id_label.setVisible(True)
            self.run_camcol_field_label.setText("Run-Camcol-Field: Not found")
            self.run_camcol_field_label.setVisible(True)
            self.image_label.clear()
            self.image_label.setVisible(False)


def main():
    app = QApplication(sys.argv)
    viewer = SDSSImageViewer()
    viewer.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()