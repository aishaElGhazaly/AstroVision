import os
import requests
import bz2
import shutil
from PIL import Image
from io import BytesIO


# Function to validate RA/DEC input
def validate_ra_dec(ra, dec):
    """
    Validate RA (0 to 360) and DEC (-90 to 90) values.
    """
    try:
        ra = float(ra)
        dec = float(dec)
        return 0 <= ra <= 360 and -90 <= dec <= 90
    except ValueError:
        return False


# Function to fetch SDSS image based on RA and DEC
def fetch_sdss_image(ra, dec, scale=0.2, width=2048, height=1489):
    """
    Fetch SDSS image cutout based on RA and DEC.
    """
    url = f"https://skyserver.sdss.org/dr18/SkyServerWS/ImgCutout/getjpeg?ra={ra}&dec={dec}&scale={scale}&width={width}&height={height}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Error fetching image: {e}")
        return None


# Function to get SDSS object ID based on RA and DEC
def get_object_id(ra, dec):
    """
    Query SDSS Object ID based on RA and DEC.
    """
    url = "http://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
    query = f"""
    SELECT TOP 1 objID
    FROM PhotoObj
    WHERE RA BETWEEN {ra} - 0.001 AND {ra} + 0.001
    AND DEC BETWEEN {dec} - 0.001 AND {dec} + 0.001
    """
    params = {"cmd": query, "format": "json"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data[0]['Rows'][0]['objID']
    except (IndexError, KeyError):
        print("No objID found for the given RA/DEC.")
    except Exception as e:
        print(f"Error querying Object ID: {e}")
    return None


# Function to fetch object details based on Object ID
def get_object_details(object_id):
    """
    Fetch RA, DEC, magnitudes [u, g, r, i, z], and type for a given Object ID.
    """
    url = "http://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
    query = f"""
    SELECT TOP 1 ra, dec, u, g, r, i, z, type
    FROM PhotoObj
    WHERE objID = {object_id}
    """
    params = {"cmd": query, "format": "json"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        row = data[0]['Rows'][0]
        return {
            "ra": row["ra"],
            "dec": row["dec"],
            "u": row["u"],
            "g": row["g"],
            "r": row["r"],
            "i": row["i"],
            "z": row["z"],
            "type": get_object_type(row["type"]),
        }
    except (IndexError, KeyError):
        print("No data found for the given Object ID.")
    except Exception as e:
        print(f"Error fetching object details: {e}")
    return None


# Function to map SDSS type values to descriptions
def get_object_type(type_value):
    """
    Map SDSS PhotoType values to their descriptions.
    """
    type_mapping = {
        0: "Unknown",
        1: "Cosmic ray",
        2: "Defect",
        3: "Galaxy",
        4: "Ghost",
        5: "Known object",
        6: "Star",
        7: "Trail",
        8: "Sky",
        9: "Not a type",
    }
    return type_mapping.get(type_value, "Invalid type")


# Function to query Run-Camcol-Field from RA/DEC
def query_run_camcol_field(ra, dec):
    """
    Query Run-Camcol-Field from RA/DEC coordinates.
    """
    url = "http://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
    query = f"""
    SELECT TOP 1 run, camcol, field
    FROM PhotoObj
    WHERE RA BETWEEN {ra} - 0.0001 AND {ra} + 0.0001
    AND DEC BETWEEN {dec} - 0.0001 AND {dec} + 0.0001
    """
    params = {"cmd": query, "format": "json"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        row = data[0]['Rows'][0]
        return f"{row['run']}-{row['camcol']}-{row['field']}"
    except (IndexError, KeyError):
        print("No Run-Camcol-Field found for the given RA/DEC.")
    except Exception as e:
        print(f"Error querying Run-Camcol-Field: {e}")
    return None


# Function to fetch Run-Camcol-Field components
def get_run_camcol_field(ra, dec):
    """
    Fetch Run, Camcol, and Field individually based on RA and DEC.
    """
    url = "http://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
    query = f"""
    SELECT TOP 1 run, camcol, field
    FROM PhotoObj
    WHERE RA BETWEEN {ra} - 0.0001 AND {ra} + 0.0001
    AND DEC BETWEEN {dec} - 0.0001 AND {dec} + 0.0001
    """
    params = {"cmd": query, "format": "json"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        row = data[0]['Rows'][0]
        return row["run"], row["camcol"], row["field"]
    except (IndexError, KeyError):
        print("No Run-Camcol-Field components found for the given RA/DEC.")
    except Exception as e:
        print(f"Error fetching Run-Camcol-Field components: {e}")
    return None, None, None


# Function to get FITS file URLs
def get_fits_urls(run_camcol_field, bands):
    """
    Generate URLs for FITS files based on Run-Camcol-Field and selected bands.
    """
    try:
        run, camcol, field = run_camcol_field.split("-")
        base_url = "https://dr18.sdss.org/sas/dr18/prior-surveys/sdss4-dr17-eboss/photoObj/frames/301"
        fits_urls = [
            f"{base_url}/{run}/{camcol}/frame-{band}-{run.zfill(6)}-{camcol}-{field.zfill(4)}.fits.bz2"
            for band in bands
        ]
        return fits_urls
    except ValueError:
        print("Invalid Run-Camcol-Field format.")
        return []


# Function to download and decompress FITS files
def download_fits_files(run_camcol_field, bands, progress_callback=None):
    """
    Download and decompress FITS files for specified bands.
    """
    directory = run_camcol_field
    if not os.path.exists(directory):
        os.makedirs(directory)

    fits_urls = get_fits_urls(run_camcol_field, bands)
    total_files = len(fits_urls)

    for index, fits_url in enumerate(fits_urls, start=1):
        try:
            response = requests.get(fits_url, stream=True)
            if response.status_code == 200:
                compressed_file_name = fits_url.split("/")[-1]
                decompressed_file_name = compressed_file_name.replace(".bz2", "")
                file_path = os.path.join(directory, decompressed_file_name)

                with open(compressed_file_name, 'wb') as compressed_file:
                    compressed_file.write(response.content)

                with bz2.BZ2File(compressed_file_name, 'rb') as compressed_stream, open(file_path, 'wb') as decompressed_file:
                    shutil.copyfileobj(compressed_stream, decompressed_file)

                os.remove(compressed_file_name)

                # Update progress if callback provided
                if progress_callback:
                    progress_callback(int(index / total_files * 100))
            else:
                print(f"Failed to download {fits_url} - HTTP {response.status_code}")
        except Exception as e:
            print(f"Error downloading {fits_url}: {e}")
