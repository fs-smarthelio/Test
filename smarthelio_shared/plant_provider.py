import pytz
import datetime
from datetime import timezone
from smarthelio_shared import MetadataAPI


def convert_date(current_utc_time, destination_time_zone):
    utc_moment = current_utc_time.replace(tzinfo=pytz.utc)
    return utc_moment.astimezone(pytz.timezone(destination_time_zone))


class PlantProvider:
    def __init__(self, metadb_api: MetadataAPI):
        self.metadb_api = metadb_api

    def get_plants_to_run_at(self, hour):
        plants = self.metadb_api.get_plants().to_dict()

        if len(plants) == 0:
            print(f'No plants found in Metadata-API')
            return []

        result = []
        for plant_index in plants['plant_id']:
            plant_id = plants['plant_id'][plant_index]
            plant_timezone = plants['timezone'][plant_index]

            localised_date = convert_date(datetime.datetime.now(timezone.utc), plant_timezone)

            if localised_date.hour == hour:
                result.append(plant_id)

        return result

