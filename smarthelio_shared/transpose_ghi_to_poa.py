import numpy as np
from pvlib import location, irradiance

import warnings

warnings.filterwarnings('ignore')

def get_clearsky_irradiance(
    latitude, longitude, tz, times, surface_tilt, surface_azimuth, altitude
):
    """
    To calculate Plane-of-Array Clearsky Irradiance for a specific
    geolocation, timezone, and orientation.
    Parameters
    ----------
    latitude : float
        Geolocation latitude value of a solar plant.
    longitude : float
        Geolocation latitude value of a solar plant..
    tz : string
        timezone information.
    times : list
        pandas.Datetime index with Localized timezone.
    surface_tilt : string
        Tilt value.
    surface_azimuth : string
        Azimuth value.
    altitude : float
        Altitude value.
    Returns
    -------
    clearsky_POA : pandas.DataFrame
    clearsky : pandas.DataFrame
    solar_position : pandas.DataFrame
    """

    site = location.Location(latitude, longitude, tz=tz, altitude=altitude)
    clearsky = site.get_clearsky(times)
    # Get solar azimuth and zenith to pass to the transposition function
    solar_position = site.get_solarposition(times=times)
    # Use the get_total_irradiance function to transpose the GHI to POA
    clearsky_POA = irradiance.get_total_irradiance(
        surface_tilt=surface_tilt,
        surface_azimuth=surface_azimuth,
        dni=clearsky["dni"],
        ghi=clearsky["ghi"],
        dhi=clearsky["dhi"],
        solar_zenith=solar_position["apparent_zenith"],
        solar_azimuth=solar_position["azimuth"],
    )
    return clearsky_POA, clearsky, solar_position


def transposition_model(
    df, latitude, longitude, surface_tilt, surface_azimuth, altitude
):
    """
    Transposes GHI (Global Horizontal Irradiance) to POA (Plane of Array Irradiance).

    Args:
        df (DataFrame): DataFrame with time aware UTC index and GHI values.
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
        surface_tilt (float): Tilt angle of the solar panel surface.
        surface_azimuth (float): Azimuth angle of the solar panel surface.
        altitude (float): Altitude of the location.

    Returns:
        DataFrame: DataFrame with transposed POA values.
    """
    tz = "UTC" # tz = 'UTC' because data comes as UTC time
    tilt_radian = np.deg2rad(surface_tilt)
    azimuth_radian = np.deg2rad(surface_azimuth)
    column_name = "GHI"
    if column_name not in df.columns:
        raise ValueError(f"'{column_name}' must be in the DataFrame.")
    times = df.index
    clearsky_POA, clearsky, solar_position = get_clearsky_irradiance(
        latitude, longitude, tz, times, surface_tilt, surface_azimuth, altitude
    )
    df["GHI_norm"] = df["GHI"] / df["GHI"].max()
    df["csky_GHI"] = clearsky["ghi"].copy()
    df["csky_GHI_norm"] = df["csky_GHI"] / df["csky_GHI"].max()
    df["csky_POA"] = clearsky_POA["poa_global"].copy()
    df["csky_POA_norm"] = df["csky_POA"] / df["csky_POA"].max()
    df["POA_inter"] = (df["csky_POA_norm"] / df["csky_GHI_norm"]) * df["GHI_norm"]
    df["POA_inter_norm"] = df["POA_inter"] / df["POA_inter"].max()
    Sun_Zenith_radian = np.deg2rad(
        solar_position["apparent_zenith"].loc[df["csky_POA"].idxmax()]
    )
    Sun_Azimuth_radian = np.deg2rad(
        solar_position["azimuth"].loc[df["csky_POA"].idxmax()]
    )
    x_zenith = np.sin(Sun_Zenith_radian) * np.cos(Sun_Azimuth_radian - np.pi / 2)
    y_zenith = np.sin(Sun_Zenith_radian) * np.sin(Sun_Azimuth_radian - np.pi / 2)
    z_zenith = np.cos(Sun_Zenith_radian)
    x_normal = np.sin(tilt_radian) * np.cos(azimuth_radian - np.pi / 2)
    y_normal = np.sin(tilt_radian) * np.sin(azimuth_radian - np.pi / 2)
    z_normal = np.cos(tilt_radian)
    dot_product = x_zenith * x_normal + y_zenith * y_normal + z_zenith * z_normal
    zenith_at_GHI_max = np.deg2rad(
        solar_position["apparent_zenith"].loc[df["GHI"].idxmax()]
    )
    df["Gpoa"] = (
        df["POA_inter_norm"] * dot_product * df["GHI"].max() / np.cos(zenith_at_GHI_max)
    )
    return df

