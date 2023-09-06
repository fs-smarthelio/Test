import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


def retry_session(url, retries=3, backoff_factor=3, allowed_error_list=None, allowed_request_type=None):

    if allowed_error_list is None:
        allowed_error_list = [502, 503, 504]

    if allowed_request_type is None:
        raise Exception("Empty allowed_request_type param received!")
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=allowed_error_list,
        method_whitelist=frozenset(allowed_request_type)
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount(url, adapter)
    return session