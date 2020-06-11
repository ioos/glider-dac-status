#!/usr/bin/env python
# -*- coding: utf-8 -*-


import boto3
import json
import requests
import sys
from datetime import datetime, timedelta
from flask import current_app


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
    last_updated = last_updated / 1000  # convert to seconds
    last_updated_dt = datetime.utcfromtimestamp(last_updated)
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
    # Create SQS client
    sqs = boto3.client(
        service_name='sqs',
        region_name=current_app.config['AWS']['REGION_NAME'],
        aws_access_key_id=current_app.config['AWS']['ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS']['SECRET_ACCESS_KEY'],
    )
    queue_url = current_app.config['AWS']['SQS_QUEUE_URL']

    for deployment in iter_deployments():
        try:
            for deployment_filter in deployments or []:
                if deployment_filter in deployment['deployment_dir']:
                    break
            else:
                if deployments:
                    continue

            # Only plot if the deployment has been recently updated or the data is recent
            recent_update = is_recent_update(deployment['updated'])
            recent_data = is_recent_data(deployment)
            if (recent_update or recent_data):
                # Send message to SQS queue
                message_body = dict(
                    thredds_url=deployment['dap']
                )
                sqs.send_message(
                    QueueUrl=queue_url,
                    DelaySeconds=10,
                    MessageBody=json.dumps(message_body)
                )
        except Exception:
            from traceback import print_exc
            print_exc()
    return 0


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
