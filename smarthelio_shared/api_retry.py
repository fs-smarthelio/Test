import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


CODES_TO_RETRY_ON = frozenset([502, 503, 504])
METHODS_TO_RETRY_ON = frozenset(['GET', 'TRACE', 'HEAD', 'OPTIONS'])


def retry_session(url, retries=3, backoff_factor=3, codes_to_retry_on=CODES_TO_RETRY_ON,
                  methods_to_retry_on=METHODS_TO_RETRY_ON):
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=codes_to_retry_on,
        method_whitelist=methods_to_retry_on
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount(url, adapter)
    return session
