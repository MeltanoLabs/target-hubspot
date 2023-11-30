from pydantic import Field

import target_hubspot.pydantic_config
from target_hubspot.model import HubspotObjectsEnum


class TargetConfig(target_hubspot.pydantic_config.BaseConfig):
    # We define our config both here and in the main `target.py` file because the SDK checks at runtime but does not get you mypy-level type safety like we want
    client_id: str = Field(
        ...,
        min_length=1,
        description="Our OAuth app client ID.",
    )
    client_secret: str = Field(
        ...,
        min_length=1,
        description="Our OAuth app client secret. Persistent across all installs, but we still allow it to be injected.",
    )
    refresh_token: str = Field(
        ...,
        min_length=1,
        description="The refresh token of the current user's OAuth connection.",
    )

    stream_identifier: HubspotObjectsEnum = Field(
        ...,
        description=f"The object type to upload data to. Supported types: {HubspotObjectsEnum.__members__.values()}",
    )
    filepath: str = Field(
        ...,
        description="The file path to upload data from.",
    )


HUBSPOT_ROOT_URL = "https://api.hubapi.com"
