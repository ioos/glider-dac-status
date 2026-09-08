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
from haversine import haversine, Unit
import shutil

@lru_cache
def get_land_geom():
    """
    Load the Natural Earth land polygons and return an STRtree.
    """
    app.logger.info("Creating land mask")
    land_shp = shpreader.natural_earth(
        resolution="10m",
        category="physical",
        name="land",
    )
    
    return STRtree(
        list(shpreader.Reader(land_shp).geometries())
    )


# ---------------------------------------------------------------------------
# Distance and filtering functions
# ---------------------------------------------------------------------------
def calculate_distance_km(point_a, point_b):
    """
    Calculate the distance between two points.

    Coordinates must be provided as: (longitude, latitude)

    The haversine package expects: (latitude, longitude)
    """
    lon_a, lat_a = point_a
    lon_b, lat_b = point_b

    return haversine(
        (lat_a, lon_a),
        (lat_b, lon_b),
        unit=Unit.KILOMETERS,
    )


def parse_iso_time(value):
    """
    Parse an ERDDAP ISO timestamp.

    Expected format: YYYY-MM-DDTHH:MM:SSZ
    """
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


def add_filter_log(log, step_name, before_n, after_n, removed=None, note=None):
    """
    Add a filter summary to the processing log.
    """
    log.append({
        "step": step_name,
        "before": before_n,
        "after": after_n,
        "removed": before_n - after_n,
        "note": note,
        "removed_points": removed or [],
    })


def filter_by_min_time(coords, times, flags=None, min_time=None):
    """
    Remove points occurring before min_time or having invalid timestamps.

    Returns
    -------
    tuple
        filtered coordinates, times, flags, and removed-point details
    """
    if not min_time:
        return coords, times, flags, []

    min_datetime = datetime.strptime(min_time, "%Y%m%dT%H%M")

    kept = []
    removed = []

    flag_iter = flags if flags is not None else repeat(None)

    for coordinate, timestamp, flag in zip(coords, times, flag_iter):
        lon, lat = coordinate

        try:
            keep = parse_iso_time(timestamp) >= min_datetime
        except (TypeError, ValueError):
            keep = False

        if keep:
            kept.append((coordinate, timestamp, flag))
        else:
            removed.append({
                "lon": lon,
                "lat": lat,
                "time": timestamp,
                "flag": flag,
                "reason": "before min_time or invalid time",
            })

    filtered_coords = [item[0] for item in kept]
    filtered_times = [item[1] for item in kept]

    if flags is not None:
        filtered_flags = [item[2] for item in kept]
    else:
        filtered_flags = None

    return filtered_coords, filtered_times, filtered_flags, removed


def filter_invalid_coordinates(coords, times, flags=None):
    """
    Remove points with missing coordinates or invalid QC flags.

    A QC flag is considered valid when it is either None or equal to 1.
    """
    kept = []
    removed = []

    flag_iter = flags if flags is not None else repeat(None)

    for coordinate, timestamp, flag in zip(coords, times, flag_iter):
        lon, lat = coordinate

        if lon is None or lat is None:
            removed.append({
                "lon": lon,
                "lat": lat,
                "time": timestamp,
                "flag": flag,
                "reason": "missing lon or lat",
            })
            continue

        if flag is not None and flag != 1:
            removed.append({
                "lon": lon,
                "lat": lat,
                "time": timestamp,
                "flag": flag,
                "reason": "flag != 1",
            })
            continue

        kept.append((coordinate, timestamp, flag))

    filtered_coords = [item[0] for item in kept]
    filtered_times = [item[1] for item in kept]

    if flags is not None:
        filtered_flags = [item[2] for item in kept]
    else:
        filtered_flags = None

    return filtered_coords, filtered_times, filtered_flags, removed


def _land_tree_indices(land_tree, points):
    """
    Return the indices of points that intersect land.

    Shapely 2.x returns an array of tree indices for a vectorized query.
    This function also handles the older query behavior that may return
    geometry objects.
    """
    if not points:
        return set()

    try:
        query_result = land_tree.query(
            points,
            predicate="intersects",
        )

        if len(query_result) == 0:
            return set()

        query_array = np.asarray(query_result)

        # Shapely 2.x vectorized query returns a 2 x N array:
        # [input_geometry_index, tree_geometry_index]
        if query_array.ndim == 2 and query_array.shape[0] == 2:
            return set(query_array[0].tolist())

        # Some Shapely versions may return a one-dimensional array
        # containing input indices.
        if query_array.ndim == 1 and np.issubdtype(
            query_array.dtype,
            np.integer,
        ):
            return set(query_array.tolist())

    except Exception as exc:
        app.logger.error("Land mask query failed: %s", exc)

    return set()


def filter_land_points(coords, times):
    """
    Remove coordinate points that intersect land.
    """
    if not coords:
        return [], [], []

    try:
        land_tree = get_land_geom()
        points = [Point(lon, lat) for lon, lat in coords]
        land_indices = _land_tree_indices(land_tree, points)
    except Exception as exc:
        app.logger.error("Step 2 land mask error: %s", exc)
        land_indices = set()

    kept = []
    removed = []

    for index, (coordinate, timestamp) in enumerate(zip(coords, times)):
        lon, lat = coordinate

        if index in land_indices:
            removed.append({
                "lon": lon,
                "lat": lat,
                "time": timestamp,
                "flag": None,
                "reason": "on land",
            })
        else:
            kept.append((coordinate, timestamp))

    filtered_coords = [item[0] for item in kept]
    filtered_times = [item[1] for item in kept]

    return filtered_coords, filtered_times, removed


def filter_large_jumps(coords, times, max_jump_km):
    """
    Remove points that are farther than max_jump_km from the previous
    accepted point.

    The first point is always retained.
    """
    if not coords:
        return [], [], []

    cleaned_coords = [coords[0]]
    cleaned_times = [times[0]]
    removed = []

    for index in range(1, len(coords)):
        previous_point = cleaned_coords[-1]
        current_point = coords[index]

        distance_km = calculate_distance_km(
            previous_point,
            current_point,
        )

        if distance_km > max_jump_km:
            removed.append({
                "index": index,
                "lon": current_point[0],
                "lat": current_point[1],
                "time": times[index],
                "distance_km": distance_km,
                "reason": (
                    f"distance > max_jump_km ({max_jump_km} km)"
                ),
            })
            continue

        cleaned_coords.append(current_point)
        cleaned_times.append(times[index])
        
    return cleaned_coords, cleaned_times, removed


# ---------------------------------------------------------------------------
# ERDDAP handling
# ---------------------------------------------------------------------------
def get_trajectory(erddap_url):
    """
    Read trajectory information from ERDDAP and return a GeoJSON-like
    structure.

    The trajectory is filtered from the deployment date onward.
    """
    min_time = (
        erddap_url
        .split("/")[-1]
        .replace(".html", "")
        .split("-")[-1]
    )

    url = erddap_url.replace(".html", ".json")

    response = None
    last_url = None

    app.logger.info("Trying dataset related to: %s", erddap_url)

    for qc_append in (
        "qartod_location_test_flag,",
        "",
    ):
        last_url = (
            f"{url}?profile_id,longitude,latitude,"
            f"{qc_append}time&orderBy(%22time%22)"
        )

        try:
            response = requests.get(
                last_url,
                timeout=180,
                allow_redirects=True,
            )
            response.raise_for_status()
            break
        except RequestException as exc:
            app.logger.error(
                "Failed to fetch trajectory from %s: %s",
                last_url,
                exc,
            )
            response = None

    if response is None:
        raise RuntimeError(
            f"Failed to fetch trajectory data from {url}"
        )

    data = response.json()

    column_names = data["table"]["columnNames"]
    rows = data["table"]["rows"]

    profile_idx = column_names.index("profile_id")
    lon_idx = column_names.index("longitude")
    lat_idx = column_names.index("latitude")
    time_idx = column_names.index("time")

    flag_idx = (
        column_names.index("qartod_location_test_flag")
        if "qartod_location_test_flag" in column_names
        else None
    )

    geo_data = {
        "type": "LineString",
        "profileid": [row[profile_idx] for row in rows],
        "coordinates": [
            (row[lon_idx], row[lat_idx])
            for row in rows
        ],
        "time": [row[time_idx] for row in rows],
        "flag": (
            [row[flag_idx] for row in rows]
            if flag_idx is not None
            else None
        ),
    }

    raw_coords = geo_data["coordinates"]

    cleaned = parse_geometry_with_checks(
        geo_data,
        has_flag=geo_data["flag"] is not None,
        min_time=min_time,
        max_jump_km=200,
    )

    cleaned_coords = cleaned["coordinates"]

    if len(cleaned_coords) >= 2:
        trajectory = LineString(cleaned_coords).simplify(
            0.02,
            preserve_topology=False,
        )
        geometry = {
            "type": "LineString",
            "coordinates": list(trajectory.coords),
            "properties": {
                "oceansmap_type": "glider",
            },
        }
    elif len(cleaned_coords) == 1:
        geometry = {
            "type": "Point",
            "coordinates": cleaned_coords[0],
            "properties": {
                "oceansmap_type": "glider",
            },
        }
    else:
        geometry = {
            "type": "LineString",
            "coordinates": [],
            "properties": {
                "oceansmap_type": "glider",
            },
        }

    return {
        "raw_coordinates": raw_coords,
        "cleaned_coordinates": cleaned_coords,
        "geometry": geometry,
        "logs": cleaned["log"],
    }
    


# ---------------------------------------------------------------------------
# Geometry processing
# ---------------------------------------------------------------------------
def parse_geometry_with_checks(
    geometry,
    has_flag,
    min_time=None,
    max_jump_km=200,):
    """
    Filter trajectory coordinates using the following steps:

    1. Minimum timestamp filtering.
    2. Missing coordinate and QC flag filtering.
    3. Land masking.
    4. Large-jump distance filtering.

    Returns
    -------
    dict
        Contains profile IDs, cleaned coordinates, times, and filter logs.
    """
    coords = geometry.get("coordinates", [])
    times = geometry.get("time", [])
    flags = geometry.get("flag", []) if has_flag else None
    profileid = geometry.get("profileid")

    log = []

    # Step 0: Minimum time filter
    before_n = len(coords)

    coords, times, flags, removed = filter_by_min_time(
        coords,
        times,
        flags,
        min_time,
    )

    add_filter_log(
        log,
        "step_0_time_filter",
        before_n,
        len(coords),
        removed=removed,
        note=(
            f"min_time={min_time}"
            if min_time
            else "No min_time filter applied"
        ),
    )

    # Step 1: Missing values and QC flag filter
    before_n = len(coords)

    coords, times, flags, removed = filter_invalid_coordinates(
        coords,
        times,
        flags,
    )

    add_filter_log(
        log,
        "step_1_flag_and_missing_filter",
        before_n,
        len(coords),
        removed=removed,
        note="Kept points with valid coordinates and acceptable flags",
    )

    # Step 2: Land mask
    before_n = len(coords)

    coords, times, removed = filter_land_points(
        coords,
        times,
    )

    add_filter_log(
        log,
        "step_2_land_mask",
        before_n,
        len(coords),
        removed=removed,
        note="Removed points that fall on land",
    )

    # Step 3: Large-jump filter
    before_n = len(coords)

    coords, times, removed = filter_large_jumps(
        coords,
        times,
        max_jump_km,
    )

    add_filter_log(
        log,
        "step_3_big_jump_filter",
        before_n,
        len(coords),
        removed=removed,
        note=f"max_jump_km={max_jump_km} km",
    )

    return {
        "profileid": profileid,
        "coordinates": coords,
        "times": times,
        "log": log,
    }


# ---------------------------------------------------------------------------
# File handling
# ---------------------------------------------------------------------------
def get_path(deployment):
    '''
    Returns the path of the trajectory file

    :param dict deployment: Dictionary containing the deployment metadata
    '''
    trajectory_dir = app.config.get('TRAJECTORY_DIR')
    username = deployment['username']
    dir_path = os.path.join(trajectory_dir, username)
    os.makedirs(dir_path, exist_ok=True)
    
    return dir_path


def write_trajectory(deployment, geo_data):
    '''
    Write the trajectory GeoJSON-like structure to disk.
    
    :param dict deployment: Dictionary containing the deployment metadata
    :param dict geo_data: A GeoJSON Geometry object
    '''
    name = deployment['name']
    dir_path = get_path(deployment)
    file_path = os.path.join(dir_path, f"{name}.json")
    
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(geo_data, file)


def write_trajectory_log(deployment, log_data):
    '''
    Write trajectory filtering issues to disk.
    
    :param dict deployment: Dictionary containing the deployment metadata
    :param dict log_data: A dictionary containing trajectory (lat/lon) outliers
    '''
    name = deployment['name']
    dir_path = get_path(deployment)
    log_path = os.path.join(dir_path, f"{name}_log.json")
    
    with open(log_path, "w", encoding="utf-8") as file:
        json.dump(log_data, file)
    

def move_trajectory_log(deployment):
    '''
    Move the current trajectory log into the past_issues directory.
    
    :param dict deployment: Dictionary containing the deployment metadata
    '''
    name = deployment['name']
    dir_path = get_path(deployment)
    log_path = os.path.join(dir_path, f"{name}_log.json")
    target_path = os.path.join(dir_path, 'past_issues')
    if os.path.exists(log_path):
        os.makedirs(target_path, exist_ok=True)
        shutil.move(log_path, target_dir)

def trajectory_exists(deployment):
    '''
    Return True if a trajectory file already exists.

    :param dict deployment: Dictionary containing the deployment metadata
    '''

    dir_path = get_path(deployment)
    file_path = os.path.join(dir_path, f"{deployment['name']}.json")
    
    return os.path.exists(file_path)


# ---------------------------------------------------------------------------
# Trajectory generation
# ---------------------------------------------------------------------------
def generate_trajectories(deployments=None):
    """
    Determine which trajectories need to be built and write them to disk.
    """
    for deployment in iter_deployments():
        if (
            deployments is not None
            and deployment["name"] not in deployments
        ):
            continue

        try:
            recent_update = is_recent_update(
                deployment["updated"]
            )
            recent_data = is_recent_data(deployment)
            existing_trajectory = trajectory_exists(deployment)
            
            should_generate = (
                not deployment["name"].endswith("-delayed")
                and (
                    recent_update
                    or recent_data
                    or not existing_trajectory
                    or not deployment["completed"]
                )
            )    
            
            if not should_generate:
                continue
            
            geo_data = get_trajectory(
                deployment["erddap"]
            )

            write_trajectory(
                deployment,
                geo_data["geometry"],
            )

            log_issues = [
                entry
                for entry in geo_data["logs"]
                if entry.get("removed_points")
            ]
            
            if log_issues:
                write_trajectory_log(
                    deployment,
                    log_issues,
                )
            else:
                move_trajectory_log(deployment)

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
