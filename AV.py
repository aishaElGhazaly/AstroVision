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

# Function to get SDSS object ID based on RA and DEC
def get_sdss_obj_id(ra, dec):
    # Define the base URL for SDSS SQL Search
    url = "http://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
    
    # Define the query with your parameters
    query = f"""
    SELECT TOP 1 objID
    FROM PhotoObj
    WHERE RA BETWEEN {ra} - 0.0001 AND {ra} + 0.0001
    AND DEC BETWEEN {dec} - 0.0001 AND {dec} + 0.0001
    """

    # Parameters for the HTTP request
    params = {
        "cmd": query,
        "format": "json"
    }
    
    # Send the HTTP request
    response = requests.get(url, params=params)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        
        # Access objID using your desired one-liner
        try:
            obj_id = data[0]['Rows'][0]['objID']
            return obj_id
        except (IndexError, KeyError):
            print("No objID found or invalid response format.")
            return None
        
    else:
        print(f"Error: {response.status_code}")
        return None


# Function to get detailed information of an object based on objID
def get_object_info(obj_id):
    # Define the base URL for SDSS SQL Search
    url = "http://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
    
    # Define the query to fetch details for the object based on objID
    query = f"""
    SELECT *
    FROM PhotoObj
    WHERE objID = {obj_id}
    """
    
    # Parameters for the HTTP request
    params = {
        "cmd": query,
        "format": "json"
    }
    
    # Send the HTTP request
    response = requests.get(url, params=params)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        
        print(data)


# Function to display the image and object ID in the label
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
        # Fetch the SDSS object ID
        obj_id = get_sdss_obj_id(ra, dec)
        
        get_object_info(obj_id)
        
        # Display the object ID only if the image is fetched successfully
        if obj_id:
            obj_id_label.config(text=f"Object ID: {obj_id}")
        else:
            obj_id_label.config(text="Object ID: Not found")
        
        # Display the image
        tk_image = ImageTk.PhotoImage(image)
        image_label.config(image=tk_image)
        image_label.image = tk_image  # Keep a reference to avoid garbage collection
        
        # Show the object ID label
        obj_id_label.grid(row=3, column=0, columnspan=2, pady=5)
    else:
        obj_id_label.config(text="Object ID: Not found")
        obj_id_label.grid_forget()  # Hide the object ID label if image fetch fails

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

# Object ID display label (initially hidden)
obj_id_label = tk.Label(root, text="Object ID: ")
obj_id_label.grid_forget()  # Hide the label initially

# Image display label
image_label = tk.Label(root)
image_label.grid(row=4, column=0, columnspan=2)

# Start the Tkinter event loop
root.mainloop()