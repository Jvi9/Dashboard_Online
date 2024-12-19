import time
import os, glob
import pandas as pd
import piexif
from PIL import Image
import warnings
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import simplekml
import plotly.express as px
import json

import re

# =============================================================================
# Initialization, look at the directories carefully
# =============================================================================
dashboard_directory = r'C:\Users\Jhon\Desktop\test_Z007_replicaserver'
log_directory = r'C:\Users\Jhon\Desktop\test_Z007_replicaserver\logs'
canon_directory=r'C:\Users\Jhon\Desktop\test_Z007_replicaserver\CANON_PHOTOS'
flir_directory=r'C:\Users\Jhon\Desktop\test_Z007_replicaserver\FLIR_PHOTOS'
output_directory=r'C:\Users\Jhon\Desktop\test_Z007_replicaserver'
file_pattern = os.path.join(log_directory, '*.txt')
Fligth_name = 'Z007'  # IMPORTANT!!!!

# Use glob to get all .txt files
txt_files = glob.glob(file_pattern)
log_path = txt_files[-1]

# =============================================================================
# Functions defined for the creation of raw databases
# =============================================================================
# Data initialization
def initialize_files():
    # Define the column headers for each file
    file_definitions = {
        'db_photoflir.txt': ['timestamp', 'image', 'latitude', 'longitude', 'altitude'],
        'db_photocanon.txt': ['timestamp', 'image', 'latitude', 'longitude', 'altitude'],
        'db_balloon_gps.txt': ['timestamp', 'latitude', 'longitude', 'altitude', 'speed'],
        'db_balloon_traj.txt': ['timestamp', 'yaw', 'pitch'],
        'db_microloon.txt': ['timestamp','cpu','altitude','heading', 'course', 'uptime', 'transponder_state', 'flasher_state', 
                'kiwi_roll', 'kiwi_pitch', 'kiwi_yaw', 'temp', 'therm_1', 'therm_2', 'therm_3', 'therm_4', 
                'five_volt_state', 'five_v_voltage', 'five_v_current', 'twentyfour_v_voltage', 
                'twentyfour_v_current', 'yaw', 'pitch', 'gimbal_state', 'total_degrees_moved_pitch', 
                'total_degrees_moved_yaw', 'rail_current_state_5v', 'rail_current_state_8v' ],
        'db_postcanon.txt': ['Image', 'Name','Latitude','Longitude',
                             'Altitude','Captured', 'Date','flight_ID','Time'],
        'db_desired.txt': ['timestamp', 'heading','position','alt',
                           	'desired_gumball_yaw','desired_gumball_pitch','poi']# Adjust these columns as per your microloon data
    }
    for filename, columns in file_definitions.items():
        filepath = os.path.join(output_directory, filename).replace(os.sep, '/')
        # If the file doesn't exist, create it with headers
        if not os.path.exists(filepath):
            df = pd.DataFrame(columns=columns)
            df.to_csv(filepath, sep='\t', index=False, header=True, mode='w')
def initialize_empty_plot():
    # Create an empty DataFrame with the expected columns
    empty_df = pd.DataFrame(columns=['Total_Seconds', 'Altitude'])

    # Create an empty figure with placeholder titles using the empty DataFrame
    fig = px.line(empty_df, x='Total_Seconds', y='Altitude', title="Altitude vs Time",
                  labels={'Total_Seconds': 'Time (secs)', 'Altitude': 'Altitude (m)'})

    # Update layout for responsiveness and placeholder appearance
    fig.update_layout(
        title={
            'text': "Altitude vs Time (No Data Available)",
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 16},
        },
        xaxis=dict(
            title="Time",
            tickvals=[],
            ticktext=[],
            showgrid=True,
            zeroline=True,
        ),
        yaxis=dict(
            title="Altitude (m)",
            showgrid=True,
            zeroline=True,
        ),
        margin=dict(l=20, r=20, t=50, b=50),
        template="plotly_white",
        autosize=True,
    )

    # Save the empty figure as a responsive HTML
    output_path = os.path.join(output_directory, 'altitude_vs_time_plot.html')
    fig.write_html(output_path, full_html=False, include_plotlyjs='cdn')

    return fig

data = []
balloon_gps=[]
balloon_traj=[]
current_image = None
# def line_process(line):
#     global current_time, timestamp, data, current_image
    
#     entry = line.strip()
    
#     if "_flir" in entry.lower():
#         timestamp, image_name = entry.split(": ", 1)
#         current_image = image_name    
#     elif entry.endswith(".JPG"):
#         timestamp, image_name = entry.split(": ", 1)
#         current_image = image_name     
#     elif "lat:" in entry and "lon:" in entry:
#         lat_str = entry.split("lat:")[1].split(",")[0].strip()
#         lon_str = entry.split("lon:")[1].split(",")[0].strip()
#         alt_str = entry.split("alt:")[1].strip() if "alt:" in entry else None
        
#         # Convert GPS values to float
#         lat, lon, alt = float(lat_str), float(lon_str), float(alt_str) if alt_str else None

#         # Assign the first found GPS data to the current image
#         if current_image:
#             # Store data in a list for the DataFrame
#             data.append({
#                 "timestamp": timestamp,
#                 "image": current_image,
#                 "latitude": lat,
#                 "longitude": lon,
#                 "altitude": alt
#             })
#             current_image = None  # Reset current_image after assigning GPS data
current_image = None
reserved_name = None
last_gps = None  # To store the last GPS data (lat, lon, alt)
data = []  # To store the processed data

def line_process(line):
    global current_image, reserved_name, last_gps, data, entry
    
    entry = line.strip()
    timestamp = None

    if "lat:" in entry and "lon:" in entry:
        # Extract GPS data
        lat_str = entry.split("lat:")[1].split(",")[0].strip()
        lon_str = entry.split("lon:")[1].split(",")[0].strip()
        alt_str = entry.split("alt:")[1].strip() if "alt:" in entry else None

        # Convert GPS values to float
        lat, lon, alt = float(lat_str), float(lon_str), float(alt_str) if alt_str else None

        # Save the GPS data as the last known GPS
        last_gps = {"latitude": lat, "longitude": lon, "altitude": alt}

    elif "_flir" in entry.lower() and (entry.endswith(".jpg")) or entry.endswith(".JPG"):
        timestamp, image_name = entry.split(": ", 1)

        # Before updating current_image, check if there is a stored GPS for the reserved image
        if current_image and last_gps:
            data.append({
                "timestamp": timestamp,
                "image": current_image,
                "latitude": last_gps["latitude"],
                "longitude": last_gps["longitude"],
                "altitude": last_gps["altitude"]
            })
            reserved_name = current_image  # Move the current image to reserved

        # Update the current image
        current_image = image_name

    # If no new GPS is found before the current image changes
    if current_image and last_gps:
        data.append({
            "timestamp": timestamp,
            "image": current_image,
            "latitude": last_gps["latitude"],
            "longitude": last_gps["longitude"],
            "altitude": last_gps["altitude"]
        })
        current_image = None  # Reset after processing
            
# timestamp2=None
def line_gps(line):
    global balloon_gps,timestamp2,text
    lat, lon, alt = None,None, None
    
    entry = line.strip()

    if "lat:" in entry and "lon:" in entry:
        lat_str = entry.split("lat:")[1].split(",")[0].strip()
        lon_str = entry.split("lon:")[1].split(",")[0].strip()
        alt_str = entry.split("alt:")[1].strip() if "alt:" in entry else None
        timestamp2, text = entry.split(": ", 1) 
        # Convert GPS values to float
        lat, lon, alt = float(lat_str), float(lon_str), float(alt_str) if alt_str else None
        
        if timestamp2 and lat is not None and lon is not None:
            # Only store the data if lat, lon, and yaw/pitch are available
            balloon_gps.append({
                "timestamp": timestamp2,
                "latitude": lat,
                "longitude": lon,
                "altitude": alt,
            })            
def line_traj(line):
    global balloon_traj,timestamp2,text
    yaw, pitch = None,None
    
    entry = line.strip()

    if "g_yaw:" in entry and "g_pitch:" in entry:
        yaw_str = entry.split("g_yaw:")[1].split(",")[0].strip()
        pitch_str = entry.split("g_pitch:")[1].strip()
        timestamp2, text = entry.split(": ", 1) 
        # Convert yaw and pitch to float
        yaw, pitch = float(yaw_str), float(pitch_str)
        
        if timestamp2 and yaw is not None and pitch is not None:
            # Only store the data if lat, lon, and yaw/pitch are available
            balloon_traj.append({
                "timestamp": timestamp2,
                "yaw": yaw,
                "pitch": pitch,
            })

microloon=[]

# def line_microloon(line):
#     entry = line.strip()

#     if "{'cpu" in entry and "}" in entry:
#         # Split the timestamp from the dictionary data
#         timestamp, dict_str = line.split(': ', 1)
            
#         # Parse the dictionary string
#         dict_str = dict_str.replace("'", "\"")  # replace single quotes with double quotes for JSON compatibility
#         values = json.loads(dict_str)  # Safely evaluate string to dictionary (use json.loads(dict_str) if possible)
#         # values = eval(dict_str)  # Safely evaluate string to dictionary (use json.loads(dict_str) if possible)
        
#         # Add timestamp to the dictionary
#         values['timestamp'] = timestamp.strip()
        
#         microloon.append(values)
def line_microloon(line):
    entry = line.strip()
    
    if "cpu" in entry:  # Check if the line contains the expected data
        # Extract the timestamp and data string
        timestamp, data_str = line.split(": ", 1)
        
        # Parse the dictionary part of the string
        try:
            data_dict = eval(data_str)
        except SyntaxError:
            raise ValueError("Line format is incorrect or data cannot be evaluated.")
        
        # Extract specific values using dictionary keys
        cpu = data_dict.get('cpu')
        altitude = data_dict.get('altitude')
        heading = data_dict.get('heading')
        course = data_dict.get('course')
        uptime = data_dict.get('uptime')
        transponder_state = data_dict.get('transponder_state')
        flasher_state = data_dict.get('flasher_state')
        kiwi_roll = data_dict.get('kiwi_roll')
        kiwi_pitch = data_dict.get('kiwi_pitch')
        kiwi_yaw = data_dict.get('kiwi_yaw')
        temp = data_dict.get('temp')
        therm_1 = data_dict.get('therm_1')
        therm_2 = data_dict.get('therm_2')
        therm_3 = data_dict.get('therm_3')
        therm_4 = data_dict.get('therm_4')
        five_volt_state = data_dict.get('five_volt_state')
        five_v_voltage = data_dict.get('five_v_voltage')
        five_v_current = data_dict.get('five_v_current')
        twentyfour_v_voltage = data_dict.get('twentyfour_v_voltage')
        twentyfour_v_current = data_dict.get('twentyfour_v_current')
        yaw = data_dict.get('yaw')
        pitch = data_dict.get('pitch')
        gimbal_state = data_dict.get('gimbal_state')
        total_degrees_moved_pitch = data_dict.get('total_degrees_moved_pitch')
        total_degrees_moved_yaw = data_dict.get('total_degrees_moved_yaw')
        rail_current_state_5v = data_dict.get('rail_current_state_5v')
        rail_current_state_8v = data_dict.get('rail_current_state_8v')
        
        # Append the parsed values to the microloon list
        microloon.append({
            'timestamp': timestamp,
            'cpu': cpu,
            'altitude': altitude,
            'heading': heading,
            'course': course,
            'uptime': uptime,
            'transponder_state': transponder_state,
            'flasher_state': flasher_state,
            'kiwi_roll': kiwi_roll,
            'kiwi_pitch': kiwi_pitch,
            'kiwi_yaw': kiwi_yaw,
            'temp': temp,
            'therm_1': therm_1,
            'therm_2': therm_2,
            'therm_3': therm_3,
            'therm_4': therm_4,
            'five_volt_state': five_volt_state,
            'five_v_voltage': five_v_voltage,
            'five_v_current': five_v_current,
            'twentyfour_v_voltage': twentyfour_v_voltage,
            'twentyfour_v_current': twentyfour_v_current,
            'yaw': yaw,
            'pitch': pitch,
            'gimbal_state': gimbal_state,
            'total_degrees_moved_pitch': total_degrees_moved_pitch,
            'total_degrees_moved_yaw': total_degrees_moved_yaw,
            'rail_current_state_5v': rail_current_state_5v,
            'rail_current_state_8v': rail_current_state_8v
        })

        
desired=[]
def line_athor(line):
    entry = line.strip()
    
    if "desired_" in entry:
        # Extract the timestamp
        timestamp, data_str = line.split(': ', 1)
        
        # Extract specific values using split and strip
        heading = int(data_str.split("heading:")[1].split(",")[0].strip())
        position_str = data_str.split("position:")[1].split("),")[0].strip()
        lat, lon = map(float, position_str.strip("()").split(","))
        alt = float(data_str.split("alt:")[1].split(",")[0].strip())
        desired_gumball_yaw = int(data_str.split("desired_gumball_yaw:")[1].split(",")[0].strip())
        desired_gumball_pitch = int(data_str.split("desired_gumball_pitch:")[1].split(",")[0].strip())
        poi = data_str.split("poi:")[1].strip()
        
        # Append the parsed values to the desired list
        desired.append({
            'timestamp': timestamp,
            'heading': heading,
            'position': (lat, lon),
            'alt': alt,
            'desired_gumball_yaw': desired_gumball_yaw,
            'desired_gumball_pitch': desired_gumball_pitch,
            'poi': poi
        })
# =============================================================================
# Functions defined for the EXIF
# =============================================================================

# I will look for the photo with gps data and insert the exif
def dms_coords(coord):
    """Convert a GPS coordinate in decimal degrees to degrees, minutes, seconds (DMS) format."""
    degrees = int(coord)
    minutes = int((coord - degrees) * 60)
    seconds = round((coord - degrees - minutes / 60) * 3600 * 10000)  # In hundredths for EXIF format
    return (degrees, 1), (minutes, 1), (seconds, 10000)

def set_gps_exif(image_path, latitude, longitude, altitude=None, comment=None):
    """Set the GPS EXIF data for an image given latitude, longitude, and optional altitude."""
    if not os.path.isfile(image_path):
        print(f"File not found: {image_path}")
        return  # Exit if file is not found
    
    # Convert latitude and longitude to DMS format
    lat_dms = dms_coords(abs(latitude))
    lon_dms = dms_coords(abs(longitude))
    
    # Determine the GPS reference direction
    lat_ref = "N" if latitude >= 0 else "S"
    lon_ref = "E" if longitude >= 0 else "W"
    
    # Create GPS IFD dictionary with latitude, longitude, and optional altitude
    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: lat_ref,
        piexif.GPSIFD.GPSLatitude: lat_dms,
        piexif.GPSIFD.GPSLongitudeRef: lon_ref,
        piexif.GPSIFD.GPSLongitude: lon_dms,
    }
    
    if altitude is not None:
        gps_ifd[piexif.GPSIFD.GPSAltitude] = (int(altitude * 100), 100)  # Altitude in meters with precision
    
    # Open the image and create or load existing EXIF data
    img = Image.open(image_path)
    try:
        exif_dict = piexif.load(img.info["exif"])  # Attempt to load existing EXIF data
    except KeyError:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}}  # Initialize empty EXIF if none exists
    
    # Add GPS data to the EXIF dictionary
    exif_dict["GPS"] = gps_ifd
    if comment:
        exif_dict["Exif"][piexif.ExifIFD.UserComment] = comment.encode("utf-8")
    
    # Save image with modified EXIF data
    exif_bytes = piexif.dump(exif_dict)
    img.save(image_path, "jpeg", exif=exif_bytes)
    print(f"Updated EXIF data for {image_path}")

processed_images = set()
unsuccessful_images = []
processed_images = set()  # Set to track successfully processed images
unsuccessful_images = []  # List to track images that failed processing

def process_exif():
    print("Inserting the EXIF lat/lon info into the images...")
    database_canon = pd.read_csv(os.path.join(output_directory, 'db_photocanon.txt'), delimiter='\t')
    database_flir = pd.read_csv(os.path.join(output_directory, 'db_photoflir.txt'), delimiter='\t')
    
    # Process Canon images
    for image_name in os.listdir(canon_directory):
        if image_name.lower().endswith(('.jpg', '.jpeg', '.png')) and image_name not in processed_images:
            image_path = os.path.join(canon_directory, image_name)
            image_info = database_canon[database_canon["image"] == image_name]
            
            if not image_info.empty:
                latitude = image_info["latitude"].values[0]
                longitude = image_info["longitude"].values[0]
                altitude = image_info["altitude"].values[0]
                try:
                    set_gps_exif(image_path, latitude, longitude, altitude)
                    processed_images.add(image_name)  # Add to processed list
                except Exception as e:
                    print(f"Error processing {image_name}: {e}")
                    unsuccessful_images.append(image_name)
            else:
                print(f"No GPS data found for {image_name}")
                unsuccessful_images.append(image_name)

    # Process FLIR images
    for image_name in os.listdir(flir_directory):
        if image_name.lower().endswith(('.jpg', '.jpeg', '.png')) and image_name not in processed_images:
            image_path = os.path.join(flir_directory, image_name)
            image_info = database_flir[database_flir["image"] == image_name]
            
            if not image_info.empty:
                latitude = image_info["latitude"].values[0]
                longitude = image_info["longitude"].values[0]
                altitude = image_info["altitude"].values[0]
                try:
                    set_gps_exif(image_path, latitude, longitude, altitude)
                    processed_images.add(image_name)  # Add to processed list
                except Exception as e:
                    print(f"Error processing {image_name}: {e}")
                    unsuccessful_images.append(image_name)
            else:
                print(f"No GPS data found for {image_name}")
                unsuccessful_images.append(image_name)

    print("Processing completed.")

# Retry failed images
def retry_unsuccessful_images():
    while True:
        print("Retrying unsuccessful images...")
        for image_name in list(unsuccessful_images):  # Iterate over a copy of the list
            if image_name in os.listdir(canon_directory):
                database_canon = pd.read_csv(os.path.join(output_directory, 'db_photocanon.txt'), delimiter='\t')
                image_path = os.path.join(canon_directory, image_name)
                image_info = database_canon[database_canon["image"] == image_name]

                if not image_info.empty:
                    latitude = image_info["latitude"].values[0]
                    longitude = image_info["longitude"].values[0]
                    altitude = image_info["altitude"].values[0]
                    try:
                        set_gps_exif(image_path, latitude, longitude, altitude)
                        processed_images.add(image_name)
                        unsuccessful_images.remove(image_name)  # Remove from unsuccessful list
                        print(f"Successfully retried {image_name}")
                    except Exception as e:
                        print(f"Retry failed for {image_name}: {e}")

        # Sleep for 5 minutes before retrying again was 300
        time.sleep(180)


# =============================================================================
# Functions defined for the photo/postproced databased
# =============================================================================

# Suppress the specific warning about the corrupted MakerNote
warnings.filterwarnings("ignore", message="Possibly corrupted field Tag 0x0001 in MakerNote IFD")

# Function to convert GPS coordinates from DMS (degrees, minutes, seconds) to decimal degrees
def convert_to_degrees(value):
    if value:
        degrees = value[0][0] / value[0][1]
        minutes = value[1][0] / value[1][1]
        seconds = value[2][0] / value[2][1]
        return degrees + (minutes / 60.0) + (seconds / 3600.0)
    return None

# Function to extract metadata (latitude, longitude, altitude, captured date) using piexif
def extract_metadata_piexif(image_path):
    try:
        img = Image.open(image_path)
        exif_data = piexif.load(img.info.get('exif', b''))  # Get EXIF metadata
        gps_data = exif_data.get('GPS', {})
        exif_info = exif_data.get('Exif', {})
        
        lat = lon = alt = captured_date = None

        # Extract GPS data
        if piexif.GPSIFD.GPSLatitude in gps_data and piexif.GPSIFD.GPSLatitudeRef in gps_data:
            lat = round(convert_to_degrees(gps_data[piexif.GPSIFD.GPSLatitude]),4)
            if gps_data[piexif.GPSIFD.GPSLatitudeRef] != b'N':
                lat = -lat
        
        if piexif.GPSIFD.GPSLongitude in gps_data and piexif.GPSIFD.GPSLongitudeRef in gps_data:
            lon = round(convert_to_degrees(gps_data[piexif.GPSIFD.GPSLongitude]),4)
            if gps_data[piexif.GPSIFD.GPSLongitudeRef] != b'E':
                lon = -lon

        if piexif.GPSIFD.GPSAltitude in gps_data:
            alt = gps_data[piexif.GPSIFD.GPSAltitude][0] / gps_data[piexif.GPSIFD.GPSAltitude][1]

        # Extract captured date (DateTimeOriginal)
        if piexif.ExifIFD.DateTimeOriginal in exif_info:
            captured_date = exif_info[piexif.ExifIFD.DateTimeOriginal].decode("utf-8")

        return lat, lon, alt, captured_date
    except Exception as e:
        print(f"Error extracting metadata from {image_path}: {e}")
        return None, None, None, None

# Function to generate KML files
def generate_kml(df_filtered):
    # Create a new KML object for multipoints
    kml = simplekml.Kml()

    # Loop through the filtered DataFrame and add placemarks for each row
    for index, row in df_filtered.iterrows():
        lat = row['Latitude']
        lon = row['Longitude']
        altitude = row['Altitude']
        image_name = row['Image Name']
        kml.newpoint(name=image_name, coords=[(lon, lat)], altitudemode='clampToGround', description=f"Altitude: {altitude}")

    output_kml_path = os.path.join(output_directory, 'filtered_multipoint_path' + f'_{Fligth_name}.kml').replace(os.sep, '/')
    kml.save(output_kml_path)
    print(f"KML file saved at: {output_kml_path}")

    # Create polyline KML
    coords = [(row['Longitude'], row['Latitude']) for _, row in df_filtered.iterrows()]
    kml = simplekml.Kml()
    linestring = kml.newlinestring(name="Flight Path")
    linestring.coords = coords
    linestring.altitudemode = 'clampToGround'
    linestring.style.linestyle.color = simplekml.Color.red
    linestring.style.linestyle.width = 3

    output_kml_path = os.path.join(output_directory, 'filtered_polyline_path' + f'_{Fligth_name}.kml').replace(os.sep, '/')
    kml.save(output_kml_path)
    print(f"Polyline KML file saved at: {output_kml_path}")
    

# def refresh_plot(df_filtered):
#     # Convert timedelta to total seconds for x-axis
#     df_filtered['Total_Seconds'] = df_filtered['Time']

#     # Create interactive Plotly figure
#     fig = px.line(df_filtered, x='Total_Seconds', y='Altitude', title="Altitude vs Time",
#                   labels={'Total_Seconds': 'Time (secs)', 'Altitude': 'Altitude (m)'})
    
#     # Customize x-axis tick formatting for better readability
#     fig.update_xaxes(
#         tickvals=[i for i in range(0, int(df_filtered['Total_Seconds'].max()), 900)],
#         ticktext=[f"{int(x // 3600)}h {int((x % 3600) // 60)}m" for x in range(0, int(df_filtered['Total_Seconds'].max()), 900)],
#         tickangle=90
#     )

#     # Save the figure as an HTML string
#     output_path = os.path.join(output_directory, 'altitude_vs_time_plot.html')
#     fig.write_html(output_path)

def refresh_plot(df_filtered):
    # Convert timedelta to total seconds for x-axis
    df_filtered['Total_Seconds'] = df_filtered['Time']

    # Determine maximum time for dynamic formatting
    max_time = int(df_filtered['Total_Seconds'].max())
    if max_time < 60:
        # Use seconds
        tickvals = list(range(0, max_time + 1, 10))  # Every 10 seconds
        ticktext = [f"{x}s" for x in tickvals]
    elif max_time < 3600:
        # Use minutes and seconds
        tickvals = list(range(0, max_time + 1, 60))  # Every minute
        ticktext = [f"{int(x // 60)}m {int(x % 60)}s" for x in tickvals]
    else:
        # Use hours and minutes
        tickvals = list(range(0, max_time + 1, 900))  # Every 15 minutes
        ticktext = [f"{int(x // 3600)}h {int((x % 3600) // 60)}m" for x in tickvals]

    # Create interactive Plotly figure
    fig = px.line(
        df_filtered,
        x='Total_Seconds',
        y='Altitude',
        title="Altitude vs Time",
        labels={'Total_Seconds': 'Time', 'Altitude': 'Altitude (m)'}
    )

    # Customize x-axis tick formatting
    fig.update_xaxes(
        tickvals=tickvals,
        ticktext=ticktext,
        tickangle=90  # Adjust angle for readability
    )

    # Update layout for responsiveness
    fig.update_layout(
        title={
            'text': "Altitude vs Time",
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 16},
        },
        margin=dict(l=20, r=20, t=50, b=50),
        xaxis_title=dict(font=dict(size=12)),
        yaxis_title=dict(font=dict(size=12)),
        template="plotly_white",
        autosize=True,
    )

    # Save the figure as a responsive HTML
    output_path = os.path.join(output_directory, 'altitude_vs_time_plot.html')
    fig.write_html(output_path, full_html=False, include_plotlyjs='cdn')
    
def extract_date_from_filename(filename):
    """
    Extract the captured date from the filename in the format YYYYMMDD_HHMMSS.
    """
    match = re.match(r"(\d{8}_\d{6})", filename)
    if match:
        # Convert the match to a datetime string
        date_time_str = match.group(1)
        return pd.to_datetime(date_time_str, format='%Y%m%d_%H%M%S', errors='coerce')
    return pd.NaT

# Function to process the images and generate all the outputs (database, plots, KML)
# def process_images():
#     global df_filtered

#     print("Processing images...")
    
#     # List to store image data
#     image_data = []

#     # Loop through the directory and process each image
#     for filename in os.listdir(canon_directory):
#         if filename.lower().endswith(('.jpg', '.jpeg', '.png')):  # Case-insensitive check for image files
#             image_path = os.path.join(canon_directory, filename)
#             lat, lon, alt, captured_date = extract_metadata_piexif(image_path)  # Extract metadata using piexif
#             image_data.append({'Image Name': filename, 'Latitude': lat, 'Longitude': lon, 'Altitude': alt, 'Captured Date': captured_date})

#     # Create a pandas DataFrame
#     canon_df = pd.DataFrame(image_data)
#     canon_df['flight_ID'] = Fligth_name

#     # Convert the "Captured Date" column to datetime format
#     canon_df['Captured Date'] = pd.to_datetime(canon_df['Captured Date'], format='%Y:%m:%d %H:%M:%S')

#     # Filter rows where Latitude, Longitude, and Altitude are not None or NaN
#     # df_filtered = canon_df.dropna(subset=['Latitude', 'Longitude', 'Altitude'])

#     df_filtered = canon_df.dropna(subset=['Latitude', 'Longitude', 'Altitude']).copy()
    
#     # Convert "Captured Date" to datetime
#     df_filtered.loc[:, 'Captured Date'] = pd.to_datetime(df_filtered['Captured Date'], format='%Y:%m:%d %H:%M:%S')

#     # Calculate the relative time in seconds
#     df_filtered.loc[:, 'Time'] = (df_filtered['Captured Date'] - df_filtered['Captured Date'].iloc[0]).dt.total_seconds()

#     # Save to a txt file with tab separator
#     df_filtered.to_csv(os.path.join(output_directory, 'db_postcanon.txt').replace(os.sep, '/'), sep='\t', index=False)

#     # Generate KML files
#     generate_kml(df_filtered)

#     # Refresh and create the plot
#     refresh_plot(df_filtered)
    
#     print("Processing complete.")
def process_images():
    global df_filtered

    print("Processing images...")
    
    # List to store image data
    image_data = []

    # Loop through the directory and process each image
    for filename in os.listdir(canon_directory):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):  # Case-insensitive check for image files
            image_path = os.path.join(canon_directory, filename)
            
            # Try to extract metadata using piexif
            lat, lon, alt, captured_date = extract_metadata_piexif(image_path)
            
            # If no captured date from EXIF, extract from filename
            if not captured_date or pd.isna(captured_date) or captured_date is pd.NaT:
                captured_date = extract_date_from_filename(filename)

            image_data.append({'Image Name': filename, 'Latitude': lat, 'Longitude': lon, 'Altitude': alt, 'Captured Date': captured_date})

    # Create a pandas DataFrame
    canon_df = pd.DataFrame(image_data)
    canon_df['flight_ID'] = Fligth_name

    # Convert the "Captured Date" column to datetime format
    canon_df['Captured Date'] = pd.to_datetime(canon_df['Captured Date'], format='%Y:%m:%d %H:%M:%S', errors='coerce')

    # Filter rows where Latitude, Longitude, and Altitude are not None or NaN
    df_filtered = canon_df.dropna(subset=['Latitude', 'Longitude', 'Altitude']).copy()
    
    # Calculate the relative time in seconds
    df_filtered.loc[:, 'Time'] = (df_filtered['Captured Date'] - df_filtered['Captured Date'].iloc[0]).dt.total_seconds()

    # Save to a txt file with tab separator
    df_filtered.to_csv(os.path.join(output_directory, 'db_postcanon.txt').replace(os.sep, '/'), sep='\t', index=False)

    # Generate KML files
    generate_kml(df_filtered)

    # Refresh and create the plot
    refresh_plot(df_filtered)
    
    print("Processing complete.")    
# =============================================================================
# Create the loop over the log file
# =============================================================================
# Haversine formula to calculate distance in meters
import math
def haversine(lat1, lon1, lat2, lon2):
    if lat1 == lat2 and lon1 == lon2:
        return 0  # Distance is zero if the points are the same
    
    R = 6371000  # Earth radius in meters
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c  # Distance in meters
###
import threading
import warnings
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Assuming other function definitions are already present (line_microloon, line_process, line_gps, line_traj, etc.)
# Initialize the files with headers
initialize_files()
initialize_empty_plot()
# Set up the log monitoring function
def monitor_log_file():
    last_line_count = 0
    while True:
        with open(log_path, "r") as file:
            # print("Monitoring the log file for updates")
            lines = file.readlines()
            if len(lines) > last_line_count:
                for line in lines[last_line_count:]:
                    line_microloon(line)
                    line_process(line)
                    line_gps(line)
                    line_traj(line)
                    line_athor(line)
                # Save data if any
                if data:
                    df = pd.DataFrame(data)
                    dcanon = df[~df['image'].str.contains('_flir')]
                    dflir = df[df['image'].str.contains('_flir')]
                    if not dflir.empty:
                        dflir.to_csv(os.path.join(output_directory, 'db_photoflir.txt').replace(os.sep, '/'), sep='\t', index=False, mode='a', header=not os.path.exists(os.path.join(output_directory, 'db_photoflir.txt')))
                    if not dcanon.empty:
                        dcanon.to_csv(os.path.join(output_directory, 'db_photocanon.txt').replace(os.sep, '/'), sep='\t', index=False, mode='a', header=not os.path.exists(os.path.join(output_directory, 'db_photocanon.txt')))
                    data.clear()

                if balloon_gps:
                    db = pd.DataFrame(balloon_gps)

# =============================================================================
#                    # Calculate speed based on GPS data
                    # speeds = []
                    # grouped = db.groupby('timestamp')

                    # for _, group in grouped:
                    #     first_point = group.iloc[0]
                    #     last_point = group.iloc[-1]

                    #     lat1, lon1 = first_point['latitude'], first_point['longitude']
                    #     lat2, lon2 = last_point['latitude'], last_point['longitude']

                    #     # Calculate the distance between the first and last point in that second
                    #     distance = haversine(lat1, lon1, lat2, lon2)
                        
                    #     # Speed (distance in meters, time difference is 1 second)
                    #     speed = distance  # Speed in m/s
                    #     group['speed (m/s)'] = speed

                    #     speeds.append(speed)

                    # # Add the speed column to the DataFrame
                    # db['speed (m/s)'] = None
                    # db.loc[db.groupby('timestamp').head(1).index, 'speed (m/s)'] = speeds

                    # # Save GPS data with speeds to CSV
                    # if not db.empty:
                    #     db.to_csv(os.path.join(output_directory, 'db_balloon_gps.txt').replace(os.sep, '/'), sep='\t', index=False, mode='a', header=not os.path.exists(os.path.join(output_directory, 'db_balloon_gps.txt')))
                    # balloon_gps.clear()
                    
                    
                    
                    grouped = db.groupby('timestamp')
                    speeds = []  # List to collect modified DataFrames
                    
                    for _, group in grouped:
                        first_point = group.iloc[0]
                        last_point = group.iloc[-1]
                    
                        lat1, lon1 = first_point['latitude'], first_point['longitude']
                        lat2, lon2 = last_point['latitude'], last_point['longitude']
                    
                        # Calculate the distance between the first and last point in that second
                        distance = haversine(lat1, lon1, lat2, lon2)
                        
                        # Speed (distance in meters, time difference is 1 second)
                        speed = distance  # Speed in m/s
                        
                        # Assign the calculated speed to all rows in the group
                        group['speed (m/s)'] = speed
                        
                        # Append the modified group (DataFrame) to the list
                        speeds.append(group)
                    
                    # Check the contents of the speeds list before concatenation
                    # print(f"Speeds list length: {len(speeds)}")
                    # print(f"First item in speeds: {speeds[0] if speeds else 'No data'}")
                    
                    # Now concatenate the list of DataFrames
                    if speeds:  # Proceed only if the list is not empty
                        db_with_speeds = pd.concat(speeds, ignore_index=True)
                    
                        # Save GPS data with speeds to CSV
                        if not db_with_speeds.empty:
                            db_with_speeds.to_csv(os.path.join(output_directory, 'db_balloon_gps.txt').replace(os.sep, '/'), 
                                                  sep='\t', index=False, mode='a', header=not os.path.exists(os.path.join(output_directory, 'db_balloon_gps.txt')))
                    else:
                        print("No data to concatenate!")
                    
                    balloon_gps.clear()
# =============================================================================
                    # if not db.empty:
                    #     db.to_csv(os.path.join(output_directory, 'db_balloon_gps.txt').replace(os.sep, '/'), sep='\t', index=False, mode='a', header=not os.path.exists(os.path.join(output_directory, 'db_balloon_gps.txt')))
                    # balloon_gps.clear()

                if balloon_traj:
                    db = pd.DataFrame(balloon_traj)
                    if not db.empty:
                        db.to_csv(os.path.join(output_directory, 'db_balloon_traj.txt').replace(os.sep, '/'), sep='\t', index=False, mode='a', header=not os.path.exists(os.path.join(output_directory, 'db_balloon_traj.txt')))
                    balloon_traj.clear()

                if microloon:
                    dmicro = pd.DataFrame(microloon)
                    if not dmicro.empty:
                        dmicro.to_csv(os.path.join(output_directory, 'db_microloon.txt').replace(os.sep, '/'), sep='\t', index=False, mode='a', header=not os.path.exists(os.path.join(output_directory, 'db_microloon.txt')))
                    microloon.clear()

                if desired:
                    df_desired = pd.DataFrame(desired)
                    if not df_desired.empty:
                        df_desired.to_csv(os.path.join(output_directory, 'db_desired.txt').replace(os.sep, '/'), sep='\t', index=False, mode='a', header=not os.path.exists(os.path.join(output_directory, 'db_desired.txt')))
                    microloon.clear()                    
                    

                last_line_count = len(lines)
        
        time.sleep(1)

# Set up the image monitoring function
def monitor_images():
    # Suppress specific warnings
    warnings.filterwarnings("ignore", message="Possibly corrupted field Tag 0x0001 in MakerNote IFD")
    
    class ImageHandler(FileSystemEventHandler):
        def on_created(self, event):
            if event.is_directory:
                return
            if event.src_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                process_exif()
                process_images()

    observer = Observer()
    event_handler = ImageHandler()
    observer.schedule(event_handler, path=canon_directory, recursive=False)
    observer.start()

    try:
        print(f"Monitoring {canon_directory} for new images...")
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()

# Start both threads
log_thread = threading.Thread(target=monitor_log_file)
image_thread = threading.Thread(target=monitor_images)
retry_thread = threading.Thread(target=retry_unsuccessful_images, daemon=True)

log_thread.start()
image_thread.start()
retry_thread.start()

log_thread.join()
image_thread.join()
retry_thread.join()
