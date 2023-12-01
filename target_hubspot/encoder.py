import decimal
from typing import Any

from target_hubspot.model import HubspotDataTypes, HubspotFieldTypes


class TypeInferenceUtils:

    @staticmethod
    def determine_hubspot_data_type_for_object(v: Any) -> HubspotDataTypes:
        try:
            float(v)
            return HubspotDataTypes.NUMBER
        except:
            pass
        try:
            int(v)
            return HubspotDataTypes.NUMBER
        except:
            pass
        # TODO: THis can be much more thorough, especially with regard to categorical types, but is good enough for now
        return HubspotDataTypes.STRING

    @staticmethod
    def determine_hubspot_field_type_for_object(v: Any) -> HubspotFieldTypes:
        try:
            float(v)
            return HubspotFieldTypes.NUMBER
        except:
            pass
        try:
            int(v)
            return HubspotFieldTypes.NUMBER
        except:
            pass
        # TODO: THis can be much more thorough, especially with regard to categorical types, but is good enough for now
        return HubspotFieldTypes.TEXT

    @staticmethod
    def coerce_to_json_serializable(v: Any) -> Any:
        if isinstance(v, decimal.Decimal):
            # We technically lose precision here (the lossless solution is to cast Decimal to string anyway), but being able to represent as a number in HubSpot is worth the edge case tradeoff
            return float(v)
        return v