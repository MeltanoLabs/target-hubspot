"""Tests standard target features using the built-in SDK tests library."""

from __future__ import annotations

import json
import os
from pathlib import Path

from singer_sdk.testing import TargetTestRunner

from target_hubspot.constants import TargetConfig
from target_hubspot.target import TargetHubSpot

SAMPLE_CONFIG: TargetConfig = TargetConfig(
    **json.load(
        open(os.path.join(".secrets", "config.json"))
    )
)


def _run_on_path(filepath: str) -> None:
    runner = TargetTestRunner(
        target_class=TargetHubSpot,
        config=SAMPLE_CONFIG.model_dump(),
        input_filepath=Path(filepath),
    )
    runner.sync_all()


def test_contacts() -> None:
    _run_on_path("./tests/resources/contacts.jsonl")
