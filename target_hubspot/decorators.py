from typing import Callable

import tenacity

from target_hubspot.exceptions import RetryException
from target_hubspot.parameters import HUBSPOT_TIME_BETWEEN_RETRIES, HUBSPOT_TIMEOUT_MINUTES

_SECONDS_PER_MINUTE = 60

# TODO: These values can (and should) be tuned eventually

def retry_hubspot(f: Callable) -> Callable:
    return tenacity.retry(
        retry=tenacity.retry_if_exception_type(RetryException),
        stop=tenacity.stop_after_delay(HUBSPOT_TIMEOUT_MINUTES * _SECONDS_PER_MINUTE), # five minutes should be more than enough to circumvent any rate limiting (we could probably even get away with 2, but that neglects that a single person may have multiple HubSpot deployments running concurrently)
        wait=tenacity.wait_random_exponential(multiplier=1.2, max=HUBSPOT_TIME_BETWEEN_RETRIES),
    )(f)
