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
            "filepath",
            th.StringType,
            description="The path to the target output file",
        ),
        th.Property(
            "file_naming_scheme",
            th.StringType,
            description="The scheme with which output files will be named",
        ),
        th.Property(
            "auth_token",
            th.StringType,
            secret=True,  # Flag config as protected.
            description="The path to the target output file",
        ),
    ).to_dict()

    default_sink_class = HubSpotSink


if __name__ == "__main__":
    TargetHubSpot.cli()
