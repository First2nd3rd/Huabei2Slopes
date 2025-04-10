#!/usr/bin/env python3
import argparse
import json
import os
import re
import requests
import datetime
from xml.etree import ElementTree as ET

def extract_track_uuid(url):
    """Extract the track_uuid or ski_uuid from the shared URL."""
    # Try to find track_uuid first
    track_match = re.search(r'track_uuid=([^&]+)', url)
    if track_match:
        return track_match.group(1)
    
    # If track_uuid not found, try to find ski_uuid
    ski_match = re.search(r'ski_uuid=([^&]+)', url)
    if ski_match:
        return ski_match.group(1)
    
    raise ValueError("Could not find track_uuid or ski_uuid in the provided URL")

def fetch_track_data(track_uuid):
    """Fetch track data from the Huabei API."""
    # First try the track endpoint
    url = f"https://api.fenxuekeji.com/api/tracks/{track_uuid}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    
    # If track endpoint fails, try the ski endpoint
    url = f"https://api.fenxuekeji.com/api/skis/{track_uuid}"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch track data: {response.status_code}")
    
    return response.json()

def get_default_filename(track_data):
    """Generate a default filename based on date and resort name."""
    try:
        # Get date
        if 'data' in track_data and 'track' in track_data['data']:
            # Try to get formatted date string first
            date_str = track_data['data']['track'].get('start_at_str')
            if date_str:
                # Convert from format like "2024-02-05" to "February 05, 2024"
                date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                date_formatted = date_obj.strftime("%B %d, %Y")
            else:
                # Fall back to timestamp if string date not available
                start_timestamp = track_data['data']['track'].get('start_at')
                if start_timestamp:
                    date_obj = datetime.datetime.fromtimestamp(start_timestamp)
                    date_formatted = date_obj.strftime("%B %d, %Y")
                else:
                    date_formatted = "unknown_date"
        else:
            date_formatted = "unknown_date"
        
        # Get resort name
        if 'data' in track_data and 'ski_ranch' in track_data['data']:
            resort_name = track_data['data']['ski_ranch'].get('name', 'unknown_resort')
            # Clean resort name to make it file-system friendly
            resort_name = resort_name.replace('/', '-').replace('\\', '-').replace(' ', '_')
        else:
            resort_name = "unknown_resort"
        
        # Combine date and resort name
        return f"{date_formatted} - {resort_name}.gpx"
    except Exception as e:
        print(f"Warning: Could not generate default filename: {str(e)}")
        if 'data' in track_data and 'track' in track_data['data'] and 'uuid' in track_data['data']['track']:
            return f"{track_data['data']['track']['uuid']}.gpx"
        return "ski_track.gpx"

def parse_timestamp(timestamp_str):
    """Parse timestamp string to datetime object."""
    try:
        # Format is likely "YYYY-MM-DD HH:MM:SS"
        return datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        # Try alternative formats if necessary
        try:
            return datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
        except ValueError:
            return None

def create_gpx(track_data, timezone_offset=0):
    """Convert track data to GPX format."""
    # Create the root GPX element
    gpx = ET.Element('gpx')
    gpx.set('version', '1.1')
    gpx.set('creator', 'Huabei to Slopes Converter')
    gpx.set('xmlns', 'http://www.topografix.com/GPX/1/1')
    gpx.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    gpx.set('xsi:schemaLocation', 'http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd')
    
    # Extract track information
    if 'data' in track_data and 'track' in track_data['data']:
        track_info = track_data['data']['track']
        # Use the formatted date-time if available
        if 'start_at_str_format' in track_info:
            track_name = f"Ski Track - {track_info['start_at_str_format']}"
        else:
            track_name = f"Ski Track - {track_info.get('start_at_str', 'Unknown')}"
        
        # Get resort name if available
        if 'ski_ranch' in track_data['data'] and 'name' in track_data['data']['ski_ranch']:
            resort_name = track_data['data']['ski_ranch']['name']
            track_name = f"{track_name} at {resort_name}"
    else:
        track_name = "Ski Track"
    
    # Add metadata
    metadata = ET.SubElement(gpx, 'metadata')
    name = ET.SubElement(metadata, 'name')
    name.text = track_name
    
    # Extract GPS coordinates (track_detail) and altitude/time data (altitude_arr)
    runs = []
    altitude_data = []
    total_points = 0
    
    if 'data' in track_data:
        if 'track_detail' in track_data['data']:
            # track_detail is a collection of runs, with each run being a list of coordinates
            runs = track_data['data']['track_detail']
            for run in runs:
                total_points += len(run)
            print(f"Found {len(runs)} ski runs with a total of {total_points} coordinate points")
        
        if 'altitude_arr' in track_data['data']:
            altitude_data = track_data['data']['altitude_arr']
            if altitude_data and isinstance(altitude_data[0], list) and len(altitude_data[0]) >= 2:
                # If altitude_arr exists and has the expected format
                print(f"Found altitude/time data")
    
    if not runs:
        raise ValueError("No coordinate data found in the track data")
    
    # Create track element
    trk = ET.SubElement(gpx, 'trk')
    trk_name = ET.SubElement(trk, 'name')
    trk_name.text = track_name
    
    # Get the max altitude for default elevation if needed
    default_elevation = None
    if 'data' in track_data and 'track' in track_data['data']:
        default_elevation = track_data['data']['track'].get('max_altitude_meter')
    
    # Process each run as a separate trkseg
    total_added_points = 0
    
    # Get time offset from track start time if available
    start_time = None
    if 'data' in track_data and 'track' in track_data['data']:
        start_time = track_data['data']['track'].get('start_at')
    
    # Process each run
    for run_idx, run in enumerate(runs):
        # Create a new track segment for this run
        trkseg = ET.SubElement(trk, 'trkseg')
        run_points = 0
        
        # Process each point in the run
        for point_idx, coord in enumerate(run):
            if len(coord) >= 2:  # Ensure we have at least lon, lat
                trkpt = ET.SubElement(trkseg, 'trkpt')
                # In GPX format, latitude comes first as an attribute
                trkpt.set('lat', str(coord[1]))  # Latitude is second in coordinate
                trkpt.set('lon', str(coord[0]))  # Longitude is first in coordinate
                
                # Add elevation if available from altitude_arr
                # Note: altitude_arr may not directly map to track points, so we need to be careful
                if altitude_data and run_idx < len(altitude_data) and point_idx < len(altitude_data[run_idx]):
                    alt_point = altitude_data[run_idx][point_idx]
                    if isinstance(alt_point, list) and len(alt_point) >= 1:
                        ele = ET.SubElement(trkpt, 'ele')
                        ele.text = str(alt_point[0])  # First element is elevation
                        
                        # Add time if available
                        if len(alt_point) >= 2 and isinstance(alt_point[1], str):
                            time_str = alt_point[1]  # Second element is timestamp string
                            timestamp = parse_timestamp(time_str)
                            if timestamp:
                                # Adjust for timezone offset
                                timestamp = timestamp + datetime.timedelta(hours=timezone_offset)
                                time_elem = ET.SubElement(trkpt, 'time')
                                time_elem.text = timestamp.strftime('%Y-%m-%dT%H:%M:%S') + f"{timezone_offset:+03d}:00"
                elif default_elevation is not None:
                    # Use default elevation if no specific elevation data
                    ele = ET.SubElement(trkpt, 'ele')
                    ele.text = str(default_elevation)
                
                # Add time based on start_time if we don't have specific time data but have start_time
                if start_time and trkpt.find('time') is None:
                    time_elem = ET.SubElement(trkpt, 'time')
                    point_time = datetime.datetime.fromtimestamp(start_time + total_added_points + point_idx)
                    # Adjust for timezone offset
                    point_time = point_time + datetime.timedelta(hours=timezone_offset)
                    time_elem.text = point_time.strftime('%Y-%m-%dT%H:%M:%S') + f"{timezone_offset:+03d}:00"
                
                run_points += 1
        
        total_added_points += run_points
        print(f"Added {run_points} points from RUN {run_idx+1}")
    
    print(f"Total points added to the GPX file: {total_added_points}")
    return ET.ElementTree(gpx)

def load_json_file(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_gpx(gpx_tree, output_file):
    """Save the GPX tree to a file."""
    gpx_tree.write(output_file, encoding='utf-8', xml_declaration=True)

def process_track(url, timezone_offset=0, output_dir=None):
    """Process a single track URL and return the output filename."""
    try:
        # Extract UUID from URL
        track_uuid = extract_track_uuid(url)
        print(f"Extracted track UUID: {track_uuid}")
        
        print(f"Fetching track data...")
        track_data = fetch_track_data(track_uuid)
        
        # Generate default filename based on date and resort
        output_file = get_default_filename(track_data)
        
        # If output directory is specified, prepend it to the filename
        if output_dir:
            output_file = os.path.join(output_dir, output_file)
        
        print(f"Converting to GPX format with timezone offset: {timezone_offset} hours...")
        gpx_tree = create_gpx(track_data, timezone_offset)
        
        print(f"Saving to {output_file}...")
        save_gpx(gpx_tree, output_file)
        
        print(f"Conversion completed successfully. The GPX file is saved to {output_file}")
        return output_file
    
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
        return None

def handle_duplicate_filenames(files):
    """Handle duplicate filenames by adding sequential numbers."""
    # Group files by base filename
    filename_groups = {}
    for file in files:
        if file:  # Skip None values
            base_name = os.path.splitext(file)[0]
            if base_name not in filename_groups:
                filename_groups[base_name] = []
            filename_groups[base_name].append(file)
    
    # Rename files in groups with more than one file
    for base_name, group in filename_groups.items():
        if len(group) > 1:
            for i, file in enumerate(group, 1):
                new_name = f"{base_name}_{i}.gpx"
                if file != new_name:  # Only rename if the name is different
                    os.rename(file, new_name)
                    print(f"Renamed {file} to {new_name}")

def main():
    parser = argparse.ArgumentParser(description='Convert Huabei ski tracks to GPX format')
    parser.add_argument('urls', nargs='+', help='Huabei shared URLs')
    parser.add_argument('-o', '--output-dir', help='Output directory for GPX files')
    parser.add_argument('-t', '--timezone', type=int, default=0, 
                      help='Timezone offset in hours (e.g., -7 for Mountain Time, 8 for China Standard Time)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    if args.output_dir and not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Process all tracks
    output_files = []
    for url in args.urls:
        output_file = process_track(url, args.timezone, args.output_dir)
        if output_file:
            output_files.append(output_file)
    
    # Handle duplicate filenames
    handle_duplicate_filenames(output_files)
    
    return 0

if __name__ == "__main__":
    exit(main())
