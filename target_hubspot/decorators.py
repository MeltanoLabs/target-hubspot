from typing import Callable

import tenacity

from target_hubspot.exceptions import RetryException


def retry_hubspot(f: Callable) -> Callable:
    return tenacity.retry(
        retry=tenacity.retry_if_exception_type(RetryException)
    )(f)
