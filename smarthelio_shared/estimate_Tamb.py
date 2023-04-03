import pandas as pd
import numpy as np
import datetime
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

def estimate_air_temperature(df_in, lat, long, tz, utc=True):
    """Estimating Ambient Temperature from TMY using lat and long
    """

    webUrl = 'https://re.jrc.ec.europa.eu/api/tmy?lat=' + str(lat) + '&lon=' \
             + str(long) + '&usehorizon=0&browser=1'
    tmy = pd.read_csv(webUrl, sep=',', header=0, skiprows=16, skipfooter=12,
                         engine='python')
    tmy.loc[:,'yday'] = [datetime.strptime(n, '%Y%m%d:%H%M').timetuple().tm_yday
                            for n in tmy.loc[:,'time(UTC)']]
    tmy.loc[:, 'datetime'] = [datetime.strptime(n, '%Y%m%d:%H%M') for n
                                 in tmy.loc[:, 'time(UTC)']]
    times = df_in.index
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
    # UTC to local time
    if utc:
        tmy_f.index = tmy_f.index.tz_localize('UTC').tz_convert(tz=tz)

    # Resample at freq of times
    freq = int(np.median(np.diff(times.values)) / 1e9/60)
    tmy_f = tmy_f[['T2m']].resample(str(freq)+'min').fillna(method='ffill')
    tmy_f.columns = ['Tamb']

    # Adding TMY Tamb to df_in
    df_in = pd.concat([df_in, tmy_f], axis=1)
    df_in['Tamb'] = df_in['Tamb'].bfill()

    return df_in.Tamb


