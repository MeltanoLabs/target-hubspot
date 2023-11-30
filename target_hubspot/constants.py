from enum import Enum

from pydantic import Field
import target_hubspot.pydantic_config


class HubspotStreamsEnum(str, Enum):
    CONTACTS = "contacts"
    COMPANIES = "companies"

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

    stream_identifier: HubspotStreamsEnum = Field(
        ...,
        description=f"The stream identifier to upload data to. Supported types: {HubspotStreamsEnum.__members__.values()}",
    )
    filepath: str = Field(
        ...,
        description="The file path to upload data from.",
    )