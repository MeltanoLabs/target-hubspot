"""HubSpot Authentication."""
import time
from logging import Logger

import requests

from target_hubspot.client import _retry_hubspot
from target_hubspot.config import ConfigInheriter
from target_hubspot.constants import HUBSPOT_ROOT_URL, TargetConfig
from target_hubspot.exceptions import RetryException
from target_hubspot.model import GetNewToken

_THIRTY_SECONDS = 30


class AuthenticationHandler(ConfigInheriter):
    """
    Responsibilities:
    - Provide a @property representing an access token that is guaranteed to be valid (handles refreshing internally)
    """
    _expiration_timestamp_seconds: int = 0  # always start out as stale
    _access_token: str

    def __init__(self, config: TargetConfig, logger: Logger) -> None:
        super().__init__(config=config, logger=logger)

    @property
    def http_headers(self) -> dict:
        # AuthenticationHandler automatically refreshes this when stale
        return {"Authorization": f"Bearer {self.access_token}"}

    @property
    def access_token(self) -> str:
        # This is the extent of the public interface; a single property that automatically refreshes itself when stale (without requiring a network hop to check)
        if self._is_token_stale:
            self._access_token = self._get_token()
        return self._access_token

    @_retry_hubspot
    def _get_token(self) -> str:
        response = requests.post(
            HUBSPOT_ROOT_URL + "/oauth/v1/token",
            json=self._refresh_token_body
        )
        if response.status_code >= 500 or response.status_code == 429:
            raise RetryException()  # trigger retry
        if response.status_code >= 400:
            raise Exception(f"Error refreshing token (status {response.status_code}): {response.text}")
        body = GetNewToken.ResponseBody(**response.json())
        self._expiration_timestamp_seconds = int(time.time()) + body.expires_in
        self._logger.info(f"Successfully refreshed token. New one expires in {body.expires_in} seconds.")
        return body.access_token

    @property
    def _is_token_stale(self) -> bool:
        # check stale; give us a bit of flexiblity, as we'd rather refresh too early rather than too late
        return time.time() > (self._expiration_timestamp_seconds - _THIRTY_SECONDS)

    @property
    def _refresh_token_body(self) -> GetNewToken.RequestPayload:
        return GetNewToken.RequestPayload(
            client_id=self._config.client_id,
            client_secret=self._config.client_secret,
            refresh_token=self._config.refresh_token
        )
