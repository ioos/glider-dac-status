#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import matplotlib
matplotlib.use('AGG')
import matplotlib.dates as mdate
import boto3
import cmocean
import io
import logging
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import netCDF4
import numpy as np
import traceback
from datetime import datetime

from erddapy import ERDDAP


# In[ ]:


dataset_id = 'ce_311-20200708T1723'

#'ce_381-20171208T1841-delayed'
#
#'bios_minnie-20170616T1454'
#'amelia-20180501T0000'
#whoi_406-20160902T1700'

parameter_list = [
                    'depth',
                    'latitude',
                    'longitude',
                    'salinity',
                    'temperature',
                    'conductivity',
                    'density',
                    'time',
                   ]


# In[ ]:


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


# In[ ]:


def get_erddap_data(dataset_id):
    e = ERDDAP(
      server='https://gliders.ioos.us/erddap',
      protocol='tabledap',
    )
    e.response = 'csv'
    e.dataset_id = dataset_id
    # e.constraints = {
    #     'time>=': '2016-07-10T00:00:00Z',
    #     'time<=': '2017-02-10T00:00:00Z',
    #     'latitude>=': 38.0,
    #     'latitude<=': 41.0,
    #     'longitude>=': -72.0,
    #     'longitude<=': -69.0,
    # }
    e.variables = parameter_list
    df = e.to_pandas()
    return df


# In[ ]:


def get_variables(dataset, parameter):
    
    y_name = [name for name in dataset.keys() if 'depth' in name]
    x_name = [name for name in dataset.keys() if 'time' in name]
    z_name = [name for name in dataset.keys() if parameter in name]
    
    y = dataset[y_name[0]].values
    z = dataset[z_name[0]].values
    x = dataset[x_name[0]].values
    return x, y, z, x_name[0], y_name[0], z_name[0]


# In[ ]:


def get_times(x):
    '''
    Converts an array of timestamps to the matplotlib epoch 
    :param numpy.ndarray x: An array of time values
    '''    
    xv = list()
    for d in x:
        xv.append(datetime.strptime(d,'%Y-%m-%dT%H:%M:%SZ'))
    return xv


# In[ ]:


def get_plot(x, y, z, cmap='cmap', title='Glider Profiles', ylabel='Pressure (dbar)', zlabel='Temperature'):
    '''
    Renders a matplotlib profile plot
    :param numpy.ndarray x: A grid of timestamps 
    :param numpy.ndarray y: A grid of depths     
    :param numpy.ndarray z: A grid of values     
    :param cmap: The colormap to use on the plot
    :param str title: Title of the plot
    :param str ylabel: The label to display along the Y-Axis
    :param str zlabel: The label to display along the color bar legend
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
    # day_locator = mdate.DayLocator(bymonthday=None, interval=1, tz=None)
    # ax.xaxis.set_major_locator(day_locator)
    # month_locator = mdate.MonthLocator(interval=1)
    # ax.xaxis.set_major_locator(month_locator)
    date_format = mdate.DateFormatter('%Y-%m-%d')
    ax.xaxis.set_major_formatter(date_format)
    ax.set_ylabel(ylabel)
    colorbar = fig.colorbar(im, ax=ax)
    colorbar.set_label(zlabel)
    fig.autofmt_xdate()





    #ax.fmt_xdata = mdate.DateFormatter('%Y-%m-%d')

    return fig


# In[ ]:


def plot_from_pd(title, dataset, parameter, filepath):
    '''
    Plot the parameter from csv ERDDAP file. 
    :param str title: Title of the plot
    :param array Dataset: A pandas array values 
    :param str parameter: Parameter to plot
    :param str filepath: Location to save the figure to (PNG)
    '''
    x, y, z, xlabel, ylabel, zlabel = get_variables(dataset, parameter)

    # Remove empty timesteps
    if hasattr(x, 'mask'):
        y = y[~x.mask]
        z = z[~x.mask]
        x = x[~x.mask]

    total_mask = y.mask | z.mask | np.isnan(y) | np.isnan(z)
    

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


# In[ ]:


def dir_path(dataset_id):
    cwd = os.getcwd()
    path = os.path.join(cwd,dataset_id)
    if not os.path.exists(path):
        os.mkdir(path)
    return path


# In[ ]:


def generate_profile_plot(erddap_dataset):
    '''
    Plot the parameters for a deployment
    :param str erddap_dataset: ERDDAP Dataset_id
    '''
    path = dir_path(erddap_dataset)
    df = get_erddap_data(erddap_dataset)

    for parameter in PARAMETERS:
        title = erddap_dataset + ' ' + parameter[0].upper() + parameter[1:] + ' Profiles'
        filename = '{}/{}.png'.format(path, parameter)
        try:
            plot_from_pd(title, df, parameter, filename)
        except Exception:
            logging.exception("Failed to generate plot for {}".format(parameter))
            traceback.print_exc()
            continue
    return 0


# In[ ]:


generate_profile_plot(dataset_id)

