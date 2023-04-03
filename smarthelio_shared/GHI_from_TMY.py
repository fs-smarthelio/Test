import pandas as pd
import datetime
from datetime import datetime, time, date
import warnings
warnings.filterwarnings("ignore")

def GHIfromTMY(times, latitude, longitude, tz):

    """
    Fetches TMY GHI data using lat and long in UTC and convert it
    into local time https://re.jrc.ec.europa.eu/pvg_tools/en/

    Parameters
    ----------
    times: series
        Typically, datetime index series
    latitude: float
        Latitude of a specific location
    longitude: float
        Longitude of a specific location
    tz: string
        Default is UTC. Please specify the timezone for which you want to
        localize the data
    Returns
    -------
    dni_comp: dataframe
        dataframe with TMY-GHI times in tz-aware timezone.
    """
    webUrl = 'https://re.jrc.ec.europa.eu/api/tmy?lat=' + str(latitude) \
             + '&lon=' + str(longitude) + '&usehorizon=0&browser=1'
    tmy = pd.read_csv(webUrl, sep=',', header=0, skiprows=16,
                      skipfooter=12, engine='python')
    tmy.loc[:, 'datetime'] = [datetime.strptime(n, '%Y%m%d:%H%M')
                              for n in tmy.loc[:, 'time(UTC)']]
    if times[0].year != times[-1].year:
        first_index = tmy[(tmy.datetime.dt.month == times[0].month) &
                          (tmy.datetime.dt.day == times[0].day)].index
        a = tmy.loc[:first_index[0] - 1, :]
        b = tmy.loc[first_index[0] - 1:, :]
        b.loc[:, 'datetime'] = [n.replace(year=times[0].year)
                                for n in b.datetime]
        a.loc[:, 'datetime'] = [n.replace(year=times[-1].year)
                                for n in a.datetime]
    else:
        tmy.loc[:, 'datetime'] = [n.replace(year=times[0].year)
                                     for n in tmy.datetime]
    tmy = tmy.set_index('datetime')
    tmy = tmy.sort_index(axis=0)

    # date filter
    tmy_f = tmy[(tmy.index >= times[0].strftime("%Y-%m-%d")) &
                        (tmy.index <= (times[-1] + pd.to_timedelta(
                            '1D')).strftime("%Y-%m-%d"))]

    dni_comp = pd.DataFrame(index=tmy_f.index, columns=['dni', 'dhi', 'airmass', 'dni_extra'])
    dni_comp['dni'] = tmy_f['Gb(n)'].values
    dni_comp['ghi'] = tmy_f['G(h)'].values
    dni_comp['dhi'] = tmy_f['Gd(h)'].values

    # Resample at 10min
    dni_comp = dni_comp[['ghi']].resample('10min').interpolate(order=2)

    # UTC to local time
    dni_comp.index = dni_comp.index.tz_localize('UTC').tz_convert(tz=tz)

    return dni_comp
