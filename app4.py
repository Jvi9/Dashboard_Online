# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 18:08:06 2024

@author: Jhon
"""

import os
from flask import Flask, jsonify, render_template, url_for,send_file, request
from flask_cors import CORS
from flask import send_from_directory
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

app = Flask(__name__)
CORS(app) #Delete when we put it in the server
dashboard_directory = r'C:\Users\Jhon\Desktop\test_Z007_replicaserver'
image_directory = os.path.join(dashboard_directory, 'test_canon') # Update with your actual path
canon_directory = r'C:\Users\Jhon\Desktop\test_Z007_replicaserver\CANON_PHOTOS'
output_directory=r'C:\Users\Jhon\Desktop\test_Z007_replicaserver'

# INITIALIZATION=============================================================================
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

# initialize_files()
# initialize_empty_plot()
# =============================================================================
            
# Function to read the db_canon.txt file and return data
def read_gps_data(file_path):
    gps_data = []
    with open(file_path, 'r') as f:
        lines = f.readlines()[1:]  # Skip the header line
        for line in lines:
            parts = line.strip().split('\t')  # Split by tab characters
            if len(parts) >= 5:  # Ensure there are enough parts
                photo_name = parts[0]
                lat = float(parts[1])
                lon = float(parts[2])
                alt = float(parts[3])
                gps_data.append({
                    'photo_name': photo_name,
                    'lat': lat,
                    'lon': lon,
                    'alt': alt
                })
    return gps_data

def get_latest_image(directory):
    try:
        # List all files in the folder
        files = [os.path.join(directory, f) for f in os.listdir(directory)]
        
        # Filter only image files
        image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        if not image_files:
            return None  # No images found
        
        # Find the latest image by modification time
        latest_image_path = max(image_files, key=os.path.getmtime)
        # Convert file path to a URL for serving in Flask
        latest_image_filename = os.path.basename(latest_image_path)
        return latest_image_filename
    
    except Exception as e:
        print(f"Error: {e}")
        return None

#testing
def read_latest_balloon_data(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()[1:]  # Skip the header line
        if lines:
            last_line = lines[-1]
            parts = last_line.strip().split('\t')
            if len(parts) >= 5:
                return {
                    'timestamp': parts[0],
                    'latitude': float(parts[1]),
                    'longitude': float(parts[2]),
                    'altitude': float(parts[3]),
                    'speed': float(parts[4])
                }

# Function to read the db_traj.txt file and return data
def read_latest_traj_data(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()[1:]  # Skip the header line
        if lines:
            last_line = lines[-1]
            parts = last_line.strip().split('\t')
            if len(parts) >= 2:
                return {
                    'timestamp': parts[0],
                    'yaw': float(parts[1]),
                    'pitch': float(parts[2])
                }
    return None

def read_latest_microloon_data(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()[1:]  # Skip the header line
        if lines:
            last_line = lines[-1]
            parts = last_line.strip().split('\t')
            if len(parts) >= 4:
                return {
                    'timestamp': parts[0],
                    'cpu': float(parts[1]),
                    'altitude': float(parts[2]),
                    'heading':parts[3],
                    'course':float(parts[4]),    
                    'uptime': float(parts[5]),
                    'transponder_state': float(parts[6]),
                    'flasher_state': float(parts[7]),
                    'kiwi_roll': float(parts[8]),
                    'kiwi_pitch': float(parts[9]),
                    'kiwi_yaw': float(parts[10]),
                    'temp': float(parts[11]),
                    'therm_1': float(parts[12]),
                    'therm_2': float(parts[13]),
                    'therm_3': float(parts[14]),
                    'therm_4': float(parts[15]),
                    'five_volt_state': float(parts[16]),
                    'five_v_voltage': float(parts[17]),
                    'five_v_current': float(parts[18]),
                    'twentyfour_v_voltage': float(parts[19]),
                    'twentyfour_v_current': float(parts[20]),
                    'yaw': float(parts[21]),
                    'pitch': float(parts[22]),
                    'gimbal_state': float(parts[23]),
                    'total_degrees_moved_pitch': float(parts[24]),
                    'total_degrees_moved_yaw': float(parts[25]),
                    'rail_current_state_5v': float(parts[26]),
                    'rail_current_state_8v': float(parts[27])
                }
    return None

def read_latest_desired_data(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()[1:]  # Skip the header line
        if lines:
            last_line = lines[-1]
            parts = last_line.strip().split('\t')
            if len(parts) >= 2:
                return {
                    'timestamp': parts[0],
                    'heading': float(parts[1]),
                    'position': parts[2],
                    'alt': float(parts[3]),
                    'desired_gumball_yaw':float(parts[4]),
                    'desired_gumball_pitch':float(parts[5]),
                    'poi':parts[6]
                }
    return None
    
#testing
@app.route('/canon_photos/<path:filename>')
def canon_photos(filename):
    return send_from_directory(canon_directory, filename)
@app.route('/latest-image')
def latest_image():
    folder_path = canon_directory
    latest_image_name = get_latest_image(folder_path)
    if latest_image_name:
        # Return the URL in JSON format for better API design
        latest_image_url = url_for('canon_photos', filename=latest_image_name, _external=True)
        return jsonify({"latest_image_url": latest_image_url})
    
    return jsonify({"error": "No images found"}), 404
@app.route('/root_file/<path:filename>')
def root_file(filename):
    # Serve files directly from the app root path
    folder_path = os.path.join(os.getcwd(), '')  # Get the current working directory (where app.py is located)
    return send_from_directory(folder_path, filename)

@app.route('/')
def index():
    # Path to db_canon.txt
    # file_path = r'C:\Users\Jhon\Desktop\Balloon_Tech_Project\Z006\db_canon.txt'
    file_path = os.path.join(dashboard_directory, 'db_postcanon.txt')
   
    # Read the GPS data
    gps_data = read_gps_data(file_path)

    # Ensure the images exist in the folder and append the full path
    for data in gps_data:
        img_path = os.path.join(canon_directory, data['photo_name'])
        print(f"Checking image path: {img_path}")  # Debugging statement
        if os.path.exists(img_path):
            data['img_url'] = url_for('canon_photos', filename=data['photo_name'])
            print(f"Image URL generated: {data['img_url']}")  # Debugging statement
        else:
            data['img_url'] = None  # Mark missing images
            print(f"Image does not exist: {data['photo_name']}")  # Debugging statement

    latest_image = get_latest_image(canon_directory)  # Get the latest image URL
    
    # Path to your plot file
    plot_file_path = os.path.join(app.root_path, 'altitude_vs_time_plot.html')
    plot_exists = os.path.exists(plot_file_path)
    # Get the last modified time of the plot file
    last_modified_time = os.path.getmtime(plot_file_path)

    return render_template('draft_dash_vuser.html',
                           gps_data=gps_data,
                           latest_image=latest_image,
                           last_modified_time=last_modified_time,
                           plot_exists=plot_exists)
@app.route('/check-plot-update')
def check_plot_update():
    # Path to your plot file
    plot_file_path = os.path.join(app.root_path, 'altitude_vs_time_plot.html')
    
    # Get the last modified time of the plot file
    last_modified_time = os.path.getmtime(plot_file_path)
    
    # Return the last modified time as JSON
    return jsonify({'last_modified_time': last_modified_time})
@app.route('/load-all-maps')
def load_all_maps():
    folder_path = os.path.join(app.static_folder, 'KMLmaps')
    # Make sure the folder exists
    if not os.path.exists(folder_path):
        return jsonify([])  # Return empty list if folder doesn't exist

    # Get all KML and KMZ files in the folder
    files = [f for f in os.listdir(folder_path) if f.endswith('.kml') or f.endswith('.kmz')]
    return jsonify(files)

# New API route to fetch GPS data
# @app.route('/api/gps-data', methods=['GET'])
# def api_gps_data():
#     # Path to db_canon.txt
#     # file_path = r'C:\Users\Jhon\Desktop\Balloon_Tech_Project\Z006\db_canon.txt'
#     file_path = os.path.join(dashboard_directory, 'db_postcanon.txt')
#     gps_data = read_gps_data(file_path)
    
#     # Base URL for static images
#     base_url = '/canon_photos/'

#     # Update gps_data to include full URLs
#     for data in gps_data:
#         # Assuming data['imageName'] contains the filename
#         data['imageUrl'] = f"{base_url}{data['photo_name']}"

#     # Log the fetched GPS data
#     for data in gps_data:
#         print(data)  # Debugging statement

#     return jsonify(gps_data)
@app.route('/api/gps-data', methods=['GET'])
def api_gps_data():
    # Path to db_postcanon.txt
    file_path = os.path.join(dashboard_directory, 'db_postcanon.txt')
    gps_data = read_gps_data(file_path)

    # Base URL for static images
    base_url = '/canon_photos/'

    # Update gps_data to include full URLs
    for data in gps_data:
        data['imageUrl'] = f"{base_url}{data['photo_name']}"

    # Log the fetched GPS data
    print(f"Fetched {len(gps_data)} GPS points")

    # Check for mode in query parameters
    mode = request.args.get('mode', 'last20')  # Default mode is 'last20'

    if mode == 'last20':
        # Return the last 20 points
        gps_data = gps_data[-20:]
    elif mode == 'all':
        # Return all points
        pass  # gps_data is already all points

    return jsonify(gps_data)
#Testing
@app.route('/latest-balloon-data')
def latest_balloon_data():
    # pathgps=r'C:\Users\Jhon\Desktop\Balloon_Tech_Project\Z006\To_delete\db_balloon_gps.txt'
    pathgps=os.path.join(dashboard_directory, 'db_balloon_gps.txt')
    latest_data = read_latest_balloon_data(pathgps)
    if latest_data:
        return jsonify(latest_data)
    else:
        return jsonify({"error": "No data found"}), 404

@app.route('/latest-microloon-data')
def latest_microloon_data():
    # pathmicroloon=r'C:\Users\Jhon\Desktop\test_Z007_replicaserver\db_microloon.txt'
    pathmicroloon=os.path.join(dashboard_directory, 'db_microloon.txt')
    latest_data = read_latest_microloon_data(pathmicroloon)
    if latest_data:
        return jsonify(latest_data)
    else:
        return jsonify({"error": "No data found"}), 404

@app.route('/latest-traj-data')
def latest_traj_data():
    # pathmicroloon=r'C:\Users\Jhon\Desktop\test_Z007_replicaserver\db_microloon.txt'
    pathtraj=os.path.join(dashboard_directory, 'db_balloon_traj.txt')
    latest_data = read_latest_traj_data(pathtraj)
    if latest_data:
        return jsonify(latest_data)
    else:
        return jsonify({"error": "No data found"}), 404    

@app.route('/latest-desired-data')
def latest_desired_data():
    # pathmicroloon=r'C:\Users\Jhon\Desktop\test_Z007_replicaserver\db_microloon.txt'
    pathdesired=os.path.join(dashboard_directory, 'db_desired.txt')
    latest_data = read_latest_desired_data(pathdesired)
    if latest_data:
        return jsonify(latest_data)
    else:
        return jsonify({"error": "No data found"}), 404 

@app.route('/generate-plots')
def generate_plots():
    try:
        # File paths
        gps_file_path = os.path.join(dashboard_directory, 'db_balloon_gps.txt')
        traj_file_path = os.path.join(dashboard_directory, 'db_balloon_traj.txt')
        microloon_file_path = os.path.join(dashboard_directory, 'db_microloon.txt')

        # Load and process GPS data
        gps_data = pd.read_csv(gps_file_path, delimiter='\t')
        last_1000_points = gps_data.tail(2500)

        # Create the first plot (Timestamp vs Speed)
        gps_fig = px.scatter(
            last_1000_points, 
            x='timestamp', 
            y='speed',
            title='Timestamp vs Speed',
            labels={'timestamp': 'Timestamp (HH:MM:SS)', 'speed': 'Speed (m/s)'},
            opacity=0.7
        )
        gps_plot_html = gps_fig.to_html(full_html=False)

        # Load and process Trajectory data
        traj_data = pd.read_csv(traj_file_path, delimiter='\t')
        last_2500_points_traj = traj_data.tail(2500)

        # Create the second plot (Pitch and Yaw with dual y-axes)
        traj_fig = go.Figure()
        traj_fig.add_trace(go.Scatter(
            x=last_2500_points_traj['timestamp'],
            y=last_2500_points_traj['pitch'],
            mode='lines',
            name='Pitch',
            line=dict(color='blue')
        ))
        traj_fig.add_trace(go.Scatter(
            x=last_2500_points_traj['timestamp'],
            y=last_2500_points_traj['yaw'],
            mode='lines',
            name='Yaw',
            line=dict(color='orange'),
            yaxis='y2'
        ))
        traj_fig.update_layout(
            title='Timestamp vs Pitch and Yaw',
            xaxis=dict(title='Timestamp (HH:MM:SS)'),
            yaxis=dict(title='Pitch', titlefont=dict(color='blue'), tickfont=dict(color='blue')),
            yaxis2=dict(title='Yaw', titlefont=dict(color='orange'), tickfont=dict(color='orange'),
                        overlaying='y', side='right'),
            legend=dict(x=0.5, y=1.1, orientation='h'),
        )
        traj_plot_html = traj_fig.to_html(full_html=False)
        
        # Load and process Trajectory data
        microloon_data = pd.read_csv(microloon_file_path, delimiter='\t')
        last_2500_points_micro = microloon_data.tail(2500)
        
        micro_fig = go.Figure()
        micro_fig = go.Figure()

        # Add each therm variable as a separate trace
        micro_fig.add_trace(go.Scatter(
            x=last_2500_points_micro['timestamp'],
            y=last_2500_points_micro['therm_1'],
            mode='lines',
            name='Therm 1',
            line=dict(color='blue')
        ))
        micro_fig.add_trace(go.Scatter(
            x=last_2500_points_micro['timestamp'],
            y=last_2500_points_micro['therm_2'],
            mode='lines',
            name='Therm 2',
            line=dict(color='orange')
        ))
        micro_fig.add_trace(go.Scatter(
            x=last_2500_points_micro['timestamp'],
            y=last_2500_points_micro['therm_3'],
            mode='lines',
            name='Therm 3',
            line=dict(color='green')
        ))
        micro_fig.add_trace(go.Scatter(
            x=last_2500_points_micro['timestamp'],
            y=last_2500_points_micro['therm_4'],
            mode='lines',
            name='Therm 4',
            line=dict(color='red')
        ))
        micro_fig.update_layout(
            title='Timestamp vs Therm Variables',
            xaxis=dict(title='Timestamp (HH:MM:SS)'),
            yaxis=dict(title='Therm Values'),
            legend=dict(x=0.5, y=1.1, orientation='h')
        )
        micro_plot_html = micro_fig.to_html(full_html=False)


        # Return both plots as JSON
        return jsonify({
            'success': True,
            'gpsPlotHtml': gps_plot_html,
            'trajPlotHtml': traj_plot_html,
            'microPlotHtml': micro_plot_html
        })
    except Exception as e:
        print(f"Error generating plots: {e}")
        return jsonify({'success': False, 'message': 'Error generating plots.'})

#Testing

# to comment later!
@app.route('/dashboard2')
def dashboard2():
    # Any data or logic specific to dashboard 2 can go here
    return render_template('Aarthi_dashboard.html')
if __name__ == '__main__':
    app.run(debug=True)
    
# =============================================================================
# Aathi's dashboard
# =============================================================================

from flask import Flask, render_template
import os
from datetime import datetime
import pytz

image_app = Flask('image_dashboard')

# Correct paths to your image directories
webcam_directory = r'C:\Users\Jhon\Desktop\test_Z007_replicaserver/WEBCAM_PHOTOS'
flir_directory = r'C:\Users\Jhon\Desktop\test_Z007_replicaserver\FLIR_PHOTOS'
canon_directory = r'C:\Users\Jhon\Desktop\test_Z007_replicaserver\CANON_PHOTOS'
log_dir = r'C:\Users\Jhon\Desktop\test_Z007_replicaserver\logs'

# Function to get the recent images from a directory
def get_recent_images(image_directory):
    images = [f for f in sorted(os.listdir(image_directory), reverse=True) if f.endswith('.jpg') or f.endswith('.JPG')]
    return images[:10]  # Limit to the most recent 10 images

def get_latest_log_file():
    symlink_path = os.path.join(log_dir, 'latest_jetson_logfile.txt')
    # Check if the symlink exists
    if not os.path.islink(symlink_path):
        raise FileNotFoundError(f"{symlink_path} does not exist or is not a symlink.")
     # Get the file the symlink points to
    latest_file = os.readlink(symlink_path)

    # Join the directory with the file name
    latest_file_path = os.path.join(log_dir, os.path.basename(latest_file))
    if not os.path.isfile(latest_file_path):
        raise FileNotFoundError(f"File {latest_file_path} does not exist.")
    return latest_file_path

def parse_log_data(log_file_path):
    flight_info = {'lat': 'None', 'lon': 'None', 'alt': 'None', 'heading': 'None'}
    temperatures = {'therm_1': 'None', 'therm_2': 'None', 'therm_3': 'None', 'therm_4': 'None'}
    log_stream = []
    
    with open(log_file_path, 'r') as log_file:
        health_dict = {}
        try:
            for line in log_file:
                timestamp = line.split(" ")[0]
                line = ":".join(line.split(":")[3:])
                log_stream.append(line.strip())
                if '{' in line and '}' in line:
                    key_val_pairs = line.split(",")
                    for key_val_pair in key_val_pairs:
                        key, val = key_val_pair.split(":")
                        key = key.strip().strip("'").strip('"')
                        val = val.strip().strip("'").strip('"')
                        health_dict[key] = val
                elif 'lat' in line and 'lon' in line and 'alt' in line:
                    gps_data = line.split(",")
                    for key_val_pair in gps_data:
                        key, val = key_val_pair.split(":")
                        key = key.strip().strip("'").strip('"')
                        val = val.strip().strip("'").strip('"')
                        health_dict[key] = val
            print(health_dict.keys())



            for key in list(flight_info.keys()):
                flight_info[key] = health_dict.get(key, 'None')
            for key in list(temperatures.keys()):
                temperatures[key] = health_dict.get(key, 'None')
        except Exception as e:
            print(e)

    return flight_info, temperatures, log_stream, timestamp 

@image_app.route('/')
def image_dashboard():
    # Get recent images from each directory
    webcam_images = get_recent_images(webcam_directory)
    flir_images = get_recent_images(flir_directory)
    canon_images = get_recent_images(canon_directory)
    log_file_path = get_latest_log_file()
    flight_info, temperatures, log_stream, timestamp = parse_log_data(log_file_path)

    # Get current PST and Zulu time
    pst_time = datetime.now(pytz.timezone('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S')
    zulu_time = datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')

    return render_template('image_dashboard.html',
                           pst_time=pst_time,
                           zulu_time=zulu_time,
                           webcam_images=webcam_images,
                           flir_images=flir_images,
                           canon_images=canon_images,
                           flight_info=flight_info,
                           temperatures=temperatures,
                           log_file=os.path.basename(log_file_path),
                           latest_log_entry_time=timestamp)