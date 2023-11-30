from enum import Enum
from typing import List, Literal, Optional

import target_hubspot.pydantic_config


class HubspotObjectsEnum(str, Enum):
    # There exist more than this, but these are Jon's "big three" that we probably want to support right out of the gate
    CONTACTS = "contacts"
    COMPANIES = "companies"
    DEALS = "deals"


class GetNewToken:
    class RequestPayload(target_hubspot.pydantic_config.BaseConfig):
        grant_type: Literal["refresh_token"] = "refresh_token"
        client_id: str
        client_secret: str
        refresh_token: str

    class ResponseBody(target_hubspot.pydantic_config.BaseConfig):
        access_token: str
        refresh_token: str
        expires_in: int


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


class _BatchCreatePropertiesRequestPayloadItem(target_hubspot.pydantic_config.BaseConfig):
    # Derived from: https://developers.hubspot.com/docs/api/crm/properties
    hidden: Optional[bool] = None
    displayOrder: Optional[int] = None
    description: Optional[str] = None
    label: str
    type: HubspotDataTypes
    formField: Optional[bool] = None
    groupName: str
    referencedObjectType: Optional[str] = None
    name: str
    options: Optional[List[str]] = None
    calculationFormula: Optional[str] = None
    hasUniqueValue: Optional[bool] = None
    fieldType: HubspotFieldTypes
    externalOptions: Optional[bool] = None


class BatchCreateProperties:
    class RequestPayload(target_hubspot.pydantic_config.BaseConfig):
        items: List[_BatchCreatePropertiesRequestPayloadItem]
        objectType: HubspotObjectsEnum


class BatchUpdateContacts:
    class RequestPayloadItem(target_hubspot.pydantic_config.BaseConfig):
        vid: int
        properties: list[dict]

    class ResponseBody(target_hubspot.pydantic_config.BaseConfig):
        pass
