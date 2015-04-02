#!/usr/bin/env python
'''
navo/tasks.py

Author: Luke Campbell

Parse the time, lat, and lon from the glider emails
'''
from dateutil.parser import parse as dateparse
from datetime import timedelta
import csv
import re
import glob
import os
import json

def parse(email_path):
    with open(email_path, 'r') as f:
        buf = f.read()
    lines = buf.split('\n')
    current_time = parse_current_time(lines)
    lat, lon, delta_time = parse_gps(lines)
    current_time = current_time - timedelta(seconds=delta_time)
    return current_time, lat, lon


def parse_current_time(email_lines):
    '''
    Parses out the current time from a list of lines from the Glider emails. 
    Returns a datetime object with the parsed time.
    The function expects the line to be of the format
        Curr Time: <date time string>
    '''
    time_regex = r'Curr Time: (.*) MT.*$'
    current_time = [l for l in email_lines if 'Curr Time:' in l]
    if not current_time:
        raise ValueError('Unable to find "Curr Time" in email')
    matches = re.match(time_regex, current_time[0])
    if not matches:
        raise ValueError('Unable to parse current time')
    groups = matches.groups()

    current_time = dateparse(groups[0])
    return current_time

def parse_gps(email_lines):
    '''
    Parses out the GPS
    '''
    gps_regex = r'GPS Location: *(-?[0-9]+\.?[0-9]*) N (-?[0-9]+\.?[0-9]*) E measured *(-?[0-9]+\.?[0-9]*).*$'
    gps_line = [l for l in email_lines if 'GPS Location:' in l]
    if not gps_line:
        raise ValueError('Unable to find "GPS Location" in email')
    matches = re.match(gps_regex, gps_line[0])
    if not matches:
        raise ValueError('Unable to parse GPS coordinates')

    lat, lon, delta_time = matches.groups()
    delta_time = float(delta_time)
    
    if '69696969' in lat:
        raise ValueError('Invalid GPS Coordinates detected')

    if '69696969' in lon:
        raise ValueError('Invalid GPS Coordinates detected')

    
    lat = parse_coordinate(lat)
    lon = parse_coordinate(lon)

    # These will generally be skipped
    if lat > 90 or lat < -90:
        raise ValueError('Invalid Lat')
    if lon > 180 or lon < -180:
        raise ValueError('Invalid Lon')

    return lat, lon, delta_time

def parse_coordinate(coordinate):
    gps_vector_regex = r'(-?)([0-9]{2})([0-9]{2}\.[0-9]{3,4})'
    
    match = re.match(gps_vector_regex, coordinate)
    if not match:
        raise ValueError('Unable to parse coordinate')

    groups = match.groups()

    deg, minutes = [float(i) for i in groups[1:]]

    coord = deg + (minutes/60.)
    if groups[0]:
        coord *= -1
    return coord


def dump_csv(csvfile, sorted_records):
    csvwriter = csv.writer(csvfile, delimiter=',', quotechar="'", quoting=csv.QUOTE_MINIMAL)
    csvwriter.writerow([
        'Date', 'lat', 'lon'
    ])
    for record in sorted_records:
        csvwriter.writerow([
            record[0].isoformat(),
            record[1],
            record[2]
        ])

def dump_json(json_file, sorted_records):
    coordinates = []
    times = []
    for record in sorted_records:
        coordinates.append([record[2], record[1]]) # GeoJSON goes lon,lat
        times.append(record[0].isoformat())

    geojson_record = {
        'type': 'Feature',
        'geometry' : {
            'type' : 'LineString',
            'coordinates': coordinates
        },
        "properties": {
            "times": times
        }
    }
    json_file.write(json.dumps(geojson_record))

    
def get_sorted_records(mail_folder):
    path = os.path.join(mail_folder, '*.txt')
    records = []
    for email_path in glob.glob(path):
        try:
            record = parse(email_path)
            records.append(record)

        except ValueError as e:
            continue
    sorted_records = sorted(records, key=lambda x: x[0])
    return sorted_records

def main(args):
    sorted_records = get_sorted_records(args.mail_folder)
    if args.json:
        with open(args.output, 'w') as json_file:
            dump_json(json_file, sorted_records)
    else:
        with open(args.output, 'w') as csvfile:
            dump_csv(csfile, sorted_records)

def update_cache():
    from flask import current_app as app
    cache = app.config['GLIDER_EMAIL']['OUTPUT_DIRECTORY']
    path = 'navo/static/json/trajectories.json'
    sorted_records = get_sorted_records(cache)
    with open(path, 'w') as f:
        dump_json(f, sorted_records)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Parse GPS Coordinates from Glider Emails')
    parser.add_argument('mail_folder', help='Folder containing .txt files of emails')
    parser.add_argument('output', help='Output file (CSV)')
    parser.add_argument('-j', '--json', action='store_true', help='Output file (CSV)')
    args = parser.parse_args()
    main(args)

