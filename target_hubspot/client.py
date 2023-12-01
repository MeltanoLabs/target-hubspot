import json
from enum import Enum
from logging import Logger

import requests

from target_hubspot.auth import AuthenticationHandler
from target_hubspot.config import ConfigInheriter
from target_hubspot.constants import HUBSPOT_ROOT_URL, TargetConfig
from target_hubspot.decorators import retry_hubspot
from target_hubspot.exceptions import RetryException
from target_hubspot.model import BatchCreateProperties, BatchUpdateContacts, CreatePropertyGroup


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"

class HubspotClient(ConfigInheriter):
    """
    Responsible:
    - Extremely thin wrapper over HubSpot API, making all requests and returning strongly typed response bodies (intent = keep mapping out of this class)
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

    @retry_hubspot
    def _post(self, url: str, body: dict) -> None:
        self._logger.info(f"POST {url}")
        response = requests.post(
            HUBSPOT_ROOT_URL + "/crm/v3/objects/contacts/batch/update",
            json=body,
            headers=self._authentication_handler.http_headers
        )
        self._logger.info(f"{url} HTTP {response.status_code}")
        if response.status_code == 409:
            return # we almost always intend an upsert, so 409s aren't an issue
        if response.status_code >= 500 or response.status_code == 429:
            raise RetryException()
        if response.status_code >= 400:
            raise Exception(f"{url} (status {response.status_code}): {response.text}. Payload: {json.dumps(body, indent=2)}")

    def batch_update_contacts(self, payload: BatchUpdateContacts.RequestPayload) -> None:
        self._post(
            url=HUBSPOT_ROOT_URL + "/crm/v3/objects/contacts/batch/update",
            body=payload.model_dump(exclude_none=True)
        )

    def batch_create_properties(self, payload: BatchCreateProperties.RequestPayload) -> None:
        self._post(
            url=HUBSPOT_ROOT_URL + f"/crm/v3/properties/{self._config.object_type}/batch/create",
            body=payload.model_dump(exclude_none=True)
        )

    def create_property_group(self, payload: CreatePropertyGroup.RequestPayload) -> None:
        self._post(
            url=HUBSPOT_ROOT_URL + f"/crm/v3/properties/{self._config.object_type}/groups",
            body=payload.model_dump(exclude_none=True)
        )
