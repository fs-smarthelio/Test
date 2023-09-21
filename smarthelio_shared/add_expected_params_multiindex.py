import pandas as pd

from smarthelio_shared import get_multiindex_expected_current_stc
from smarthelio_shared import get_multiindex_expected_voltage_stc
from smarthelio_shared import get_multiindex_expected_power_stc

from smarthelio_shared import get_multiindex_expected_current_noct
from smarthelio_shared import get_multiindex_expected_power_noct
from smarthelio_shared import get_multiindex_expected_voltage_noct


def get_expected_inverter_params(array_info, inverter_df, meteo_df):
    """
    Calculate and concatenate expected inverter parameters based on provided array information,
    inverter data, and meteorological data.

    Parameters:
    ----------
    array_info : pd.Series
        A pandas Series containing array information including 'Tmod', 'expected_degradation',
        and other relevant parameters.

    inverter_df : pd.DataFrame
        A DataFrame containing inverter data.

    meteo_df : pd.DataFrame
        A DataFrame containing meteorological data.

    Returns:
    -------
    pd.DataFrame
        A DataFrame containing the concatenated expected inverter parameters.

    The function calculates expected current, voltage, and power values based on provided meteorological data and
    array information. It then concatenates these expected parameters with the original inverter data.

    The resulting DataFrame includes the expected inverter parameters.
    """
    try:
        if 'Tmod' in meteo_df.columns.get_level_values(2):
            # Calculate expected current, voltage, and power at STC
            expected_current = get_multiindex_expected_current_stc(array_info, meteo_df)
            expected_voltage = get_multiindex_expected_voltage_stc(array_info, meteo_df)
            expected_power = get_multiindex_expected_power_stc(array_info, expected_current, expected_voltage)
        else:
            # Calculate expected current, power, and voltage at NOCT
            expected_current = get_multiindex_expected_current_noct(array_info, meteo_df)
            expected_power = get_multiindex_expected_power_noct(array_info, meteo_df)
            expected_voltage = get_multiindex_expected_voltage_noct(array_info, expected_current, expected_power)

        # Concatenate expected parameters into the inverter data
        master_inv_df = pd.concat([inverter_df, expected_current, expected_voltage, expected_power],
                                  axis=1).sort_index(axis=1)

        return master_inv_df

    except Exception as e:
        # Handle other exceptions
        raise Exception("An error occurred while calculating expected inverter parameters.") from e
