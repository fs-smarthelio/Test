import warnings

warnings.filterwarnings('ignore')

# Pvlib methods
from pvlib.location import Location
from pvlib.irradiance import erbs
from pvlib.irradiance import get_total_irradiance, get_extra_radiation

def transposition_model(df, lat, lon, tz, tilt, azimuth):
    """Transposes GHI to POA;
    df: dataframe with UTC index and GHI values"""
    # Column name to check
    column_name = 'GHI'
    # Check if 'GHI' is in the columns of the DataFrame
    if column_name not in df.columns:
        raise ValueError(f"'{column_name}' must be in the DataFrame.")
    # Check if the index is timezone-aware
    if df.index.tz is None:
        # If the index is timezone-naive, convert it to the user-specified timezone and make it timezone-aware
        df.index = df.index.tz_localize(tz)
    else:
        # If the index is timezone-aware, convert it to the user-specified timezone
        df.index = df.index.tz_localize(None).tz_localize(tz)
    # Create a location object named 'site' to contain geographical information
    site = Location(lat, lon, tz=tz)
    # To calculate solar position, we need to pass a datetime index series.
    times = df.index
    # Get solar azimuth and zenith to pass to the transposition function
    solar_position = site.get_solarposition(times=times)
    # Calculate dni extra
    dni_extra = get_extra_radiation(times, solar_constant=1366.1,
                        method='spencer', epoch_year=times.year[0])
    max_zenith = solar_position['zenith'].max()
    # Use 'erbs' model to decompose measured GHI into components.
    erbs_res = erbs(df.GHI, solar_position['zenith'], times, max_zenith=max_zenith)
    # Translate irradiance to POA
    poa = get_total_irradiance(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        solar_zenith=solar_position['apparent_zenith'],
        solar_azimuth=solar_position['azimuth'],
        dni=erbs_res['dni'],
        ghi=df.GHI,
        dhi=erbs_res['dhi'],
        dni_extra=dni_extra,
        model='haydavies')
    df['Gpoa'] = poa.poa_global
    df.index = df.index.tz_localize(None).tz_localize('UTC')
    return df
