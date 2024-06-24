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
import pandas as pd
import requests

__version__ = '0.3.0'

PARAMETERS = {

    'salinity': {
        'cmap': cmocean.cm.haline,
        'display': u'Salinity',
        'standard_name': 'sea_water_practical_salinity',
        'standard_name_': 'sea_water_salinity'
    },
    'temperature': {
        'cmap': cmocean.cm.thermal,
        'display': u'Temperature (°C)',
        'standard_name': 'sea_water_temperature'
    },
    'conductivity': {
        'cmap': cmocean.cm.haline,
        'display': u'Conductivity (S m-1)',
        'standard_name': 'sea_water_electrical_conductivity'
    },
    'density': {
        'cmap': cmocean.cm.dense,
        'display': u'Density (kg m-3)',
        'standard_name': 'sea_water_density'
    },

    'oxygen':{
        'cmap': cmocean.cm.oxy,
        'display': u'Oxygen (umol kg-1)',
        'standard_name': 'moles_of_oxygen_per_unit_mass_in_sea_water'
    },

    'chlorophyll':{
        'cmap': cmocean.cm.algae,
        'display': u'Chlorophyll (ug l-1)',
        'standard_name': 'mass_concentration_of_chlorophyll_a_in_sea_water',
        'standard_name_': 'mass_concentration_of_chlorophyll_in_sea_water'
    },

    'colored_dissolved_organic_matter': {
        'cmap': cmocean.cm.matter,
        'display': u'Colored Dissolved Organic Matter (ppb)',
        'standard_name': 'concentration_of_colored_dissolved_organic_matter_in_sea_water_expressed_as_equivalent_mass_fraction_of_quinine_sulfate_dihydrate',
        'standard_name_': 'volume_absorption_coefficient_of_radiative_flux_in_sea_water_due_to_dissolved_organic_matter'
    },

    'optical_backscatter': {
        'cmap': cmocean.cm.turbid,
        'display': u'Optical Backscatter (m-1)',
        'standard_name': 'volume_scattering_coefficient_of_radiative_flux_in_sea_water',
        'standard_name_': 'volume_backwards_scattering_coefficient_of_radiative_flux_in_sea_water'
    },

    'photosynthetically_active_radiation': {
        'cmap': cmocean.cm.solar,
        'display': u'Photosynthetically Active Radiation (umol m-2 s-1)',
        'standard_name': 'downwelling_photosynthetic_photon_spherical_irradiance_in_sea_water',
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
    try:
        info_url = e.get_info_url(dataset_id=dataset_id, response='csv')
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    info = pd.read_csv(info_url)

    n_info = info.loc[info['Attribute Name'] == '_CoordinateAxisType']
    coords_var = list(n_info['Variable Name'].values)

    v_info = info.loc[info['Attribute Name'] == 'standard_name']

    # prepare list of CTD variables for plotting
    ctd_vars = []
    # prepare list of science variables for plotting
    sci_vars = []
    # update PARAMETERS dictionary:
    # (1) replace the parameter name by the one used in the data file.
    old_par = []
    new_par = []
    # (2) delete parameters that are not found in the data files
    del_par = []

    for ii, parameter in enumerate(PARAMETERS):
        # use standard_name to create a list of science parameters to plot
        if ii not in range(4):
            sn_var = PARAMETERS[parameter]['standard_name']
            vv_info = v_info.loc[v_info['Value'] == sn_var]
            if len(vv_info) != 0:
                try:
                    sci_vars.append(vv_info['Variable Name'].values[0])
                except IndexError:
                    logging.exception("standard_name changed for variable {}".format(parameter))
                    traceback.print_exc()
                    sn_var = PARAMETERS[parameter]['standard_name_']
                    vv_info = v_info.loc[v_info['Value'] == sn_var]
                    sci_vars.append(vv_info['Variable Name'].values[0])

                if vv_info['Variable Name'].values[0] != parameter:
                    old_par.append(parameter)
                    new_par.append(vv_info['Variable Name'].values[0])
            else:
                del_par.append(parameter)
        # use parameter name defined in PARAMETERS to create a list of CTD variables to plot
        else:
            ctd_vars.append(parameter)

    # add data coordinates and CTD parameters to the list of science variables for plotting.
    list_var = coords_var + sci_vars + ctd_vars

    # (1) replace the parameter name by the one used in the data file.
    if len(new_par) != 0:
        for kk in range(len(new_par)):
            PARAMETERS[new_par[kk]] = PARAMETERS.pop(old_par[kk])

    # (2) delete parameters that are not found in the data files
    if len(del_par) != 0:
        for key in del_par:
            PARAMETERS.pop(key, None)

    e.response = 'csv'
    e.dataset_id = dataset_id
    e.variables = list_var

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
        error = dataset[dataset.keys()[0]][1]
        print("Dataset {} with error {}".format(dataset, error))

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
            logging.exception("Date {} with error {}".format(dataset, error))
            traceback.print_exc()

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
