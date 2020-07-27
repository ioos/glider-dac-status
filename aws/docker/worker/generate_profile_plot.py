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
    df = get_erddap_data(dataset_id)

    for parameter in PARAMETERS:
        title = dataset_id + ' ' + parameter[0].upper() + parameter[1:] + ' Profiles'
        filename = '{}/{}.png'.format(dataset_id, parameter)
        try:
            plot_from_pd(title, df, parameter, filename)
        except Exception:
            logging.exception("Failed to generate plot for {}, dataset = {}".format(parameter, dataset_id))
            traceback.print_exc()
            continue
    return 0


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
        bbox_props = dict(boxstyle="round", fc="w", ec="0.5", alpha=0.9)
        ax.text(x[round(len(x) / 2)], 5, zlabel.split('/')[0] + ' data is missing',
                ha="center", va="center", size=20,
                bbox=bbox_props)
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


def plot_from_pd(title, dataset, parameter, filepath):
    '''
    Plot the parameter from an ERDDAP .csv file put into a pandas DataFrame.
    :param str title: Title of the plot
    :param array Dataset: A pandas array values
    :param str parameter: Parameter to plot
    :param str filepath: Location to save the figure to (PNG)
    '''
    x, y, z, xlabel, ylabel, zlabel = get_variables(dataset, parameter)

    c = [PARAMETERS[key]['cmap'] for key in PARAMETERS.keys() if key == parameter]

    fig = get_plot(x, y, z, c[0], title, ylabel, zlabel)

    fig.set_size_inches(20, 5)

    img_data = io.BytesIO()
    plt.savefig(img_data, format='png')
    img_data.seek(0)

    s3 = boto3.resource('s3')
    S3_BUCKET = os.environ['AWS_S3_BUCKET'] or 'ioos-glider-plots'
    bucket = s3.Bucket(S3_BUCKET)
    bucket.put_object(Body=img_data, ContentType='image/png', Key=filepath)

    plt.close(fig)
