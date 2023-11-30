from logging import Logger
from typing import Callable, List

import requests
import tenacity

from target_hubspot.auth import AuthenticationHandler
from target_hubspot.config import ConfigInheriter
from target_hubspot.constants import HUBSPOT_ROOT_URL, TargetConfig
from target_hubspot.exceptions import RetryException
from target_hubspot.model import BatchCreateProperties, BatchUpdateContacts


def _retry_hubspot(f: Callable) -> Callable:
    return tenacity.retry(
        retry=tenacity.retry_if_exception_type(RetryException)
    )(f)


class HubspotClient(ConfigInheriter):
    """
    Responsible:
    - Extremely thin wrapper over HubSpot API, making all requests and returning strongly typed response bodies
    - Handle retry logic, including 5xx (HubSpot issue) and 429 (rate limit)

    NOT responsible:
    - Data format mapping
    - Ensuring we have a valid auth token (handled by AuthenticationHandler)

    We create our own client around the Hubspot API rather than using their SDK because:
    - Their SDK does not have good static typing support
    - We need to ensure we regularly refresh our auth token; the SDKs are unclear whether they handle this, and they likely don't (as initializing the client doesn't require id/secret/refrehs) so it's best to just handle that logic ourselves
    """
    _authentication_handler: AuthenticationHandler

    def __init__(self, config: TargetConfig, logger: Logger) -> None:
        super().__init__(config=config, logger=logger)
        self._authentication_handler = AuthenticationHandler(
            config=config,
            logger=logger
        )

    @_retry_hubspot
    def batch_update_contacts(self, contacts: List[BatchUpdateContacts.RequestPayloadItem]) -> None:
        response = requests.post(
            HUBSPOT_ROOT_URL + "/contacts/v1/contact/batch/",
            json=[contact.model_dump() for contact in contacts],
            headers=self._authentication_handler.http_headers
        )
        if response.status_code >= 500 or response.status_code == 429:
            raise RetryException()
        if response.status_code >= 400:
            raise Exception(f"Error uploading contacts (status {response.status_code}): {response.text}")

    @_retry_hubspot
    def batch_create_properties(self, contacts: BatchCreateProperties.RequestPayload) -> None:
        response = requests.post(
            HUBSPOT_ROOT_URL + "/contacts/v1/contact/batch/",
            json=contacts.model_dump(),
            headers=self._authentication_handler.http_headers
        )
        if response.status_code >= 500 or response.status_code == 429:
            raise RetryException()
        if response.status_code >= 400:
            raise Exception(f"Error uploading contacts (status {response.status_code}): {response.text}")
