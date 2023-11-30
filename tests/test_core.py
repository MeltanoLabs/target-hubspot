"""Tests standard target features using the built-in SDK tests library."""

from __future__ import annotations

import json
import os
import typing as t

import pytest
from singer_sdk.testing import get_target_test_class

from target_hubspot.constants import TargetConfig
from target_hubspot.target import TargetHubSpot

# TODO: Initialize minimal target config

SAMPLE_CONFIG: TargetConfig = TargetConfig(
    **json.load(
        open(os.path.join(".secrets", "config.json"))
    )
)


# Run standard built-in target tests from the SDK:
StandardTargetTests = get_target_test_class(
    target_class=TargetHubSpot,
    config=SAMPLE_CONFIG.model_dump(),
    include_target_tests=False # TODO: Enable after I have my feet under myself
)

def get_test_target_lines(filename: str) -> t.IO[str]:
    return open(f"{os.path.dirname(__file__)}/resources/{filename}")

class TestTargetHubSpot(StandardTargetTests):  # type: ignore[misc, valid-type]  # noqa: E501
    """Standard Target Tests."""

    @pytest.fixture(scope="class")
    def resource(self) -> t.Literal["resource"]:  # noqa: ANN201
        """Generic external resource.

        This fixture is useful for setup and teardown of external resources,
        such output folders, tables, buckets etc. for use during testing.

        Example usage can be found in the SDK samples test suite:
        https://github.com/meltano/sdk/tree/main/tests/samples
        """
        return "resource"

    @pytest.fixture(scope="class")
    def target(self) -> TargetHubSpot:
        return TargetHubSpot(config=SAMPLE_CONFIG.model_dump())

    def test_happy_path(self, target: TargetHubSpot) -> None:
        target._process_lines(get_test_target_lines("contacts.jsonl"))
