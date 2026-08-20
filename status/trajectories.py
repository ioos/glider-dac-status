#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import requests
import sys
from app import app
from shapely.geometry import LineString
import shapely.geometry as sgeom
from shapely.strtree import STRtree
from status.profile_plots import iter_deployments, is_recent_data, is_recent_update
from requests.exceptions import RequestException
import numpy as np
from datetime import datetime
from functools import lru_cache

import os
os.environ["CARTOPY_USER_BACKGROUNDS"] = "/tmp/cartopy"
os.environ["CARTOPY_DATA_DIR"] = "/tmp/cartopy"

import cartopy.io.shapereader as shpreader
from itertools import repeat
from shapely.geometry import Point


@lru_cache
def get_land_geom():
    # Load higher-resolution land polygons for better accuracy
    app.logger.info("Creating land mask")
    land_shp = shpreader.natural_earth(resolution='10m', category='physical', name='land')
    global land_geom
    return STRtree(list(shpreader.Reader(land_shp).geometries()))


def get_trajectory(erddap_url):
    '''
    Reads the trajectory information from ERDDAP and returns a GEOJSON-like
    structure. Filters by min_time from deployment date.
    '''
    # Example URL:
    # https://gliders.ioos.us/erddap/tabledap/ru01-20140104T1621.json?latitude,longitude&time&orderBy(%22time%22)

    # get deployment time (e.g., 20250611T0000)
    min_time = erddap_url.split("/")[-1].replace(".html", "").split("-")[-1]

    # fix url with json extension
    url = erddap_url.replace("html", "json")

    # ERDDAP requires the variable being sorted to be present in the variable
    # list. The time variable will be removed before converting to GeoJSON

    valid_response = False
    app.logger.info(f"Trying dataset related to: {erddap_url}")
    for qc_append in ("qartod_location_test_flag,", ""):
        url_append = url + f"?longitude,latitude,{qc_append}time&orderBy(%22time%22)"
        try:
            response = requests.get(url_append, timeout=180, allow_redirects=True)
            response.raise_for_status()
        except RequestException as e:
            app.logger.info(f"{e}")
            continue
        else:
            valid_response = True
            break

    if not valid_response:
        app.logger.error(f"Failed to fetch trajectories: {url_append}")

    data = response.json()

    # Map rows into lon/lat/time/flag
    col_names = data["table"]["columnNames"]
    rows = data["table"]["rows"]

    # Identify column indices dynamically
    lon_idx = col_names.index("longitude")
    lat_idx = col_names.index("latitude")
    time_idx = col_names.index("time")
    flag_idx = col_names.index("qartod_location_test_flag") if "qartod_location_test_flag" in col_names else None

    geo_data = {
        "type": "LineString",
        "profileid": [r[profile_idx] for r in rows],
        "coordinates": [(r[lon_idx], r[lat_idx]) for r in rows],
        "time": [r[time_idx] for r in rows],
        "flag": [r[flag_idx] for r in rows] if flag_idx is not None else None,
    }

    raw_coords = geo_data["coordinates"]

    # Call your parse function with min_time filter and max jump distance
    cleaned = parse_geometry_with_checks(
        geo_data,
        has_flag=True,
        min_time=min_time,
        max_jump_m=200000
    )
     
    # Simplify trajectory
    coords = LineString(cleaned["coordinates"])
    trajectory = coords.simplify(0.02, preserve_topology=False)

    geometry = {
        "type": "LineString",
        "coordinates": list(trajectory.coords),
        "properties": {
            "oceansmap_type": "glider",
        }
    }

    return {
        "raw_coordinates": raw_coords,
        "cleaned_coordinates": cleaned["coordinates"],
        "geometry": geometry,
        "logs": cleaned["log"]}


def get_path(deployment):
    '''
    Returns the path to the trajectory file

    :param dict deployment: Dictionary containing the deployment metadata
    '''
    trajectory_dir = app.config.get('TRAJECTORY_DIR')
    username = deployment['username']
    name = deployment['name']
    dir_path = os.path.join(trajectory_dir, username)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    file_path = os.path.join(dir_path, name + '.json')
    return file_path


def write_trajectory(deployment, geo_data):
    '''
    Writes a geojson like python structure to the appropriate data file

    :param dict deployment: Dictionary containing the deployment metadata
    :param dict geometry: A GeoJSON Geometry object
    '''
    file_path = get_path(deployment)
    with open(file_path, 'w') as f:
        f.write(json.dumps(geo_data))

def parse_geometry_with_checks(geometry: dict, has_flag: bool, min_time: str = None, max_jump_m: float = 200000):
    """
    Filters out bad coordinate pairs based on:
      - minimum time threshold (if provided),
      - flags,
      - missing coordinates,
      - land masking,
      - distance-based big-jump detection.

    Returns
    -------
    dict with:
      - profileid
      - coordinates
      - times
      - log
    """

    coords = geometry.get("coordinates", [])
    times = geometry.get("time", [])
    flags = geometry.get("flag", []) if has_flag else None
    profileid = geometry.get("profileid")

    log = []

    def add_log(step_name, before_n, after_n, removed=None, note=None):
        log.append({
            "step": step_name,
            "before": before_n,
            "after": after_n,
            "removed": before_n - after_n,
            "note": note,
            "removed_points": removed or [],
        })

    def parse_iso_time(t):
        return datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ")

    #--------------------
    #Step 0: Time filter
    #--------------------
    before_n = len(coords)
    if min_time and times:
        min_dt = datetime.strptime(min_time, "%Y%m%dT%H%M")
        kept = []
        removed = []

        flag_iter = flags if has_flag else repeat(None)
    
        for (lon, lat), t, flag in zip(coords, times, flag_iter):
            try:
                keep = parse_iso_time(t) >= min_dt
            except Exception:
                keep = False

            if keep:
                kept.append(((lon, lat), t, flag))
            else:
                removed.append({
                    "lon": lon,
                    "lat": lat,
                    "time": t,
                    "flag": flag,
                    "reason": "before min_time or invalid time",
                })
        
        coords = [xy for xy, _, _ in kept]
        times = [t for _, t, _ in kept]
        if has_flag:
            flags = [f for _, _, f in kept]

        add_log(
            "step_0_time_filter",
            before_n,
            len(coords),
            removed=removed,
            note=f"min_time={min_time}",
        )
    else:
        add_log(
            "step_0_time_filter",
            before_n,
            before_n,
            removed=[],
            note="No min_time filter applied",
        )

    # -----------------------------------
    # Step 1: Flag / missing value filter
    # -----------------------------------
    before_n = len(coords)
    kept = []
    removed = []

    if has_flag:
        for (lon, lat), t, flag in zip(coords, times, flags):
            if lon is None or lat is None:
                removed.append({
                    "lon": lon,
                    "lat": lat,
                    "time": t,
                    "flag": flag,
                    "reason": "missing lon or lat",
                })
            elif flag is not None and flag != 1:
                removed.append({
                    "lon": lon,
                    "lat": lat,
                    "time": t,
                    "flag": flag,
                    "reason": "flag != 1",
                })
            else:
                kept.append(((lon, lat), t, flag))

        coords = [xy for xy, _, _ in kept]
        times = [t for _, t, _ in kept]
        flags = [f for _, _, f in kept]

    else:
        for (lon, lat), t in zip(coords, times):
            if lon is None or lat is None:
                removed.append({
                    "lon": lon,
                    "lat": lat,
                    "time": t,
                    "flag": None,
                    "reason": "missing lon or lat",
                })
            else:
                kept.append(((lon, lat), t))

        coords = [xy for xy, _ in kept]
        times = [t for _, t in kept]

    add_log(
        "step_1_flag_and_missing_filter",
        before_n,
        len(coords),
        removed=removed,
        note="Kept points with valid lon/lat and acceptable flag",
    )

    # --------------------
    # Step 2: Land masking
    # --------------------
    before_n = len(coords)
    kept = []
    removed = []

    if coords:
        try:
            land_tree = get_land_geom()
            app.logger.debug("returned land tree")
            app.logger.debug("query tree")
            pts = [Point(lon, lat) for lon, lat in coords]
            pairs = land_tree.query(pts, predicate="intersects")
            app.logger.debug("finish query tree")
            land_idx = np.unique(pairs[0]) if len(pairs) else np.array([], dtype=int)
            land_idx_set = set(land_idx.tolist())
        except Exception as e:
            print(f"Step 2 land mask error: {e}")
            land_idx_set = set()

        for i, ((lon, lat), t) in enumerate(zip(coords, times)):
            if i in land_idx_set:
                removed.append({
                    "lon": lon,
                    "lat": lat,
                    "time": t,
                    "flag": None,
                    "reason": "on land",
                })
            else:
                kept.append(((lon, lat), t))

    coords = [xy for xy, _ in kept]
    times = [t for _, t in kept]

    add_log(
        "step_2_land_mask",
        before_n,
        len(coords),
        removed=removed,
        note="Removed points that fall on land",
    )

    # --------------------
    # Step 3: Big-jump distance filter
    # --------------------
    # this is to verify if the outlier added manually are presentin the array    
    before_n = len(coords)
    if not coords:
        add_log(
            "step_3_big_jump_filter",
            before_n,
            0,
            removed=[],
            note="No coordinates left after earlier filters",
        )
        return {
            "profileid": profileid,
            "coordinates": [],
            "times": [],
            "log": log,
        }

    cleaned_coords = [coords[0]]
    cleaned_times = [times[0]]
    removed = []

    for i in range(1, len(coords)):
        prev_lon, prev_lat = cleaned_coords[-1]
        lon, lat = coords[i]
        dist = haversine(prev_lon, prev_lat, lon, lat)

        
        if dist > max_jump_m:
            removed.append({
                "index": i,
                "lon": lon,
                "lat": lat,
                "time": times[i],
                "distance_m": dist,
                "reason": f"distance > max_jump_m ({max_jump_m} m)",
            })
            continue

        cleaned_coords.append((lon, lat))
        cleaned_times.append(times[i])

    add_log(
        "step_3_big_jump_filter",
        before_n,
        len(cleaned_coords),
        removed=removed,
        note=f"max_jump_m={max_jump_m} m",
    )

    return {
        "profileid": profileid,
        "coordinates": cleaned_coords,
        "times": cleaned_times,
        "log": log, 
    }


def trajectory_exists(deployment):
    '''
    Returns True if the data is within the last week

    :param dict deployment: Dictionary containing the deployment metadata
    '''

    file_path = get_path(deployment)
    return os.path.exists(file_path)


def generate_trajectories(deployments=None):
    '''
    Determine which trajectories need to be built, and write geojson to file
    '''
    # TODO: Use a less brute force approach to filtering
    for deployment in iter_deployments():
        if deployments is not None and deployment["name"] not in deployments:
            continue
        try:
            # Only add if the deployment has been recently updated or the data is recent
            recent_update = is_recent_update(deployment['updated'])
            recent_data = is_recent_data(deployment)
            existing_trajectory = trajectory_exists(deployment)
            if (not deployment["name"].endswith("-delayed") and
                (recent_update or recent_data or not existing_trajectory
                or not deployment["completed"])):
                geo_data = get_trajectory(deployment['erddap'])
                write_trajectory(deployment, geo_data)
        except Exception:
            from traceback import print_exc
            print_exc()
    return 0


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(description=generate_trajectories.__doc__)
    parser.add_argument(
        '-d', '--deployment',
        action='append',
        help='Which deployment to build'
    )
    args = parser.parse_args()
    sys.exit(generate_trajectories(args.deployment))
