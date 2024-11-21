import matplotlib
matplotlib.use('AGG')
import matplotlib.dates as mdates
import boto3
import cmocean
import io
import logging
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
import os
import pandas as pd
from typing import Tuple
import urllib.error
import traceback
from datetime import datetime
from erddapy import ERDDAP


__version__ = '0.3.0'

PARAMETERS = {

    'salinity': {
        'cmap': cmocean.cm.haline,
        'display': u'Salinity'
    },
    'temperature': {
        'cmap': cmocean.cm.thermal,
        'display': u'Temperature (°C)'
    },
    'conductivity': {
        'cmap': cmocean.cm.haline,
        'display': u'Conductivity (S m-1)'
    },
    'density': {
        'cmap': cmocean.cm.dense,
        'display': u'Density (kg m-3)',
    }
}


def generate_profile_plot(erddap_dataset):
    '''
    Plot the parameters for a deployment
    :param str erddap_dataset: ERDDAP endpoint
    '''
    dataset_id = erddap_dataset.split('/')[-1].split('.html')[0]
    time_min, time_max = check_time_min_max(dataset_id)

    s3 = boto3.resource('s3')
    S3_BUCKET = os.environ.get('AWS_S3_BUCKET', 'ioos-glider-plots')
    bucket = s3.Bucket(S3_BUCKET)


    df = get_erddap_data(dataset_id)

    for parameter in PARAMETERS:
        title = f"{dataset_id} {parameter.title()} Profiles"
        filename = '{}/{}.png'.format(dataset_id, parameter)
        try:
            graph_obj = s3.Object(S3_BUCKET, filename)
        # catch all here instead of using botocore.exceptions.ClientError
        # if we can't access an object and it later fails to write
        # the graph image we'll want to throw an exception anyhow
        except:
            logging.exception("Failed attempting to fetch object for time min/max determination")
        # TODO: Add further levels of cache invalidation in case dataset is reuploaded,
        #       removed, etc.
        if (graph_obj.metadata.get("min_time") != time_min or
            graph_obj.metadata.get("max_time") != time_max):
            try:
                plot_from_pd(title, df, parameter, graph_obj, time_min, time_max)
            except:
                logging.exception("Failed to generate plot for {}, dataset = {}".format(parameter, dataset_id))
                traceback.print_exc()
        else:
            logging.info(f"Datetime extents of previous graph for {filename} unchanged, skipping.")

def check_time_min_max(dataset_name: str) -> Tuple[str, str]:
    '''
    :param str erddap_dataset: ERDDAP endpoint
    :return str: Minimum temporal extent ISO 8601 date string or empty string if not detected
    :return str: Maximum temporal extent ISO 8601 date string or empty string if not detected
    '''
    try:
        time_min, time_max = pd.read_csv(f"https://gliders.ioos.us/erddap/tabledap/{dataset_name}.csv?time&orderByMinMax(%22time%22)", skiprows=[1]).squeeze()
        return time_min, time_max
    except urllib.error.HTTPError:
        logging.exception(f"HTTP exception attempting to detect min/max of dataset {dataset_name}, skipping.")
        return "", ""
    except:
        logging.exception(f"Other error occurred attempting to detect min/max of dataset {dataset_name}, skipping.")
        return "", ""

def get_erddap_data(dataset_id):
    '''
    :param dataset_id: the deployment name example:'ce_311-20200708T1723'
    :return: pandas DataFrame with deployment variable values
    '''
    e = ERDDAP(
        server='https://gliders.ioos.us/erddap',
        protocol='tabledap',
    )
    e.response = 'csv'
    e.dataset_id = dataset_id
    e.variables = [
        'depth',
        'latitude',
        'longitude',
        'salinity',
        'temperature',
        'conductivity',
        'density',
        'time',
    ]
    df = e.to_pandas()
    return df


def get_variables(dataset, parameter):
    '''
    :param dataset: pandas DataFrame with deployment data
    :param parameter: name of parameter to plot
    :return x: list of datetime object, time
            y, z: numpy.ndarray depth, values
            x_name y_name z_name: string parameter name
    '''
    if 'Error' in dataset.keys()[0]:
        print(dataset[dataset.keys()[0]][1])
        exit()

    # get the names of the columns from the dataset
    y_name = [name for name in dataset.keys() if 'depth' in name]
    x_name = [name for name in dataset.keys() if 'time' in name]
    z_name = [name for name in dataset.keys() if parameter in name]

    # get the data arrays
    y = dataset[y_name[0]].values
    z = dataset[z_name[0]].values
    x = dataset[x_name[0]].values

    # create list of datetime object from the numpy.ndarray of
    # date/time string values in the format '%Y-%m-%dT%H:%M:%SZ'
    # get the indices of non-nan timestamps
    xv = list()
    ii = list()
    for i, d in enumerate(x):
        try:
            xv.append(datetime.strptime(d, '%Y-%m-%dT%H:%M:%SZ'))
            ii.append(i)
        except TypeError:
            error = 'strptime() argument 1 must be str, not float'
    #         print(error)

    # select only non-nan values
    yv = [y[n] for n in ii]
    xv = [x[n] for n in ii]
    zv = [z[n] for n in ii]

    # convert arrays to datatime or float to mask invalid values in the next step
    xv = np.array(xv, dtype='datetime64')
    yv = np.array(yv, dtype='float')
    zv = np.array(zv, dtype='float')

    # mask invalid values
    xv = ma.masked_invalid(xv)
    yv = ma.masked_invalid(yv)
    zv = ma.masked_invalid(zv)

    return xv, yv, zv, x_name[0], y_name[0], z_name[0]


def get_plot(x, y, z, cmap='cmap', title='Glider Profiles', ylabel='Pressure (dbar)', zlabel='Temperature'):
    '''
    Renders a matplotlib profile plot
    :param x: list datetime object
    :param y: numpy.ndarray  depths
    :param z: numpy.ndarray  values
    :param cmap: The colormap to use on the plot
    :param str title: Title of the plot
    :param str ylabel: The label to display along the Y-Axis
    :param str zlabel: The label to display along the color bar legend
    :return fig: figure handle
    '''

    # print(title)
    fig, ax = plt.subplots()
    ax.set_title(title)

    # check z for all nan values
    if len(z[np.logical_not(np.isnan(z))]) == 0:
        ax.set_ylim(0, 10)
        # annotate the plot to report data issue
        ax.annotate(
            zlabel.split('/')[0] + ' are all nan',
            xy=(x[150], 5),
            xytext=(x[100], 6),
        )
    else:
        zz = z[np.logical_not(np.isnan(z))]
        std = np.nanstd(zz)
        mean = np.nanmean(zz)
        vmin = mean - 2 * std
        vmax = mean + 2 * std
        if vmin < 0:
            vmin = 0

        im = ax.scatter(x, y, c=z, cmap=cmap, vmin=vmin, vmax=vmax)
        colorbar = fig.colorbar(im, ax=ax)
        colorbar.set_label(zlabel)

    ax.set_xlim(min(x), max(x))
    ax.invert_yaxis()
    date_format = mdates.DateFormatter('%Y-%m-%d')
    ax.xaxis.set_major_formatter(date_format)
    ax.set_ylabel(ylabel)
    fig.autofmt_xdate()

    return fig


def plot_from_pd(title, dataset, parameter, plot_obj,
                 plot_min_time_str, plot_max_time_str):
    '''
    Plot the parameter from an ERDDAP .csv file put into a pandas DataFrame.
    :param str title: Title of the plot
    :param pandas.DataFrame dataset: A DataFrame containing values to plot
    :param str parameter: Parameter name to plot
    :param boto3.S3.Object: The S3 object used for storing the plot
    :param str min_time_str: The minimum time string represented as an ISO8601 datetime
    :param str max_time_str: The maximum time string represented as an ISO8601 datetime
    '''
    x, y, z, xlabel, ylabel, zlabel = get_variables(dataset, parameter)

    c = [PARAMETERS[key]['cmap'] for key in PARAMETERS.keys()
         if key == parameter]

    fig = get_plot(x, y, z, c[0], title, ylabel, zlabel)

    fig.set_size_inches(20, 5)

    with io.BytesIO() as img_data:
        plt.savefig(img_data, format='png')
        img_data.seek(0)
        plot_obj.put(Body=img_data, ContentType='image/png',
                    Metadata={"min_time": plot_min_time_str,
                              "max_time": plot_max_time_str})

        plt.close(fig)
