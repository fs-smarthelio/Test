"""Filtering data"""
import pandas as pd

def multiindex_irradiance_filter(meteo_data, irrad_low=200, irrad_high=1200):
    """
    Filter POA irradiance readings based on measurement bounds.
    Parameters
    ----------
    meteo_data : pandas DataFrame
        DataFrame containing weather information.
    irrad_low : float, default 200
        The lower bound of acceptable values.
    irrad_high : float, default 1200
        The upper bound of acceptable values.
    Returns
    -------
    filter_df: pandas DataFrame
        Filtered DataFrame.
    """
    filter_df = meteo_data[(meteo_data.xs('G', axis=1, level='curve').ge(
        irrad_low)
                             & meteo_data.xs('G', axis=1, level='curve').le(
                                 irrad_high))]

    return filter_df


def multiindex_current_filter(inverter_data, array_info):
    """
    Filter current readings on the multi-index dataframe.
    Parameters
    ----------
    inverter_data : pandas DataFrame
        DataFrame containing operational data.
    array_info : pandas DataFrame
        DataFrame containing system information.
    Returns
    -------
    filter_df: pandas DataFrame
        Filtered dataframe.
    """
    filter_df = inverter_data[(inverter_data.xs('I', axis=1, level='curve').ge(0)
                               & inverter_data.xs('I', axis=1, level='curve').le(
                                  1.2 * array_info.xs('i_sc', axis=1)*array_info.xs('number_of_strings',axis=1)
                                  ))]

    return filter_df


def multiindex_voltage_filter(inverter_data, array_info):
    """
    Filter voltage readings on the multi-index dataframe.
    Parameters
    ----------
    inverter_data : pandas DataFrame
        DataFrame containing operational data.
    array_info : pandas DataFrame
        DataFrame containing system information.
    Returns
    -------
    filter_df: pandas DataFrame
        Filtered dataframe.
    """
    filter_df = inverter_data[(inverter_data.xs('V', axis=1, level='curve').ge(0)
                               & inverter_data.xs('V', axis=1, level='curve').le(
                                   array_info.xs('v_oc', axis=1)*array_info.xs('modules_per_string',axis=1)
                                   ))]

    return filter_df

def multiindex_tamb_filter(meteo_data, tamb_low=-10, tamb_high=55):
    """
    Filter ambient temperature readings based on measurement bounds.
    Parameters
    ----------
    meteo_data : pandas DataFrame
        DataFrame containing weather information.
    tamb_low : float, default -10
        The lower bound of acceptable values.
    irrad_high : float, default 60
        The upper bound of acceptable values.
    Returns
    -------
    filter_df: pandas DataFrame
        Filtered DataFrame.
    """
    filter_df = meteo_data[(meteo_data.xs('Tamb', axis=1, level='curve').ge(
        tamb_low)
                             & meteo_data.xs('Tamb', axis=1, level='curve').le(
                                 tamb_high))]

    return filter_df

def multiindex_tmod_filter(meteo_data, tmod_low=-5, tmod_high=80):
    """
    Filter POA irradiance readings based on measurement bounds.
    Parameters
    ----------
    meteo_data : pandas DataFrame
        DataFrame containing weather information.
    tmod_low : float, default -5
        The lower bound of acceptable values.
    tmod_high : float, default 80
        The upper bound of acceptable values.
    Returns
    -------
    filter_df: pandas DataFrame
        Filtered DataFrame.
    """
    filter_df = meteo_data[(meteo_data.xs('Tmod', axis=1, level='curve').ge(
        tmod_low)
                             & meteo_data.xs('Tmod', axis=1, level='curve').le(
                                 tmod_high))]

    return filter_df