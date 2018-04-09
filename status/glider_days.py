#!/usr/bin/env python
'''
status.glider_days

Helper methods for calculating the number of glider days in a deployment
for each glider operator
'''

import requests
import json
import pandas as pd
from collections import OrderedDict
from datetime import datetime, timedelta

def glider_days(year):
    '''
    Returns csv contents that has total number of
    glider days from GliderDAC for each operator

    :param str year: The year you want the stats from
    '''
    if year is not None:
        year = int(year)  # Convert string to int
    deployment_url = 'https://data.ioos.us/gliders/providers/api/deployment'
    response = requests.get(deployment_url)
    if response.status_code != 200:
        raise IOError("Failed to connect to GliderDAC Status API")
    data = response.json()['results']
    df = pd.DataFrame([get_glider_days(s, year) for s in data])

    return df[df.glider_days != 0].to_csv(index=False)


def get_glider_days(glider_res, year=None):
    '''
    Returns a dict of of total days of glider deployments per operator

    :param dict glider_res: Dictionary of deployment stats from an operator
    :param int year: Integer of the year you want the stats from
    '''
    # If year is not passed in, just do the current year
    if year is None:
        now = datetime.utcnow()
        year = now.year
    year_start = datetime(year, 1, 1)
    year_start_str = year_start.strftime("%Y-%m-%dT%H:%M")
    year_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    year_end_str = year_end.strftime("%Y-%m-%dT%H:%M")

    rtn_struct =  OrderedDict()
    rtn_struct['operator'] = glider_res['operator']
    rtn_struct['deployment'] = glider_res['name']
    rtn_struct['glider_days'] = 0
    templ = 'https://data.ioos.us/gliders/erddap/info/{}/index.csv'

    try:
        meta = pd.read_csv(templ.format(rtn_struct['deployment']),
                           index_col='Attribute Name')
    except:
        rtn_struct['glider_days'] = -2
        return rtn_struct
    try:
        start_time = pd.to_datetime(meta.loc['time_coverage_start'].Value)
        end_time = pd.to_datetime(meta.loc['time_coverage_end'].Value)
    except KeyError:
        # if there's no coverage start/end, then it's hard to determine the
        # exact number of days
        rtn_struct['glider_days'] = -1
        return rtn_struct

    if end_time < pd.Timestamp(year_start_str):
        rtn_struct['glider_days'] = 0
        return rtn_struct
    elif start_time > end_time:
        raise ValueError('Start time is greater than end time')
    elif pd.Timestamp(year_start_str) > start_time:
        start_time = pd.Timestamp(year_start_str)
    if end_time > pd.Timestamp(year_end_str):
        end_time = pd.Timestamp(year_end_str)

    # default case both within year
    rtn_struct['glider_days'] = (end_time - start_time).days

    return rtn_struct
