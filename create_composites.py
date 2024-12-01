from astropy.io import fits
from astropy.wcs import WCS
from reproject import reproject_interp  # Install this: pip install reproject
from astropy.visualization import make_lupton_rgb
import numpy as np
import matplotlib.pyplot as plt

# File paths for all filters
file_paths = {
    'u': "3918-3-213/frame-u-003918-3-0213.fits",
    'g': "3918-3-213/frame-g-003918-3-0213.fits",
    'r': "3918-3-213/frame-r-003918-3-0213.fits",
    'i': "3918-3-213/frame-i-003918-3-0213.fits",
    'z': "3918-3-213/frame-z-003918-3-0213.fits"
}

# Step 1: Load the reference image (e.g., 'r' filter)
reference_filter = 'r'
reference_hdulist = fits.open(file_paths[reference_filter])
reference_header = reference_hdulist[0].header
reference_data = reference_hdulist[0].data
reference_wcs = WCS(reference_header)

# Create an empty dictionary to store reprojected data
aligned_images = {}

# Step 2: Reproject all filters onto the reference grid
for filter_name, file_path in file_paths.items():
    print(f"Processing filter: {filter_name}")
    hdulist = fits.open(file_path)
    data = hdulist[0].data
    header = hdulist[0].header
    wcs = WCS(header)

    # Reproject the image onto the reference WCS
    reprojected_data, footprint = reproject_interp(
        (data, wcs),  # Input image and WCS
        reference_wcs,  # Target WCS
        shape_out=reference_data.shape  # Output shape (same as reference)
    )
    
    # Store the aligned image
    aligned_images[filter_name] = np.nan_to_num(reprojected_data, nan=0.0)  # Handle NaNs

# Close reference FITS file
reference_hdulist.close()

# Step 3: Create a Lupton RGB Composite using Astropy
# Select the aligned 'g', 'r', 'u' filters for RGB
aligned_r = aligned_images['i']
aligned_g = aligned_images['r']
aligned_b = aligned_images['g']

# Generate the RGB image using make_lupton_rgb
rgb_image = make_lupton_rgb(aligned_r, aligned_g, aligned_b, stretch=0.5, Q=10)

# Step 4: Display the result
plt.imshow(rgb_image, origin='lower')
plt.axis('off')
plt.title("Lupton RGB Composite")
plt.show()
