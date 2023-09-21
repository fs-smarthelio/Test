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

    # Array info variables
    impp = array_info['i_mpp']
    impp_noct = array_info['impp_noct']
    alpha = array_info['alpha']
    number_of_strings = array_info['number_of_strings']

    # Create a DataFrame to store the expected current values
    expected_current = pd.DataFrame(columns=array_info.index, index=met_df.index)
    expected_current.iloc[:, :] = 1

    # IAM adjusted irradiance
    adjusted_irradiance = met_df.xs('G_IAM_adjusted', axis=1, level='curve')

    # Calculate the expected current values based on temperature ('Tmod') if available
    if 'Tmod' in met_df.columns.get_level_values(2):
        module_temperature = met_df.xs('Tmod', axis=1, level='curve')
        temp_correction_factor = 1 + alpha * (module_temperature - 25)

        expected_current = impp * (adjusted_irradiance / 1000) * number_of_strings
        expected_current = expected_current * temp_correction_factor
    else:
        # If 'Tmod' not found, use NOCT values for calculation
        expected_current = impp_noct * (adjusted_irradiance / 800) * number_of_strings

    # Transform the DataFrame into a multi-index format
    expected_current.columns = add_index_curve_level(expected_current.columns, 'I_exp')
    expected_current = expected_current.swaplevel(0, 1, axis=1).swaplevel(1, 2, axis=1)

    return expected_current


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

    # Array info variables
    vmpp = array_info['v_mpp']
    beta = array_info['beta']
    vmpp_noct = array_info['vmpp_noct']
    modules_per_string = array_info['modules_per_string']

    # Create a DataFrame to store the expected voltage values
    expected_voltage = pd.DataFrame(columns=array_info.index, index=met_df.index)
    expected_voltage.iloc[:, :] = 1

    # IAM adjusted irradiance
    adjusted_irradiance = met_df.xs('G_IAM_adjusted', axis=1, level='curve')

    # Estimate V_expected based on temperature ('Tmod') if available
    if 'Tmod' in met_df.columns.get_level_values(2):
        module_temperature = met_df.xs('Tmod', level='curve', axis=1)
        irradiance_correction_factor = 1 + (m * module_temperature + b) * np.log(adjusted_irradiance / 1000)

        expected_voltage = expected_voltage * vmpp * modules_per_string
        temperature_correction_factor = 1 + beta * (module_temperature - 25)
        expected_voltage = expected_voltage * temperature_correction_factor * irradiance_correction_factor

    else:
        # If 'Tmod' not found, use NOCT values for calculation
        expected_voltage = expected_voltage * vmpp_noct * array_info['modules_per_string']

    # Replace +inf and -inf with NaN
    expected_voltage = expected_voltage.replace([-np.inf, np.inf], np.nan)

    # Transform the DataFrame into a multi-index format
    expected_voltage.columns = add_index_curve_level(expected_voltage.columns, 'V_exp')
    expected_voltage = expected_voltage.swaplevel(0, 1, axis=1).swaplevel(1, 2, axis=1)

    return expected_voltage


def get_multiindex_expected_power(array_info, expected_current, expected_voltage):
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
    expected_power = pd.DataFrame(columns=array_info.index, index=expected_current.index)
    expected_power.iloc[:, :] = 1

    # Calculate expected power by multiplying expected current and voltage
    expected_power = expected_current.xs('I_exp', axis=1, level='curve') * expected_voltage.xs('V_exp', axis=1, level='curve')

    # Adjust expected power for degradation
    expected_degradation = array_info['expected_degradation']
    expected_power = expected_power * (1 - expected_degradation / 100)

    # Transform the DataFrame into a multi-index format
    expected_power.columns = add_index_curve_level(expected_power.columns, 'P_exp')
    expected_power = expected_power.swaplevel(0, 1, axis=1).swaplevel(1, 2, axis=1)

    return expected_power


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
    expected_current = get_multiindex_expected_current(array_info, meteo_df)

    # Calculate Expected Voltage (ExpV)
    expected_voltage = get_multiindex_expected_voltage(array_info, meteo_df)

    # Calculate Expected Power (ExpP)
    expected_power = get_multiindex_expected_power(array_info, expected_current, expected_voltage)

    # Concatenate expected parameters into the inverter data
    master_inv_df = pd.concat([inverter_df, expected_current, expected_voltage, expected_power],
                              axis=1).sort_index(axis=1)

    return master_inv_df
