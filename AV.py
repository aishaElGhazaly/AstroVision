import tkinter as tk
from PIL import Image, ImageTk
import requests
from io import BytesIO

# Function to fetch SDSS image based on RA and DEC (updated for DR18)
def fetch_sdss_image(ra, dec, scale=0.2, width=512, height=512):
    # SDSS DR18 cutout service URL
    url = f"https://skyserver.sdss.org/dr18/SkyServerWS/ImgCutout/getjpeg?ra={ra}&dec={dec}&scale={scale}&width={width}&height={height}"
    response = requests.get(url)
    
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        return image
    else:
        print("Failed to fetch image.")
        return None

# Function to display the image in the label
def display_image():
    # Get the RA and DEC from the input fields
    ra = ra_entry.get()
    dec = dec_entry.get()
    
    try:
        ra = float(ra)
        dec = float(dec)
    except ValueError:
        print("Please enter valid numerical values for RA and DEC.")
        return
    
    # Fetch and display the image
    image = fetch_sdss_image(ra, dec)
    if image:
        # Convert image to Tkinter-compatible format
        tk_image = ImageTk.PhotoImage(image)
        image_label.config(image=tk_image)
        image_label.image = tk_image  # Keep a reference to avoid garbage collection

# Initialize the main window
root = tk.Tk()
root.title("SDSS Image Viewer - DR18")

# RA input field
tk.Label(root, text="RA:").grid(row=0, column=0, padx=5, pady=5)
ra_entry = tk.Entry(root)
ra_entry.grid(row=0, column=1, padx=5, pady=5)

# DEC input field
tk.Label(root, text="DEC:").grid(row=1, column=0, padx=5, pady=5)
dec_entry = tk.Entry(root)
dec_entry.grid(row=1, column=1, padx=5, pady=5)

# Fetch button
fetch_button = tk.Button(root, text="Fetch Image", command=display_image)
fetch_button.grid(row=2, column=0, columnspan=2, pady=10)

# Image display label
image_label = tk.Label(root)
image_label.grid(row=3, column=0, columnspan=2)

# Start the Tkinter event loop
root.mainloop()