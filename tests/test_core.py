"""Tests standard target features using the built-in SDK tests library."""

from __future__ import annotations

import json
import os
from pathlib import Path

from singer_sdk.testing import TargetTestRunner

from target_hubspot.model import TargetConfig
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
    # basic test that we can push contact updates in bulk to HubSpot
    _run_on_path("./tests/resources/contacts.jsonl")

def test_companies() -> None:
    # basic test that we can push companies updates in bulk to HubSpot
    _run_on_path("./tests/resources/companies.jsonl")

def test_deals() -> None:
    # basic test that we can push deals updates in bulk to HubSpot
    _run_on_path("./tests/resources/deals.jsonl")