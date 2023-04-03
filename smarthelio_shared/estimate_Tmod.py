import math


def estimate_tmod(df_in, Tamb_col='Tamb_csky', G_col='G'):
    """
    The function estimates Module Temperature using Tamb and G.

    Parameters
    ----------
    df_in: dataframe
        Dataframe with columns G and Tamb
    Tamb_col: string
        Column name for Tamb
    G_col: string
        Column name for G
    Returns
    -------
    df: dataframe
        Dataframe with Tmod values
    """
    df = df_in.copy()

    irradiance = df[G_col]
    air_temperature = df[Tamb_col]
    a = -3.56
    b = -.0750
    df['Tmod'] = irradiance * (math.exp(a)) + air_temperature

    return df.Tmod
