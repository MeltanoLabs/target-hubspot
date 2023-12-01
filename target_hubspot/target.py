"""HubSpot target class."""

from __future__ import annotations

from singer_sdk import typing as th
from singer_sdk.target_base import Target

from target_hubspot.model import HubspotObjectsEnum
from target_hubspot.parameters import MELTANO_MAX_BATCH_SIZE
from target_hubspot.sinks import (
    HubSpotSink,
)


class TargetHubSpot(Target):
    """Sample target for HubSpot."""

    max_size = MELTANO_MAX_BATCH_SIZE

    name = "target-hubspot"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "client_id",
            th.StringType,
            required=True,
            description="The OAuth app client ID.",
        ),
        th.Property(
            "client_secret",
            th.StringType,
            required=True,
            secret=True,
            description="The OAuth app client secret.",
        ),
        th.Property(
            "refresh_token",
            th.StringType,
            required=True,
            secret=True,
            description="The refresh token we have on file for the user whose data we're exporting.",
        ),
        th.Property(
            "object_type",
            th.StringType,
            required=True,
            description=f"The HubSpot object type the records should be pushed up to. Supported types: {HubspotObjectsEnum.__members__.values()}",
        )
    ).to_dict()

    default_sink_class = HubSpotSink


if __name__ == "__main__":
    TargetHubSpot.cli()
