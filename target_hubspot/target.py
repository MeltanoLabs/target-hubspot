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
                        description="The name of the column header. This is based on the stream from a tap.",
                    ),
                    th.Property(
                        "propertyName",
                        th.StringType,
                        required=True,
                        description="The internal name of the HubSpot property that the data will map to. Settings -> Data Management -> Properties. Then select the object type from the drop down, search for the property, click on it, then next to the label is a code symbol that will show you the internal name for the property.",
                    ),
                    th.Property(
                        "columnObjectTypeId",
                        th.StringType,
                        required=True,
                        description="The name or objectTypeId value of the object or activity to which the data belongs, for example `0-1` for contacts or `2-123456` for a custom object. Refer to [this article](https://developers.hubspot.com/docs/api/crm/understanding-the-crm#object-type-id) for a full list of objectTypeId values.",
                    ),
                    th.Property(
                        "columnType",
                        th.StringType,
                        allowed_values=[
                            "HUBSPOT_OBJECT_ID",
                            "HUBSPOT_ALTERNATE_ID",
                        ],
                        description="An optional field used to specify that a column contains a unique identifier property. This is how the import knows that field to update/upsert on. See the [unique identifier docs](https://developers.hubspot.com/docs/api/crm/understanding-the-crm) for more details.",
                    ),
                )
            ),
            required=True,
            description="An array including an object entry for each column in your import file stream. Columns are matched to stream properties by `columnName`; stream properties without an entry are not imported.",
        ),
        th.Property(
            "date_format",
            th.StringType,
            description="The format the target writes date values in. Date and time values are written as UNIX timestamps in milliseconds.",
            default="YEAR_MONTH_DAY",
            allowed_values=[
                "MONTH_DAY_YEAR",
                "YEAR_MONTH_DAY",
                "DAY_MONTH_YEAR",
            ],
        ),
        th.Property(
            "import_operations",
            th.StringType,
            description="Used to indicate whether the import should create and update, only create, or only update records. Applies to every object type in the column mapping.",
            default="UPDATE",
            allowed_values=[
                "CREATE",
                "UPDATE",
                "UPSERT",
            ],
        ),
        th.Property(
            "import_timeout_seconds",
            th.IntegerType,
            description="How long to wait for HubSpot to finish each import before failing the run.",
            default=3600,
        ),
    ).to_dict()

    default_sink_class = HubSpotSink


if __name__ == "__main__":
    TargetHubSpot.cli()
