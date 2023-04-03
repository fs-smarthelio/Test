from rdtools.clearsky_temperature import get_clearsky_tamb


def get_csky_temp(times, lat, lon):

    """
    The function estimates Tamb for a given lat and long using RD tools.

    Parameters
    ----------
    df_in: dataframe with datetime index
    lat: float
        Latitude
    long: float
        Longitude
    G_col: string
        Column name of G_poa to be used in func estimate_tmod

    Returns
    -------
    df_out: dataframe with Tamb_csky and Tmod_csky columns

    """
    tamb = get_clearsky_tamb(times=times, latitude=lat,
                             longitude=lon, window_size=40,
                             gauss_std=20)

    return tamb