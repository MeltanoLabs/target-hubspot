"""HubSpot target class."""

from __future__ import annotations

from singer_sdk import typing as th
from singer_sdk.target_base import Target

from target_hubspot.sinks import (
    HubSpotSink,
)


class TargetHubSpot(Target):
    """Sample target for HubSpot."""

    name = "target-hubspot"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "access_token",
            th.StringType,
            secret=True,
            required=True,
            description="Your HubSpot private app API access token. See the [docs](https://developers.hubspot.com/docs/api/private-apps) for more details.",
        ),
        th.Property(
            "column_mapping",
            th.ArrayType(
                th.ObjectType(
                    th.Property(
                        "columnName",
                        th.StringType,
                        required=True,
                        description=""
                    ),
                    th.Property(
                        "propertyName",
                        th.StringType,
                        required=True,
                        description=""
                    ),
                    th.Property(
                        "columnObjectTypeId",
                        th.StringType,
                        required=True,
                        # TODO validate this some other way since you can use custom values
                        allowed_values=["0-1", "0-2", "0-3", "0-5", "0-48", "0-49", "0-47", "0-4", "0-27", "0-7", "0-8", "0-18", "0-116", "0-54", "0-19"],
                        description="https://developers.hubspot.com/docs/api/crm/understanding-the-crm#object-type-id"
                    ),
                    th.Property(
                        "columnType",
                        th.StringType,
                        allowed_values=[
                            "HUBSPOT_OBJECT_ID",
                            "HUBSPOT_ALTERNATE_ID",
                        ],
                        description="https://developers.hubspot.com/docs/api/crm/understanding-the-crm"
                    )
                )
            ),
            required=True,
            description="",
        ),
        th.Property(
            "date_format",
            th.StringType,
            description="",
            default="YEAR_MONTH_DAY",
            allowed_values=[
                "MONTH_DAY_YEAR",
                "YEAR_MONTH_DAY",
                "DAY_MONTH_YEAR",
            ]
        ),
        th.Property(
            "import_operations",
            th.StringType,
            description="",
            default="UPDATE",
            allowed_values=[
                "CREATE",
                "UPDATE",
                "UPSERT",
            ]
        ),
    ).to_dict()

    default_sink_class = HubSpotSink


if __name__ == "__main__":
    TargetHubSpot.cli()
