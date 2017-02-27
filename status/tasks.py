#!/usr/bin/env python
'''
status.tasks
'''
from app import celery, app
from datetime import datetime
from celery.utils.log import get_task_logger
from urllib import urlencode
import status.clocks as clock
import json
import os
import logging
import time
import re
import collections
import requests

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


STATUS_FAIL = -1
STATUS_OK = 0


def write_json(data):
    '''
    Returns true if data was successfully written to JSON file
    '''
    json_file = app.config['STATUS_JSON']
    logger.info('json_file: %s', json_file)
    if json_file is None:
        logger.error('JSON FILE IS NONE')
        return False

    with open(json_file, 'wb') as f:
        f.write(json.dumps(data))

    logger.info('Updated %s', json_file)
    return True


def get_trajectory(erddap_url):
    '''
    Reads the trajectory information from ERDDAP and returns a GEOJSON like
    structure.
    '''
    # http://data.ioos.us/gliders/erddap/tabledap/ru01-20140104T1621.json?latitude,longitude&trajectory=%22ru01-20140104T1621%22
    url = erddap_url.replace('html', 'json')
    url += '?longitude,latitude'
    response = requests.get(url)
    if response.status_code != 200:
        raise IOError("Failed to get trajectories")
    data = response.json()
    geo_data = {
        'type': 'LineString',
        'coordinates': data['table']['rows']
    }
    return geo_data


def write_trajectory(deployment, geo_data):
    '''
    Writes a geojson like python structure to the appropriate data file
    '''
    trajectory_dir = app.config.get('TRAJECTORY_DIR')
    username = deployment['username']
    name = deployment['name']
    dir_path = os.path.join(trajectory_dir, username)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    file_path = os.path.join(dir_path, name + '.json')
    with open(file_path, 'wb') as f:
        f.write(json.dumps(geo_data))


@celery.task()
def get_trajectory_features():
    erddap_url = app.config.get('ERDDAP_URL')
    deployments_url = app.config.get('DAC_API')

    response = requests.get(deployments_url)
    if response.status_code != 200:
        raise IOError("Failed to get response from DAC ACPI")
    data = response.json()
    deployments = data['results']
    for d in deployments:
        logger.info("Reading deployment %s", d['deployment_dir'])
        try:
            geo_data = get_trajectory(d['erddap'])
            write_trajectory(d, geo_data)
        except IOError:
            logger.exception("Failed to get trajectory for %s",
                             d['deployment_dir'])

    return deployments


@celery.task()
def get_dac_status():
    dac_api_url = app.config.get('DAC_API')
    erddap_url = app.config.get('ERDDAP_URL')
    deployment_url_template = 'http://data.ioos.us/gliders/providers/deployment/{:s}'
    tds_url_template = 'http://data.ioos.us/gliders/thredds/dodsC/deployments/{:s}/{:s}/catalog.html?dataset=deployments/{:s}/{:s}/{:s}.nc3.nc'
    deployments = {
        'meta': {
            'fetch_time': time.strftime('%b %d, %Y %H:%M Z', time.gmtime())
        },
        'datasets': []
    }

    variables = {
        'datasetID': 'datasetID',
        'institution': 'institution',
        'title': 'title',
        'minLongitude': 'west',
        'maxLongitude': 'east',
        'minLatitude': 'south',
        'maxLatitude': 'north',
        'minTime': 'ts0',
        'maxTime': 'ts1',
        'subset': 'subset',
        'tabledap': 'tabledap',
        'MakeAGraph': 'graph',
        'fgdc': 'fgdc',
        'metadata': 'meta',
        'rss': 'rss',
        'summary': 'summary'
    }
    columns = variables.keys()
    # Time coverage regexs
    t0_re = re.compile(
        'time_coverage_start\s"(\d{4}\-\d{2}\-\d{2}T\d{2}:\d{2}:\d{2}Z)"')
    t1_re = re.compile(
        'time_coverage_end\s"(\d{4}\-\d{2}\-\d{2}T\d{2}:\d{2}:\d{2}Z)"')
    # Request the dac deployments metadata
    logger.info('Fetching DAC deployments: %s', dac_api_url)
    dac_request = requests.get(dac_api_url)
    if dac_request.status_code != 200:
        logger.error('ERDDAP request failed: %s (%s)',
                     dac_api_url, dac_request.reason)
        return False

    # Request the ERDDAP dataset metadata
    logger.info('Fetching ERDDAP datasets: %s', erddap_url)
    erddap_request = requests.get(erddap_url)
    if erddap_request.status_code != 200:
        logger.error('DAC request failed: %s (%s)',
                     erddap_url, erddap_request.reason)
        return False

    # Fetch the results from both requests
    try:
        dac_data = dac_request.json()['results']
        dac_request.close()
    except ValueError as e:
        logger.exception("Failed to convert DAC response from JSON")
        return False

    try:
        erddap_data = erddap_request.json()['table']
        erddap_request.close()
    except ValueError as e:
        logger.exception("Failed to conver ERDDAP response from JSON")
        return False

    # ERDDAP tabledap url index
    tabledap_index = erddap_data['columnNames'].index('tabledap')
    # ERDDAP datasetID index
    id_index = erddap_data['columnNames'].index('datasetID')
    # Create a list of dataset ids
    dataset_ids = [record[id_index] for record in erddap_data['rows']]

    # Loop through each deployment in dac_data.  Add erddap_data metadata if an
    # ERDDAP dataset exist
    for dac_record in dac_data:

        # Initialize the metadata record
        meta = {variables[column]: None for column in columns}

        # Initialize a few other keys
        meta['status'] = None
        meta['wmo_id'] = None
        meta['num_profiles'] = 0
        meta['ts0'] = None
        meta['ts1'] = None
        meta['start'] = None
        meta['end'] = None

        # Create and add the dac2.0 deployment url
        meta['dac_url'] = deployment_url_template.format(dac_record['id'])

        # If the dac deployment name is in the ERDDAP dataset_ids, make an ERDDAP
        # request and fill in the missing metadata
        if dac_record['name'] in dataset_ids:
            i = dataset_ids.index(dac_record['name'])
            for column in columns:
                col_id = erddap_data['columnNames'].index(column)
                meta[variables[column]] = erddap_data['rows'][i][col_id]

            dataset_id = erddap_data['rows'][i][id_index]
            das_url = '.'.join([erddap_data['rows'][i][tabledap_index], 'das'])

            # Request the ERDDAP Data Attribute Structure (.das) document
            logger.info('Fetching das: %s', das_url)
            das_request = requests.get(das_url)
            if das_request.status_code != 200:
                logger.error('das request failed: %s (%s)',
                             das_url, das_request.reason)
                continue

            # Parse the global:time_coverage_start attribute
            t0_match = t0_re.search(das_request.text)
            t0_epoch = None
            if not t0_match:
                logger.error(
                    '%s: No time_coverage_start regex match', dataset_id)
            else:
                t0_epoch = clock.erddap_ts2epoch(t0_match.groups()[0])

            # Parse the global:time_coverage_end attribute
            t1_match = t1_re.search(das_request.text)
            t1_epoch = None
            if not t1_match:
                logger.error(
                    '%s: No time_coverage_end regex match', dataset_id)
            else:
                # Convert the time_coverage_end to epoch seconds and set the bootstrap
                # contextual class
                t1_epoch = clock.erddap_ts2epoch(t1_match.groups()[0])

            # Add the time coverages
            meta['ts0'] = t0_match.groups()[0]
            meta['ts1'] = t1_match.groups()[0]
            meta['start'] = t0_epoch * 1000
            meta['end'] = t1_epoch * 1000

            if dataset_id.find('all') == -1 and dataset_id.find('development') == -1:
                json_url = meta['tabledap'] + '.json'
                data_url = '?'.join([json_url, 'wmo_id,profile_id'])
                logger.info('Fetching data url: %s', data_url)
                r = requests.get(data_url)
                if r.status_code != 200:
                    logger.error('Dataset fetch error: %s', r.reason)
                    continue

                data = r.json()
                # Create an array of wmo ids returned by query
                wmo_ids = [row[0] for row in data['table']['rows'] if row[0]]
                if len(wmo_ids) > 0:
                    meta['wmo_id'] = wmo_ids[0]

                # Create an array of profile numbers
                profiles = [row[1] for row in data['table']['rows'] if row[1]]
                if len(profiles) > 0:
                    meta['num_profiles'] = max(profiles)

        for name in dac_record.keys():
            meta[name] = dac_record[name]

        # Try to fetch the THREDDS .das to see if the dataset exists
        tds_das_url = tds_url_template.format(meta['username'],
                                              meta['name'],
                                              meta['username'],
                                              meta['name'],
                                              meta['name'])
        logger.info('Fetching THREDDS catalog: %s', tds_das_url)
        tds_request = requests.get(tds_das_url)
        meta['tds'] = None
        if tds_request.status_code == 200:
            meta['tds'] = tds_das_url.replace('.das', '.html')

        # Add the deployment metadata to the return object
        deployments['datasets'].append(collections.OrderedDict(
            sorted(meta.items(), key=lambda t: t[0])))

    status = write_json(deployments)
    return status
