import pandas as pd
import numpy as np
from smarthelio_shared.add_multi_index_level import add_index_curve_level


def get_multiindex_expected_current_stc(array_info, met_df):
    """
    Calculate the expected current values under Standard Test Conditions (STC)
    using provided array information and meteorological data.

    Parameters
    ----------
    array_info : pd.Series
        A pandas Series containing array information including 'i_mpp', 'alpha',
        'number_of_strings', and other relevant parameters.

    met_df : pd.DataFrame
        A DataFrame containing meteorological data with multi-index columns.
        It should include 'G_IAM_adjusted' and 'Tmod' levels in the column index.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the calculated expected current values under STC
        conditions with a multi-index.

    The function calculates expected current values under STC conditions based on
    the provided array information and meteorological data, considering IAM-adjusted
    irradiance and module temperature.

    The resulting DataFrame has a multi-index with levels: 'I_exp', the original
    index, and the curve level.
    """
    try:
        # Extract array information
        impp = array_info['i_mpp']
        alpha = array_info['alpha']
        number_of_strings = array_info['number_of_strings']

        # Create a DataFrame to store expected current values
        expected_current = pd.DataFrame(columns=array_info.index, index=met_df.index)
        expected_current.iloc[:, :] = 1

        # Extract IAM adjusted irradiance and module temperature
        adjusted_irradiance = met_df.xs('G_IAM_adjusted', axis=1, level='curve')
        module_temperature = met_df.xs('Tmod', axis=1, level='curve')

        # Equation for Temperature correction
        temperature_correction = 1 + alpha * (module_temperature - 25)

        # Calculate estimated I_expected
        expected_current = impp * (adjusted_irradiance / 1000) * number_of_strings
        expected_current = expected_current * temperature_correction

        # Transform into multi-index
        expected_current.columns = add_index_curve_level(expected_current.columns, 'I_exp')
        expected_current = expected_current.swaplevel(0, 1, axis=1).swaplevel(1, 2, axis=1)

        return expected_current

    except KeyError as e:
        raise ValueError(f"Missing key '{e}' in 'array_info'. Please provide all required parameters.") from None
    except Exception as e:
        raise e  # Re-raise any other exceptions for debugging or handling at a higher level


def get_multiindex_expected_voltage_stc(array_info, met_df):
    """
    Calculate the expected voltage values under Standard Test Conditions (STC) based on given array information
    and meteorological data.

    Parameters
    ----------
    array_info : pd.Series
        A pandas Series containing array information including 'beta', 'v_mpp', 'modules_per_string', and other
        relevant parameters.
    met_df : pd.DataFrame
        A pandas DataFrame containing meteorological data.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the calculated expected voltage values under STC conditions with a multi-index.

    The function calculates expected voltage values under STC conditions using the provided array information and
    meteorological data. It considers temperature ('Tmod') and IAM-adjusted irradiance ('G_IAM_adjusted') in the calculation.

    The resulting DataFrame has a multi-index with levels: 'V_exp', the original index, and the curve level.
    """

    try:
        # Irradiance correction coefficients (taken from a reference paper)
        m = 2.4 / 10000
        b = 6.02 / 100

        # Array Info variables
        beta = array_info['beta']
        vmpp = array_info['v_mpp']
        modules_per_string = array_info['modules_per_string']

        # DataFrame to be returned
        expected_voltage = pd.DataFrame(columns=array_info.index, index=met_df.index)
        expected_voltage.iloc[:, :] = 1

        # Extract IAM adjusted irradiance and Module Temperature
        adjusted_irradiance = met_df.xs('G_IAM_adjusted', axis=1, level='curve')
        module_temperature = met_df.xs('Tmod', axis=1, level='curve')

        # Equations for Irradiance Correction and Temperature Correction
        irradiance_correction = 1 + (m * module_temperature + b) * np.log(adjusted_irradiance / 1000)
        temperature_correction = 1 + beta * (module_temperature - 25)

        # Estimate V_expected
        expected_voltage = expected_voltage * vmpp * modules_per_string
        expected_voltage = expected_voltage * temperature_correction * irradiance_correction

        # Replacing +inf and -inf with NaN
        expected_voltage = expected_voltage.replace([-np.inf, np.inf], np.nan)

        # Transform into multi-index
        expected_voltage.columns = add_index_curve_level(expected_voltage.columns, 'V_exp')
        expected_voltage = expected_voltage.swaplevel(0, 1, axis=1).swaplevel(1, 2, axis=1)

        return expected_voltage

    except Exception as e:
        # Handle exceptions gracefully and print an error message
        print(f"An error occurred: {str(e)}")
        return None


def get_multiindex_expected_power_stc(array_info, expected_current, expected_voltage):
    """
    Calculate the expected power at Standard Test Conditions (STC) based on expected current and voltage data.

    Parameters:
    ----------
    array_info : pd.Series
        A pandas Series containing array information including 'expected_degradation' and other relevant parameters.

    expected_current : pd.DataFrame
        A DataFrame containing the expected current values with a multi-index.

    expected_voltage : pd.DataFrame
        A DataFrame containing the expected voltage values with a multi-index.

    Returns:
    -------
    pd.DataFrame
        A DataFrame containing the calculated expected power values at STC with a multi-index.

    The function calculates expected power values by multiplying the expected current and voltage values.
    It also adjusts the expected power for degradation based on the provided degradation percentage.

    The resulting DataFrame includes the expected power values at STC in a multi-index format.
    """

    # Extract the expected degradation percentage
    expected_degradation = array_info['expected_degradation']

    # Create a DataFrame to store the expected power values
    expected_power = pd.DataFrame(columns=array_info.index, index=expected_current.index)
    expected_power.iloc[:, :] = 1

    # Extract the expected current and voltage data
    expected_current_data = expected_current.xs('I_exp', axis=1, level='curve')
    expected_voltage_data = expected_voltage.xs('V_exp', axis=1, level='curve')

    # Calculate expected power by multiplying expected current and voltage
    expected_power = expected_current_data * expected_voltage_data

    # Adjust expected power for degradation
    expected_power = expected_power * (1 - expected_degradation / 100)

    # Transform the DataFrame into a multi-index format
    expected_power.columns = add_index_curve_level(expected_power.columns, 'P_exp')
    expected_power = expected_power.swaplevel(0, 1, axis=1).swaplevel(1, 2, axis=1)

    return expected_power
