from enum import Enum
from typing import Any, List, Literal, Optional

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


class HubspotPropertyPayload(target_hubspot.pydantic_config.BaseConfig):
    # Derived from: https://developers.hubspot.com/docs/api/crm/properties
    id: str
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
        inputs: List[HubspotPropertyPayload]

class HubspotContactUpdatePayload(target_hubspot.pydantic_config.BaseConfig):
    id: int # MUST be the basic hubspot id; they claim in the docs you can use email and supply idProperty=email, but the bulk update endpoint just straight-up doesn't support it and it's horribly undocumented
    properties: dict[str, Any]

class BatchUpdateContacts:
    class RequestPayload(target_hubspot.pydantic_config.BaseConfig):
        inputs: List[HubspotContactUpdatePayload]

    class ResponseBody(target_hubspot.pydantic_config.BaseConfig):
        pass

class CreatePropertyGroup:

    class RequestPayload(target_hubspot.pydantic_config.BaseConfig):
        name: str
        label: str
