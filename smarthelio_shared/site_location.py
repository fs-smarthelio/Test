import pandas as pd
import requests

from datetime import date
from pvlib.location import Location


def get_site_location(latitude, longitude, altitude, tz):
    """
    Creates a PVLib location object.

    Parameters
    ----------
    latitude : Float
        Latitude of the system given in float.
    longitude : Float
        Longitude of the system given in float.
    altitude : Float
        Elevation with respect to the sea level in m. Given in float.
    tz : String
        Timezone of the location given in string.

    Returns
    -------
    site_location : PVLib object
        Returns a location object from PVLib Library.
    """
    # set the location and the time zone for the PV system based on PVLib
    site_location = Location(
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        tz=tz)
    return site_location


def get_timezone_from_lat_long(latitude, longitude):
    """
    Get timezone using Google maps API.

    Parameters
    ----------
    latitude: float
        Latitude of the location.
    longitude: float
        Longitude of the location.

    Returns
    -------
    tz_string: str
        The timezone string of the location.
    """
    API_KEY = 'AIzaSyD4i_GTPLSlISs3CDukyn4sPqTXybd66hs'
    BASE_URL = 'https://maps.googleapis.com/maps/api/timezone/'
    timestamp = pd.to_datetime(date.today()).timestamp()
    response = requests.get(
        BASE_URL + 'json?location={},{}&timestamp={}&key={}'.format(
            latitude, longitude, timestamp, API_KEY))
    api_response_dict = response.json()
    tz_string = api_response_dict['timeZoneId']

    return tz_string
