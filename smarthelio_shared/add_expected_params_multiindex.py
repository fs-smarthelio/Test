import pandas as pd
import numpy as np
from smarthelio_shared import add_index_curve_level


def get_multiindex_expected_current(array_info, met_df):
    """
    Calculate the expected current values based on given array information and meteorological data.

    Parameters:
    - array_info (pd.Series): A pandas Series containing array information including 'i_mpp', 'impp_noct', 'alpha',
                             and 'number_of_strings'.
    - met_df (pd.DataFrame): A pandas DataFrame containing meteorological data.

    Returns:
    - pd.DataFrame: A DataFrame containing the calculated expected current values with a multi-index.

    The function calculates expected current values using the provided array information and meteorological data.
    It considers temperature ('Tmod') in the calculation if available, otherwise, it uses NOCT values.

    The resulting DataFrame has a multi-index with levels: 'I_exp', the original index, and the curve level.
    """

    # Extract variables from array_info
    impp = array_info['i_mpp']
    impp_noct = array_info['impp_noct']
    alpha = array_info['alpha']
    number_of_strings = array_info['number_of_strings']

    # Create a DataFrame to store the expected current values
    temp_ExpI = pd.DataFrame(columns=array_info.index, index=met_df.index)
    temp_ExpI.iloc[:, :] = 1

    # Calculate the expected current values based on temperature ('Tmod') if available
    if 'Tmod' in met_df.columns.get_level_values(2):
        temp_ExpI = impp * (met_df.xs('G_IAM_adjusted', axis=1, level='curve') / 1000) * number_of_strings
        temp_correction_factor = 1 + alpha * (met_df.xs('Tmod', axis=1, level='curve') - 25)
        temp_ExpI = temp_ExpI * temp_correction_factor
    else:
        # If 'Tmod' not found, use NOCT values for calculation
        temp_ExpI = impp_noct * (met_df.xs('G_IAM_adjusted', axis=1, level='curve') / 1000) * number_of_strings
        temp_correction_factor = 1 + alpha * (met_df.xs('Tmod', axis=1, level='curve') - 25)
        temp_ExpI = temp_ExpI * temp_correction_factor

    # Transform the DataFrame into a multi-index format
    temp_ExpI.columns = add_index_curve_level(temp_ExpI.columns, 'I_exp')
    temp_ExpI = temp_ExpI.swaplevel(0, 1, axis=1).swaplevel(1, 2, axis=1)

    return temp_ExpI


def get_multiindex_expected_voltage(array_info, met_df):
    """
    Calculate the expected voltage values based on given array information and meteorological data.

    Parameters:
    - array_info (pd.Series): A pandas Series containing array information including 'v_mpp', 'vmpp_noct', 'beta',
                             'modules_per_string', and other relevant parameters.
    - met_df (pd.DataFrame): A pandas DataFrame containing meteorological data.

    Returns:
    - pd.DataFrame: A DataFrame containing the calculated expected voltage values with a multi-index.

    The function calculates expected voltage values using the provided array information and meteorological data.
    It considers temperature ('Tmod') in the calculation if available, otherwise, it uses NOCT values.

    The resulting DataFrame has a multi-index with levels: 'V_exp', the original index, and the curve level.
    """

    # Values taken from the reference paper
    m = 2.4 / 10000
    b = 6.02 / 100

    # Create a DataFrame to store the expected voltage values
    temp_ExpV = pd.DataFrame(columns=array_info.index, index=met_df.index)
    temp_ExpV.iloc[:, :] = 1

    # Estimate V_expected based on temperature ('Tmod') if available
    if 'Tmod' in met_df.columns.get_level_values(2):
        temp_ExpV = temp_ExpV * array_info['v_mpp'] * array_info['modules_per_string']
        V_irr_corr = 1 + (m * met_df.xs('Tmod', level='curve', axis=1) + b) * np.log(met_df.xs(
            'G_IAM_adjusted', axis=1, level='curve') / 1000)
        V_temp_corr = 1 + array_info['beta'] * (met_df.xs('Tmod', axis=1, level='curve') - 25)
        temp_ExpV = temp_ExpV * V_temp_corr * V_irr_corr
    else:
        # If 'Tmod' not found, use NOCT values for calculation
        temp_ExpV = temp_ExpV * array_info['vmpp_noct'] * array_info['modules_per_string']
        V_irr_corr = 1 + (m * met_df.xs('Tmod', level='curve', axis=1) + b) * np.log(met_df.xs(
            'G_IAM_adjusted', axis=1, level='curve') / 1000)
        V_temp_corr = 1 + array_info['beta'] * (met_df.xs('Tmod', axis=1, level='curve') - 20)
        temp_ExpV = temp_ExpV * V_temp_corr * V_irr_corr

    # Replace +inf and -inf with NaN
    temp_ExpV = temp_ExpV.replace([-np.inf, np.inf], np.nan)

    # Transform the DataFrame into a multi-index format
    temp_ExpV.columns = add_index_curve_level(temp_ExpV.columns, 'V_exp')
    temp_ExpV = temp_ExpV.swaplevel(0, 1, axis=1).swaplevel(1, 2, axis=1)

    return temp_ExpV


def get_multiindex_expected_power(array_info, temp_ExpI, temp_ExpV):
    """
    Calculate the expected power values based on expected current and voltage data and array information.

    Parameters:
    - array_info (pd.Series): A pandas Series containing array information including 'expected_degradation' and other
                             relevant parameters.
    - temp_ExpI (pd.DataFrame): A DataFrame containing the expected current values with a multi-index.
    - temp_ExpV (pd.DataFrame): A DataFrame containing the expected voltage values with a multi-index.

    Returns:
    - pd.DataFrame: A DataFrame containing the calculated expected power values with a multi-index.

    The function calculates expected power values by multiplying the expected current and voltage values.
    It also adjusts the expected power for degradation based on the provided degradation percentage.

    The resulting DataFrame has a multi-index with levels: 'P_exp', the original index, and the curve level.
    """

    # Create a DataFrame to store the expected power values
    temp_ExpP = pd.DataFrame(columns=array_info.index, index=temp_ExpI.index)
    temp_ExpP.iloc[:, :] = 1

    # Calculate expected power by multiplying expected current and voltage
    temp_ExpP = temp_ExpI.xs('I_exp', axis=1, level='curve') * temp_ExpV.xs('V_exp', axis=1, level='curve')

    # Adjust expected power for degradation
    temp_ExpP = temp_ExpP * (1 - array_info['expected_degradation'] / 100)

    # Transform the DataFrame into a multi-index format
    temp_ExpP.columns = add_index_curve_level(temp_ExpP.columns, 'P_exp')
    temp_ExpP = temp_ExpP.swaplevel(0, 1, axis=1).swaplevel(1, 2, axis=1)

    return temp_ExpP


def get_expected_inverter_params(array_info, inverter_df, meteo_df):
    """
    Calculate and append expected current, voltage, and power parameters to the inverter DataFrame.

    Parameters:
    - array_info (pd.Series): A pandas Series containing array information.
    - inverter_df (pd.DataFrame): A DataFrame containing inverter parameters.
    - meteo_df (pd.DataFrame): A DataFrame containing meteorological data.

    Returns:
    - pd.DataFrame: A DataFrame containing inverter parameters with added expected current, voltage, and power columns.

    The function calculates the expected current, voltage, and power values based on the provided array information and
    meteorological data. It then appends these expected parameters to the inverter DataFrame.

    The resulting DataFrame includes both the original inverter parameters and the newly added expected parameters.
    """

    # Calculate Expected Current (ExpI)
    ExpI_df = get_multiindex_expected_current(array_info, meteo_df)

    # Calculate Expected Voltage (ExpV)
    ExpV_df = get_multiindex_expected_voltage(array_info, meteo_df)

    # Calculate Expected Power (ExpP)
    ExpP_df = get_multiindex_expected_power(array_info, ExpI_df, ExpV_df)

    # Concatenate expected parameters into the inverter data
    master_inv_df = pd.concat([inverter_df, ExpI_df, ExpV_df, ExpP_df], axis=1).sort_index(axis=1)

    return master_inv_df
