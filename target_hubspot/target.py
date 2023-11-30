"""HubSpot target class."""

from __future__ import annotations

from singer_sdk import typing as th
from singer_sdk.target_base import Target

from target_hubspot.model import HubspotObjectsEnum
from target_hubspot.sinks import (
    HubSpotSink,
)


class TargetHubSpot(Target):
    """Sample target for HubSpot."""

    max_size = 1_000

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
            description="The OAuth app refresh token.",
        ),

        # We attempt to upload new data to HubSpot for the provided stream identifier
        th.Property(
            "stream_identifier",
            th.StringType,
            required=True,
            description=f"The OAuth app refresh token. Supported types: {HubspotObjectsEnum.__members__.values()}",
        ),
        th.Property(
            "filepath",
            th.StringType,
            required=True,
            description="The OAuth app refresh token.",
        ),
    ).to_dict()

    default_sink_class = HubSpotSink


if __name__ == "__main__":
    TargetHubSpot.cli()
