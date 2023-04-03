import warnings

warnings.filterwarnings('ignore')

# Pvlib methods
from pvlib.location import Location
from pvlib.irradiance import erbs
from pvlib.irradiance import get_total_irradiance

def transposition_model(df, lat, lon, tz, tilt, azimuth):
    """Transposes GHI to POA;
    df: dataframe with UTC index and GHI values"""
    site = Location(lat, lon, tz=tz)
    times = df.index
    # Generate clearsky data using the Ineichen model, which is the default
    # The get_clearsky method returns a dataframe with values for GHI, DNI,
    # and DHI
    clearsky = site.get_clearsky(times)
    df['clear_sky'] = clearsky['ghi']
    # Get solar azimuth and zenith to pass to the transposition function
    solar_position = site.get_solarposition(times=times)
    # Decompose GHI into DNI and DHI
    erbs_res = erbs(df.GHI, solar_position['zenith'], times)
    df_transpose = df.copy()
    # Translate irradiance to POA
    poa = get_total_irradiance(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        solar_zenith=solar_position['apparent_zenith'],
        solar_azimuth=solar_position['azimuth'],
        dni=erbs_res['dni'],
        ghi=df.GHI,
        dhi=erbs_res['dhi'],
        model='isotropic')
    df['Gpoa'] = poa.poa_global
    return df
