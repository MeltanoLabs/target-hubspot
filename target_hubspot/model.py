from enum import Enum

from pydantic import Field

import target_hubspot.pydantic_config


class HubspotObjectsEnum(str, Enum):
    # There exist more than this, but these are Jon's "big three" that we probably want to support right out of the gate
    CONTACTS = "contacts"
    COMPANIES = "companies"
    DEALS = "deals"


class HubspotDataTypes(str, Enum):
    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    DATETIME = "datetime"
    ENUMERATION = "enumeration"
    BOOL = "bool"


class HubspotFieldTypes(str, Enum):
    TEXTAREA = "textarea"
    TEXT = "text"
    DATE = "date"
    FILE = "file"
    NUMBER = "number"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    BOOLEAN_CHECKBOX = "booleancheckbox"
    CALCULATION_EQUATIUON = "calculation_equation"


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

    object_type: HubspotObjectsEnum = Field(
        ...,
        description=f"The object type to upload data to. Supported types: {HubspotObjectsEnum.__members__.values()}",
    )
    filepath: str = Field(
        ...,
        description="The file path to upload data from.",
    )
