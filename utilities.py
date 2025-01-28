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


def get_object_details(object_id):
    """
    Fetch RA, DEC, magnitudes [u, g, r, i, z], SpecObj ID, redshift, and class for a given Object ID.
    """
    # Query for photometric data from PhotoObj
    photo_query = f"""
    SELECT TOP 1 ra, dec, u, g, r, i, z
    FROM PhotoObj
    WHERE objID = {object_id}
    """
    # Query for spectroscopic data from SpecObj
    spec_query = f"""
    SELECT TOP 1 specObjID, z, class
    FROM SpecObj
    WHERE bestObjID = {object_id}
    """
    try:
        # Fetch data from PhotoObj
        photo_response = requests.get(
            "http://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch",
            params={"cmd": photo_query, "format": "json"}
        )
        photo_response.raise_for_status()
        photo_data = photo_response.json()
        photo_row = photo_data[0]["Rows"][0]

        # Fetch data from SpecObj
        spec_response = requests.get(
            "http://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch",
            params={"cmd": spec_query, "format": "json"}
        )
        spec_response.raise_for_status()
        spec_data = spec_response.json()
        spec_row = spec_data[0]["Rows"][0]

        # Combine data from both queries
        object_details = {
            "ra": photo_row["ra"],
            "dec": photo_row["dec"],
            "u": photo_row["u"],
            "g": photo_row["g"],
            "r": photo_row["r"],
            "i": photo_row["i"],
            "z": photo_row["z"],
            "specObjID": spec_row["specObjID"],
            "redshift": spec_row["z"],
            "class": spec_row["class"],  # Star, Galaxy, Quasar
        }
        return object_details

    except (IndexError, KeyError):
        print("No data found for the given Object ID.")
    except Exception as e:
        print(f"Error fetching object details: {e}")
    return None


# Function to get SpecObjID based on RA and DEC
def get_specobj_id_coords(ra, dec):
    """
    Query SDSS SpecObjID based on RA and DEC coordinates.
    
    Parameters:
        ra (float): Right Ascension in degrees.
        dec (float): Declination in degrees.

    Returns:
        int: The SpecObjID if found, or None if no match is found.
    """
    url = "http://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
    query = f"""
    SELECT TOP 1 specObjID
    FROM SpecObj
    WHERE RA BETWEEN {ra} - 0.001 AND {ra} + 0.001
      AND DEC BETWEEN {dec} - 0.001 AND {dec} + 0.001
    """
    params = {"cmd": query, "format": "json"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data[0]['Rows'][0]['specObjID']
    except (IndexError, KeyError):
        print("No SpecObjID found for the given RA/DEC.")
    except Exception as e:
        print(f"Error querying SpecObjID by coordinates: {e}")
    return None


# Function to get SpecObjID based on Plate, MJD, and FiberID
def get_specobj_id_pmf(plate, mjd, fiberid):
    """
    Query SDSS SpecObjID based on Plate, MJD, and FiberID.
    
    Parameters:
        plate (int): Plate number of the observation.
        mjd (int): Modified Julian Date of the observation.
        fiberid (int): Fiber ID of the observation.

    Returns:
        int: The SpecObjID if found, or None if no match is found.
    """
    url = "http://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
    query = f"""
    SELECT TOP 1 specObjID
    FROM SpecObj
    WHERE plate = {plate} AND mjd = {mjd} AND fiberID = {fiberid}
    """
    params = {"cmd": query, "format": "json"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data[0]['Rows'][0]['specObjID']
    except (IndexError, KeyError):
        print("No SpecObjID found for the given Plate-MJD-FiberID.")
    except Exception as e:
        print(f"Error querying SpecObjID by plate: {e}")
    return None


# Function to fetch detailed metadata for a given SpecObjID
def get_specobj_details(specobj_id):
    """
    Fetch detailed metadata for an object from the SDSS SpecObj table based on SpecObjID.
    
    Parameters:
        specobj_id (int): The unique SpecObjID of the object.

    Returns:
        dict: A dictionary containing object details (e.g., class, subclass, redshift) if found,
              or None if no details are available.
    """
    url = "http://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
    query = f"""
    SELECT TOP 1
        specObjID,
        class,
        subclass,
        z,
        zErr,
        ra,
        dec,
        mjd,
        plate,
        fiberID
    FROM SpecObj
    WHERE specObjID = {specobj_id}
    """
    params = {"cmd": query, "format": "json"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "Rows" in data[0] and len(data[0]["Rows"]) > 0:
            row = data[0]["Rows"][0]
            return {
                "specObjID": row["specObjID"],
                "class": row["class"],
                "subclass": row.get("subclass", None),
                "redshift": row["z"],
                "redshift_error": row["zErr"],
                "ra": row["ra"],
                "dec": row["dec"],
                "mjd": row["mjd"],
                "plate": row["plate"],
                "fiberID": row["fiberID"]
            }
        else:
            print("No metadata found for the given SpecObjID.")
            return None
    except Exception as e:
        print(f"Error fetching object metadata: {e}")
        return None
    

# Function to fetch Run, Camcol, Field, and Rerun components
def get_run_rerun_camcol_field(ra, dec):
    """
    Fetch Run, Rerun, Camcol, and Field individually based on RA and DEC.
    """
    url = "http://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
    query = f"""
    SELECT TOP 1 run, rerun, camcol, field
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
        return row["run"], row["rerun"], row["camcol"], row["field"]
    except (IndexError, KeyError):
        print("No Run-Camcol-Field components found for the given RA/DEC.")
    except Exception as e:
        print(f"Error fetching Run-Camcol-Field components: {e}")
    return None, None, None, None


# Function to query Run-Camcol-Field from RA/DEC
def query_run_camcol_field(ra, dec):
    """
    Query Run-Camcol-Field, from RA/DEC coordinates.
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


# Function to query Run-Camcol-Field from RA/DEC
def query_run_rerun_camcol_field(ra, dec):
    """
    Query Run-Rerun-Camcol-Field, from RA/DEC coordinates.
    """
    url = "http://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
    query = f"""
    SELECT TOP 1 run, rerun, camcol, field
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
        return f"{row['run']}-{row['rerun']}-{row['camcol']}-{row['field']}"
    except (IndexError, KeyError):
        print("No Run-Camcol-Field found for the given RA/DEC.")
    except Exception as e:
        print(f"Error querying Run-Camcol-Field: {e}")
    return None


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

# Function to fetch Plate, MJD, and Fiber based on RA/DEC
def get_plate_mjd_fiber(ra, dec):
    """
    Fetch Plate, MJD, and FiberID based on RA and DEC.
    """
    url = "http://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
    query = f"""
    SELECT TOP 1 plate, mjd, fiberID
    FROM SpecObj
    WHERE RA BETWEEN {ra} - 0.001 AND {ra} + 0.001
    AND DEC BETWEEN {dec} - 0.001 AND {dec} + 0.001
    """
    params = {"cmd": query, "format": "json"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        row = data[0]['Rows'][0]
        return row['plate'], row['mjd'], row['fiberID']
    except (IndexError, KeyError):
        print("No Plate-MJD-Fiber found for the given RA/DEC.")
    except Exception as e:
        print(f"Error fetching Plate-MJD-Fiber: {e}")
    return None, None, None


# Function to fetch spectrum based on Plate, MJD, and Fiber
def fetch_spectrum_file(plate, mjd, fiber):
    """
    Fetch spectrum data given Plate, MJD, and FiberID using DR18.
    """
    url = f"https://dr18.sdss.org/sas/dr18/spectro/sdss/redux/26/spectra/lite/{plate}/spec-{plate}-{mjd}-{fiber:04d}.fits"
    file_name = f"spec-{plate}-{mjd}-{fiber:04d}.fits"
    try:
        # Check if the file already exists
        if os.path.exists(file_name):
            print(f"File '{file_name}' already exists. Skipping download.")
            return file_name  # Return the existing file path

        # Download the spectrum file
        response = requests.get(url)
        response.raise_for_status()

        # Save the file
        with open(file_name, "wb") as f:
            f.write(response.content)
        return file_name
    except Exception as e:
        print(f"Error fetching spectrum data: {e}")
        return None