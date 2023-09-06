import pandas as pd
from datetime import datetime
from smarthelio_shared.api_retry import retry_session

def get_sunset_and_sunrise_times(lat, long, date=None):
    """
    Retrieve the sunrise and sunset times for a given latitude and longitude.

    Parameters:
    - lat (float): The latitude of the location.
    - long (float): The longitude of the location.
    - date (str, optional): The date for which you want to retrieve sunrise and sunset times
      in the format 'YYYY-MM-DD'. If not provided, it defaults to today's date.

    Returns:
    - sunrise (str): The time of sunrise in 'HH:MM' format.
    - sunset (str): The time of sunset in 'HH:MM' format.

    Note:
    This function makes an API request to 'https://api.sunrisesunset.io/json' to get
    sunrise and sunset times based on the provided latitude, longitude, and date.
    The returned times are in LAT (Local Apparent Time).
    """

    # Convert latitude and longitude to strings
    lat = str(lat)
    long = str(long)

    # Construct the base URL for the API request
    base_url = f"https://api.sunrisesunset.io/json?lat={lat}&lng={long}"

    # Include the date parameter if provided
    if date is not None:
        date = pd.to_datetime(date).strftime('%Y-%m-%d')
        base_url = base_url + f"&date={date}"
    else:
        date = datetime.today().strftime('%Y-%m-%d')
        base_url = base_url + f"&date={date}"

    # Initialize empty payload and headers
    payload = {}
    headers = {}

    # Make a GET request to the API
    session = retry_session(base_url, retries=3, backoff_factor=0.1, allowed_request_type=['GET'])
    response = session.get(base_url, headers=headers, data=payload)

    # Parse the JSON response
    response_json = response.json()

    # Extract sunrise and sunset times from the response
    sunrise = response_json['results']['sunrise']
    sunset = response_json['results']['sunset']

    # Convert to string format
    sunrise_str = pd.to_datetime(sunrise).floor('30T').strftime('%H:%M')
    sunset_str = pd.to_datetime(sunset).ceil('30T').strftime('%H:%M')

    return sunrise_str, sunset_str
