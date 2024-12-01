import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits

# File paths for the FITS files corresponding to the filters
fits_file_paths = {
    'u': '3918-3-213/frame-u-003918-3-0213.fits',
    'g': '3918-3-213/frame-g-003918-3-0213.fits',
    'r': '3918-3-213/frame-r-003918-3-0213.fits',
    'i': '3918-3-213/frame-i-003918-3-0213.fits',
    'z': '3918-3-213/frame-z-003918-3-0213.fits'
}

# Initialize a figure for subplots
plt.figure(figsize=(15, 10))

# Iterate through the filters and their file paths
for idx, (filter_name, fits_file_path) in enumerate(fits_file_paths.items()):
    # Open the FITS file and extract the image data
    with fits.open(fits_file_path) as hdul:
        primary_data = hdul[0].data

    # Apply a logarithmic stretch for better visualization
    log_image = np.log(primary_data + 1)  # Avoid log(0) by adding 1
    normalized_log_image = (log_image - np.min(log_image)) / (np.max(log_image) - np.min(log_image))
    
    # Add a subplot for the current filter
    plt.subplot(2, 3, idx + 1)  # Arrange in a 2x3 grid
    plt.imshow(normalized_log_image, cmap='gray', origin='lower')
    plt.colorbar()
    plt.title(f'Filter: {filter_name}')
    plt.axis('off')  # Hide axis for cleaner visualization

# Adjust layout and display the figure
plt.tight_layout()
plt.suptitle('FITS Images for Different Filters', fontsize=16)
plt.subplots_adjust(top=0.9)  # Leave space for the suptitle
plt.show()