import requests
import pandas as pd
from smarthelio_shared import MetadataAPI


class VisualCrossingGHI:
    def __init__(self, base_url, api_key, meta_db_api: MetadataAPI):
        self.base_url = base_url
        self.api_key = api_key
        self.meta_db_api = meta_db_api

    def get_visual_crossing_raw_data(self, latitude, longitude, start_date, end_date):
        """Get raw data from Visual crossing."""
        response = requests.get(
            self.base_url + '/{},{}/{}/{}?unitGroup=metric&key={}&include=hours&elements=datetime,solarradiation'.format(
                latitude, longitude, start_date, end_date, self.api_key))
        data = response.json()

        df = pd.DataFrame(data['days'])
        df.dropna(subset=['hours'], inplace=True)

        total_df = pd.DataFrame()
        shape = df.shape[0]

        for i in range(0, shape):
            dataframe = pd.DataFrame(df.hours.loc[i])
            dataframe['date'] = df['datetime'].loc[i]
            total_df = pd.concat([total_df, dataframe])

        # convert datetime format into 'YYYY-MM-DD HH:MM:00
        total_df['datetime'] = total_df['date'] + ' ' + total_df['datetime']
        total_df['datetime'] = pd.to_datetime(total_df['datetime'])
        total_df.set_index('datetime', inplace=True)
        total_df.drop('date', axis=1, inplace=True)

        return total_df

    def get_specific_data(self, all_data):
        """Filter the dataframe."""
        final = all_data[['solarradiation']].copy()
        final.rename(columns={'solarradiation': 'GHI'}, inplace=True)
        return final

    def localize_timestamps(self, dataframe, timezone_string):
        """Localize UTC timestamps to specific location."""
        # Localize timestamps
        dataframe['datetime'] = pd.to_datetime(dataframe['datetimeEpoch'], unit='s',
                                               utc=True).dt.tz_convert(timezone_string)
        dataframe.set_index('datetime', inplace=True)
        dataframe.index = dataframe.index.tz_localize(None)
        dataframe.drop(columns=['datetimeEpoch'], inplace=True)
        return dataframe

    def get_ghi_from_visualcrossing(self, plant_id, start_date, end_date):
        """Get irradiance data from Visual crossing.

        Inputs
        -------

        plant_id: int
            ID of the plant as used in MetaDb.
        start_date: string
            format: YYYY-MM-DD HH:MM
        end_date: string
            format: YYYY-MM-DD HH:MM

        Returns
        -------

        vc_ghi: dataframe
            dataframe with datetime index and hourly values of GHI
        """
        # Step 1 - Get latitude and longitude from plant_id
        plant_table = self.meta_db_api.get_plant_info_from_plant_id(plant_id)
        latitude = plant_table['latitude'].iloc[0]
        longitude = plant_table['longitude'].iloc[0]

        # Get data from Visual crossing
        vc_ghi = self.get_visual_crossing_raw_data(latitude, longitude, start_date, end_date)

        return vc_ghi
