#!/usr/bin/env python
# -*- coding: utf-8 -*-


import boto3
import json
import requests
import sys
from datetime import datetime, timedelta
from flask import current_app
from status.aws.docker.worker.generate_profile_plot import generate_profile_plot


def iter_deployments():
    '''
    Iterates over all of the GliderDAC deployments and returns the dictionary
    containing the deployment attributes.
    '''
    url = 'https://gliders.ioos.us/status/static/json/status.json'
    headers = {'Cache-Control': 'no-cache'}
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    results = response.json()
    for deployment in results['datasets']:
        yield deployment


def is_recent_update(last_updated):
    '''
    Returns True if deployment update time is within last week

    :param int last_updated: Last update time in milliseconds since 1970
    '''
    last_updated_dt = datetime.fromisoformat(last_updated)
    now = datetime.utcnow().timestamp()
    secs_elapsed = now - last_updated_dt.timestamp()
    one_week = 3 * 24 * 60 * 60
    return secs_elapsed < one_week


def is_recent_data(deployment):
    '''
    Returns True if the data is within the last week

    :param dict deployment: Dictionary containing the deployment metadata
    '''
    t0 = datetime.utcnow() - timedelta(days=7)
    try:
        end_time = datetime.utcnow()
        if 'ts1' in deployment:
            end_time = datetime.strptime(deployment['ts1'], '%Y-%m-%dT%H:%M:%SZ')
    except Exception:
        return False

    return t0 <= end_time

def generate_profile_plots(deployments=None):
    '''
    Builds a directory of profile plots from the GliderDAC deployments
    '''
    if current_app.config["USE_LAMBDA"]:
        lambda_client = boto3.client('lambda')
        def plot_function(erddap_url):
            lambda_client.invoke(
                FunctionName='invoke_generate_profile_plot',
                InvocationType='Event',    # async
                Payload=json.dumps({"erddap_dataset": erddap_url}).encode('utf-8'))
    else:
        plot_function = generate_profile_plot

    for deployment in iter_deployments():
        try:
            for deployment_filter in deployments or []:
                if deployment_filter in deployment['deployment_dir']:
                    break
            # If we have filters but the deployment was not found in the filters, continue
            # to other deployments
            else:
                if deployments:
                    continue

            # Only plot if the deployment has been recently updated or the data is recent
            recent_update = is_recent_update(deployment['updated'])
            recent_data = is_recent_data(deployment)
            if (not deployment["name"].endswith("-delayed")
                and (recent_update or recent_data or
                not deployment["completed"])):
                plot_function(deployment["erddap"])
        except Exception:
            from traceback import print_exc
            print_exc()


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(description=generate_profile_plots.__doc__)
    parser.add_argument(
        '-d', '--deployment',
        action='append',
        help='Which deployment to build'
    )
    args = parser.parse_args()
    sys.exit(generate_profile_plots(args.deployment))
