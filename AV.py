import threading
import sys
import os
import requests
import bz2
import shutil
from PIL import Image
from io import BytesIO
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton

# Function to fetch SDSS image based on RA and DEC
def fetch_sdss_image(ra, dec, scale=0.2, width=2048, height=1489):
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


# Function to fetch run-camcol-field identifier
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


# Function to get FITS file URLs
def get_fits_files(run_camcol_field):
    try:
        run, camcol, field = run_camcol_field.split("-")
        base_url = "https://dr18.sdss.org/sas/dr18/prior-surveys/sdss4-dr17-eboss/photoObj/frames/301"
        filters = ['u', 'g', 'r', 'i', 'z']
        fits_urls = [
            f"{base_url}/{run}/{camcol}/frame-{flt}-{run.zfill(6)}-{camcol}-{field.zfill(4)}.fits.bz2"
            for flt in filters
        ]
        return fits_urls
    except ValueError:
        print("Invalid run-camcol-field format.")
        return []

# Function to download and decompress FITS files
def download_fits_files(run_camcol_field, callback=None):
    directory = run_camcol_field
    if not os.path.exists(directory):
        os.makedirs(directory)

    fits_files = get_fits_files(run_camcol_field)  # This should return a list of URLs

    for fits_url in fits_files:
        try:
            # Download the compressed file
            response = requests.get(fits_url, stream=True)
            if response.status_code == 200:
                compressed_file_name = fits_url.split("/")[-1]
                decompressed_file_name = compressed_file_name.replace(".bz2", "")
                file_path = os.path.join(directory, decompressed_file_name)

                # Decompress and write directly to file
                with bz2.BZ2File(response.raw, 'rb') as compressed_stream, open(file_path, 'wb') as decompressed_file:
                    shutil.copyfileobj(compressed_stream, decompressed_file)

                print(f"Downloaded and decompressed: {decompressed_file_name}")
            else:
                print(f"Failed to download {fits_url} - HTTP {response.status_code}")
        except Exception as e:
            print(f"Error downloading {fits_url}: {e}")

    if callback:
        callback()

# Thread class for FITS download
class FITSDownloadThread(QThread):
    finished_signal = pyqtSignal()

    def __init__(self, run_camcol_field):
        super().__init__()
        self.run_camcol_field = run_camcol_field

    def run(self):
        download_fits_files(self.run_camcol_field)
        self.finished_signal.emit()

# SDSS Image Viewer Application
class SDSSImageViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDSS Image Viewer - DR18")

        self.initUI()
        self.download_thread = None

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
        self.run_camcol_field_label = QLabel("")
        self.run_camcol_field_label.setAlignment(Qt.AlignCenter)
        self.image_label = QLabel("")
        self.image_label.setAlignment(Qt.AlignCenter)

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

            self.obj_id_label.setText(f"Object ID: {obj_id or 'Not found'}")
            self.run_camcol_field_label.setText(f"Run-Camcol-Field: {run_camcol_field or 'Not found'}")

            image = image.convert("RGB")
            data = image.tobytes("raw", "RGB")
            qimage = QImage(data, image.width, image.height, image.width * 3, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            self.image_label.setPixmap(pixmap.scaled(512, 512, Qt.KeepAspectRatio))

            if run_camcol_field:
                self.start_download(run_camcol_field)

    def start_download(self, run_camcol_field):
        self.download_thread = FITSDownloadThread(run_camcol_field)
        self.download_thread.finished_signal.connect(self.download_finished)
        self.download_thread.start()

    def download_finished(self):
        print("FITS file download completed.")

def main():
    app = QApplication(sys.argv)
    viewer = SDSSImageViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()