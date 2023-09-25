import pandas as pd
from smarthelio_shared.add_multi_index_level import add_index_curve_level


def get_multiindex_expected_current_noct(array_info, met_df):
    """
    Calculate the expected current values based on NOCT conditions and adjusted irradiance.

    Parameters:
    ----------
    array_info : pd.Series
        A pandas Series containing array information including 'impp_noct', 'number_of_strings',
        and other relevant parameters.

    met_df : pd.DataFrame
        A DataFrame containing meteorological data, including adjusted irradiance.

    Returns:
    -------
    pd.DataFrame
        A DataFrame containing the calculated expected current values with a multi-index.

    The function calculates expected current values based on the provided array information and
    adjusted irradiance under NOCT (Nominal Operating Cell Temperature) conditions.

    The resulting DataFrame includes the expected current values in a multi-index format.
    """
    try:
        # Extract necessary parameters from array_info
        impp_noct = array_info['impp_noct']
        number_of_strings = array_info['number_of_strings']

        # Create a DataFrame to store the expected current values
        expected_current = pd.DataFrame(columns=array_info.index, index=met_df.index)
        expected_current.iloc[:, :] = 1

        # Extract IAM adjusted irradiance data
        adjusted_irradiance = met_df.xs('G_IAM_adjusted', axis=1, level='curve')

        # Calculate expected current using NOCT conditions
        expected_current = impp_noct * (adjusted_irradiance / 800) * number_of_strings

        # Transform the DataFrame into a multi-index format
        expected_current.columns = add_index_curve_level(expected_current.columns, 'I_exp')
        expected_current = expected_current.swaplevel(0, 1, axis=1).swaplevel(1, 2, axis=1)

        return expected_current

    except KeyError as e:
        # Handle the case where a required parameter is missing in array_info
        raise ValueError(f"KeyError: '{e}' is missing in 'array_info'. Please provide all required parameters.") from e
    except Exception as e:
        # Handle other exceptions
        raise Exception("An error occurred while calculating expected current.") from e


def get_multiindex_expected_power_noct(array_info, met_df):
    """
    Calculate the expected power values based on NOCT conditions and adjusted irradiance.

    Parameters:
    ----------
    array_info : pd.Series
        A pandas Series containing array information including 'wattage_noct', 'modules_per_string',
        'number_of_strings', 'expected_degradation', and other relevant parameters.

    met_df : pd.DataFrame
        A DataFrame containing meteorological data, including adjusted irradiance.

    Returns:
    -------
    pd.DataFrame
        A DataFrame containing the calculated expected power values with a multi-index.

    The function calculates expected power values based on the provided array information, adjusted irradiance,
    and NOCT (Nominal Operating Cell Temperature) conditions. It also adjusts the expected power for degradation.

    The resulting DataFrame includes the expected power values in a multi-index format.
    """
    try:
        # Extract necessary parameters from array_info
        power_noct = array_info['wattage_noct']
        modules_per_string = array_info['modules_per_string']
        number_of_strings = array_info['number_of_strings']
        expected_degradation = array_info['expected_degradation']

        # Calculate installed capacity
        installed_capacity = power_noct * modules_per_string * number_of_strings

        # Create a DataFrame to store the expected power values
        expected_power = pd.DataFrame(columns=array_info.index, index=met_df.index)
        expected_power.iloc[:, :] = 1

        # Extract IAM adjusted irradiance data
        adjusted_irradiance = met_df.xs('G_IAM_adjusted', axis=1, level='curve')

        # Calculate expected power using NOCT conditions
        expected_power = installed_capacity * (adjusted_irradiance / 800)

        # Adjust expected power for degradation
        expected_power = expected_power * (1 - expected_degradation / 100)

        # Transform the DataFrame into a multi-index format
        expected_power.columns = add_index_curve_level(expected_power.columns, 'P_exp')
        expected_power = expected_power.swaplevel(0, 1, axis=1).swaplevel(1, 2, axis=1)

        return expected_power

    except KeyError as e:
        # Handle the case where a required parameter is missing in array_info
        raise ValueError(f"KeyError: '{e}' is missing in 'array_info'. Please provide all required parameters.") from e
    except Exception as e:
        # Handle other exceptions
        raise Exception("An error occurred while calculating expected power.") from e


def get_multiindex_expected_voltage_noct(array_info, expected_current, expected_power):
    """
    Calculate the expected voltage values based on expected current and power data.

    Parameters:
    ----------
    array_info : pd.Series
        A pandas Series containing array information including 'expected_degradation' and other relevant parameters.

    expected_current : pd.DataFrame
        A DataFrame containing the expected current values with a multi-index.

    expected_power : pd.DataFrame
        A DataFrame containing the expected power values with a multi-index.

    Returns:
    -------
    pd.DataFrame
        A DataFrame containing the calculated expected voltage values with a multi-index.

    The function calculates expected voltage values based on the provided expected current and power data.

    The resulting DataFrame includes the expected voltage values in a multi-index format.
    """
    try:
        # Create a DataFrame to store the expected voltage values
        expected_voltage = pd.DataFrame(columns=array_info.index, index=expected_current.index)
        expected_voltage.iloc[:, :] = 1

        # Calculate expected voltage based on expected current and power
        expected_power_data = expected_power.xs('P_exp', axis=1, level='curve')
        expected_current_data = expected_current.xs('I_exp', axis=1, level='curve')
        expected_voltage = expected_power_data / expected_current_data

        # Transform the DataFrame into a multi-index format
        expected_voltage.columns = add_index_curve_level(expected_voltage.columns, 'V_exp')
        expected_voltage = expected_voltage.swaplevel(0, 1, axis=1).swaplevel(1, 2, axis=1)

        return expected_voltage

    except Exception as e:
        # Handle exceptions
        raise Exception("An error occurred while calculating expected voltage.") from e
