import os
import matplotlib
matplotlib.use('AGG')
import matplotlib.dates as mdates
import boto3
import cmocean
import io
import logging
import matplotlib.pyplot as plt
import numpy as np
import traceback
from datetime import datetime
from erddapy import ERDDAP


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
    :param str erddap_dataset: ERDDAP .htm of a deployment
    '''
    dataset_id = erddap_dataset.split('/')[-1].split('.html')[0]
    path = dir_path(dataset_id)
    df = get_erddap_data(dataset_id)

    for parameter in PARAMETERS:
        title = dataset_id + ' ' + parameter[0].upper() + parameter[1:] + ' Profiles'
        filename = '{}/{}.png'.format(path, parameter)
        try:
            plot_from_pd(title, df, parameter, filename)
        except Exception:
            logging.exception("Failed to generate plot for {}".format(parameter))
            traceback.print_exc()
            continue
    return 0


def get_erddap_data(dataset_id):
    '''
    :param dataset_id: the deployment name example:'ce_311-20200708T1723'
    :return: pandas DataFrame with deployment variable values
    '''

    e = ERDDAP(
      server='http://gliders.ioos.us/erddap',
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


def dir_path(dataset_id):
    '''
    :param dataset_id: the deployment name example:'ce_311-20200708T1723'
    :return: str filepath: Location to save the figure to (PNG)
    '''
    cwd = os.getcwd()
    path = os.path.join(cwd,dataset_id)
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def get_variables(dataset, parameter):
    '''
    :param dataset: pandas DataFrame with deployment variable values
    :param parameter: name of parameter to plot
    :return x, y, z: numpy.ndarray time, depth, values
    :return x_name y_name z_name: string parameter name
    '''
    
    y_name = [name for name in dataset.keys() if 'depth' in name]
    x_name = [name for name in dataset.keys() if 'time' in name]
    z_name = [name for name in dataset.keys() if parameter in name]
    
    y = dataset[y_name[0]].values
    z = dataset[z_name[0]].values
    x = dataset[x_name[0]].values

    return x, y, z, x_name[0], y_name[0], z_name[0]


def get_times(x):
    '''
    create a datetime object from a string
    :param x: numpy.ndarray of date/time string values in the format '%Y-%m-%dT%H:%M:%SZ'
    :return: list of datetime object
    '''
    xv = list()
    for d in x:
        xv.append(datetime.strptime(d,'%Y-%m-%dT%H:%M:%SZ'))
    return xv


def get_plot(x, y, z, cmap='cmap', title='Glider Profiles', ylabel='Pressure (dbar)', zlabel='Temperature'):
    '''
    Renders a matplotlib profile plot
    :param x: list timestamps
    :param y: numpy.ndarray  depths
    :param z: numpy.ndarray  values
    :param cmap: The colormap to use on the plot
    :param str title: Title of the plot
    :param str ylabel: The label to display along the Y-Axis
    :param str zlabel: The label to display along the color bar legend
    :return fig: figure handle
    '''

    fig, ax = plt.subplots()
    std = np.nanstd(z)
    mean = np.nanmean(z)
    vmin = mean - 2 * std
    vmax = mean + 2 * std    
    
    if vmin < 0:
        vmin = 0

    im = ax.scatter(x, y, c=z, cmap=cmap, vmin=vmin, vmax=vmax)

    ax.set_title(title)
    ax.invert_yaxis()
    ax.set_xlim([min(x), max(x)])

    date_format = mdates.DateFormatter('%Y-%m-%d')
    ax.xaxis.set_major_formatter(date_format)
    ax.set_ylabel(ylabel)
    colorbar = fig.colorbar(im, ax=ax)
    colorbar.set_label(zlabel)
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

    xv = get_times(x) # if time is of size 1 it wont work
    c = [PARAMETERS[key]['cmap'] for key in PARAMETERS.keys() if key == parameter]
    
    fig = get_plot(xv, y, z, c[0], title, ylabel, zlabel)

    fig.set_size_inches(20, 5)
    fig.savefig(filepath, dpi=100)
    
    plt.close(fig)
    
    img_data = io.BytesIO()
    plt.savefig(img_data, format='png')
    img_data.seek(0)

    s3 = boto3.resource('s3')
    bucket = s3.Bucket('ioos-glider-plots')
    bucket.put_object(Body=img_data, ContentType='image/png', Key=filepath)
