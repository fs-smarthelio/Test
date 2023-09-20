import pandas as pd
import numpy as np


A_R = 0.16
C1 = 0.4244


def martin_ruiz_diffuse(surface_tilt, a_r=A_R, c1=C1, c2=None):
    '''
    Determine the incidence angle modifiers (iam) for diffuse sky and
    ground-reflected irradiance using the Martin and Ruiz incident angle model.

    Parameters
    ----------
    surface_tilt: float or array-like, default 0
        Surface tilt angles in decimal degrees.
        The tilt angle is defined as degrees from horizontal
        (e.g. surface facing up = 0, surface facing horizon = 90)
        surface_tilt must be in the range [0, 180]

    a_r : numeric
        The angular losses coefficient described in equation 3 of [1]_.
        This is an empirical dimensionless parameter. Values of a_r are
        generally on the order of 0.08 to 0.25 for flat-plate PV modules.
        a_r must be greater than zero.

    c1 : float
        First fitting parameter for the expressions that approximate the
        integral of diffuse irradiance coming from different directions.
        c1 is given as the constant 4 / 3 / pi (0.4244) in [1]_.

    c2 : float
        Second fitting parameter for the expressions that approximate the
        integral of diffuse irradiance coming from different directions.
        If c2 is None, it will be calculated according to the linear
        relationship given in [3]_.

    Returns
    -------
    iam_sky : numeric
        The incident angle modifier for sky diffuse

    iam_ground : numeric
        The incident angle modifier for ground-reflected diffuse

    Notes
    -----
    Sky and ground modifiers are complementary: iam_sky for tilt = 30 is
    equal to iam_ground for tilt = 180 - 30.  For vertical surfaces,
    tilt = 90, the two factors are equal.

    References
    ----------
    .. [1] N. Martin and J. M. Ruiz, "Calculation of the PV modules angular
       losses under field conditions by means of an analytical model", Solar
       Energy Materials & Solar Cells, vol. 70, pp. 25-38, 2001.

    .. [2] N. Martin and J. M. Ruiz, "Corrigendum to 'Calculation of the PV
       modules angular losses under field conditions by means of an
       analytical model'", Solar Energy Materials & Solar Cells, vol. 110,
       pp. 154, 2013.

    .. [3] "IEC 61853-3 Photovoltaic (PV) module performance testing and energy
       rating - Part 3: Energy rating of PV modules". IEC, Geneva, 2018.

    See Also
    --------
    pvlib.iam.martin_ruiz
    pvlib.iam.physical
    pvlib.iam.ashrae
    pvlib.iam.interp
    pvlib.iam.sapm
    '''
    # Contributed by Anton Driesse (@adriesse), PV Performance Labs. Oct. 2019

    if isinstance(surface_tilt, pd.Series):
        out_index = surface_tilt.index
    else:
        out_index = None

    surface_tilt = np.asanyarray(surface_tilt)

    # avoid undefined results for horizontal or upside-down surfaces
    zeroang = 1e-06

    surface_tilt = np.where(surface_tilt == 0, zeroang, surface_tilt)
    surface_tilt = np.where(surface_tilt == 180, 180 - zeroang, surface_tilt)

    if c2 is None:
        # This equation is from [3] Sect. 7.2
        c2 = 0.5 * a_r - 0.154

    beta = np.radians(surface_tilt)
    sin = np.sin
    pi = np.pi
    cos = np.cos

    # avoid RuntimeWarnings for <, sin, and cos with nan
    with np.errstate(invalid='ignore'):
        # because sin(pi) isn't exactly zero
        sin_beta = np.where(surface_tilt < 90, sin(beta), sin(pi - beta))

        trig_term_sky = sin_beta + (pi - beta - sin_beta) / (1 + cos(beta))
        trig_term_gnd = sin_beta + (beta - sin_beta) / (1 - cos(beta))  # noqa: E222 E261 E501

    iam_sky = 1 - np.exp(-(c1 + c2 * trig_term_sky) * trig_term_sky / a_r)
    iam_gnd = 1 - np.exp(-(c1 + c2 * trig_term_gnd) * trig_term_gnd / a_r)

    if out_index is not None:
        iam_sky = pd.Series(iam_sky, index=out_index, name='iam_sky')
        iam_gnd = pd.Series(iam_gnd, index=out_index, name='iam_ground')

    return iam_sky, iam_gnd
