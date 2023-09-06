import re
import pandas as pd
from datetime import datetime
from smarthelio_shared.api_retry import retry_session


DEFAULT_DATE = datetime.today().strftime("%Y-%m-%d")


def is_valid_date_format(date_string):
    """
    Check if a string date is in 'YYYY-MM-DD' format.

    Parameters:
    - date_string (str): The string date to check.

    Returns:
    - bool: True if the date string is in 'YYYY-MM-DD' format, False otherwise.
    """
    # Define a regular expression pattern for 'YYYY-MM-DD' format
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'

    # Use re.match to check if the date string matches the pattern
    if re.match(date_pattern, date_string):
        return True
    else:
        return False


def get_sunset_and_sunrise_times(lat, long, formatted_date_string=DEFAULT_DATE):
    """
    Retrieve the sunrise and sunset times for a given latitude and longitude.

    Parameters:
    - lat (float): The latitude of the location.
    - long (float): The longitude of the location.
    - formatted_date_string (str, optional): The date for which you want to retrieve sunrise and sunset times
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

    # convert date into the string format YYYY-MM-DD
    if not is_valid_date_format(formatted_date_string):
        raise Exception(f"Invalid Date Format - {formatted_date_string}; SHOULD BE: YYYY-MM-DD")

    # Construct the base URL for the API request
    base_url = f"https://api.sunrisesunset.io/json?lat={lat}&lng={long}&date={formatted_date_string}"

    # Make a GET request to the API
    session = retry_session(base_url)
    response = session.get(base_url)

    try:
        # Parse the JSON response
        response_json = response.json()

        # Extract sunrise and sunset times from the response
        sunrise = response_json['results']['sunrise']
        sunset = response_json['results']['sunset']

        # Convert to string format
        sunrise_str = pd.to_datetime(sunrise).floor('30T').strftime('%H:%M')
        sunset_str = pd.to_datetime(sunset).ceil('30T').strftime('%H:%M')

        return sunrise_str, sunset_str

    except Exception as e:
        print(f'Error: {e}')
