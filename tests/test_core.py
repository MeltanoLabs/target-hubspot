"""Tests the HubSpot sink against a stubbed HubSpot API client."""

from __future__ import annotations

import io
import json
import typing as t
from types import SimpleNamespace
from unittest import mock

import pytest
from singer_sdk.testing import target_sync_test

from target_hubspot.exception import (
    ImportFailedException,
    ImportTimeoutException,
    InvalidColumnMappingException,
    PartialImportException,
)
from target_hubspot.target import TargetHubSpot

SAMPLE_CONFIG: dict[str, t.Any] = {
    "access_token": "test-token",
    "column_mapping": [
        {
            "columnName": "email",
            "propertyName": "email",
            "columnObjectTypeId": "0-1",
            "columnType": "HUBSPOT_ALTERNATE_ID",
        },
        {
            "columnName": "first_name",
            "propertyName": "firstname",
            "columnObjectTypeId": "0-1",
        },
        {
            "columnName": "birthday",
            "propertyName": "date_of_birth",
            "columnObjectTypeId": "0-1",
        },
        {
            "columnName": "signed_up_at",
            "propertyName": "signup_date",
            "columnObjectTypeId": "0-1",
        },
    ],
}

SCHEMA = {
    "type": "object",
    "properties": {
        "email": {"type": ["string", "null"]},
        "first_name": {"type": ["string", "null"]},
        "birthday": {"type": ["string", "null"], "format": "date"},
        "signed_up_at": {"type": ["string", "null"], "format": "date-time"},
        "internal_id": {"type": ["integer", "null"]},
    },
}

RECORD = {
    "email": "ada@example.com",
    "first_name": "Ada",
    "birthday": "1815-12-10",
    "signed_up_at": "2024-01-02T03:04:05+00:00",
    "internal_id": 7,
}


def singer_input(records: list[dict], schema: dict = SCHEMA) -> io.StringIO:
    messages = [
        {"type": "SCHEMA", "stream": "contacts", "schema": schema, "key_properties": []}
    ]
    messages += [{"type": "RECORD", "stream": "contacts", "record": r} for r in records]
    return io.StringIO("\n".join(json.dumps(m) for m in messages) + "\n")


def import_response(state: str, counters: dict | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id="123",
        state=state,
        metadata=SimpleNamespace(counters=counters or {}),
    )


class FakeHubSpot:
    """Captures the import request and file, and returns the configured states."""

    def __init__(self, states: list[SimpleNamespace]):
        self.states = list(states)
        self.requests: list[dict] = []
        self.files: list[str] = []
        self.crm = SimpleNamespace(
            imports=SimpleNamespace(
                core_api=SimpleNamespace(create=self.create, get_by_id=self.get_by_id),
                public_imports_api=SimpleNamespace(get_errors=self.get_errors),
            )
        )

    def create(self, files: str, import_request: str):
        with open(files, encoding="utf-8") as f:
            self.files.append(f.read())
        self.requests.append(json.loads(import_request))
        return self.states.pop(0)

    def get_by_id(self, import_id: int):
        return self.states.pop(0)

    def get_errors(self, import_id: int, **kwargs):
        return SimpleNamespace(
            results=[
                SimpleNamespace(error_type="INVALID_EMAIL", error_message="bad email")
            ]
        )


def run_target(
    states, config=None, records=(RECORD,), schema=SCHEMA, clock=lambda: 0
) -> FakeHubSpot:
    fake = FakeHubSpot(states)
    fake_time = SimpleNamespace(sleep=lambda seconds: None, monotonic=clock)
    with mock.patch("target_hubspot.sinks.HubSpot", return_value=fake), mock.patch(
        "target_hubspot.sinks.time", fake_time
    ):
        target = TargetHubSpot(config={**SAMPLE_CONFIG, **(config or {})})
        target_sync_test(target, singer_input(list(records), schema))
    return fake


def test_import_request_applies_operation_to_mapped_object_types():
    fake = run_target([import_response("STARTED"), import_response("DONE")])

    request = fake.requests[0]
    assert request["importOperations"] == {"0-1": "UPDATE"}
    assert request["dateFormat"] == "YEAR_MONTH_DAY"
    page = request["files"][0]["fileImportPage"]
    assert page["columnMappings"] == SAMPLE_CONFIG["column_mapping"]
    assert request["files"][0]["fileName"] == f"{request['name']}.csv"


def test_import_operation_covers_every_object_type():
    mappings = [
        {"columnName": "email", "propertyName": "email", "columnObjectTypeId": "0-1"},
        {
            "columnName": "first_name",
            "propertyName": "name",
            "columnObjectTypeId": "2-999",
        },
    ]
    fake = run_target(
        [import_response("DONE")],
        config={"column_mapping": mappings, "import_operations": "CREATE"},
    )

    assert fake.requests[0]["importOperations"] == {"0-1": "CREATE", "2-999": "CREATE"}


def test_csv_columns_follow_mapping_by_name():
    fake = run_target([import_response("DONE")])

    lines = fake.files[0].splitlines()
    # Mapping order, not alphabetical, and the unmapped internal_id is left out
    assert lines[0] == "email,first_name,birthday,signed_up_at"
    assert lines[1] == "ada@example.com,Ada,1815-12-10,1704164645000"


@pytest.mark.parametrize(
    ("date_format", "expected"),
    [("MONTH_DAY_YEAR", "12/10/1815"), ("DAY_MONTH_YEAR", "10/12/1815")],
)
def test_dates_follow_date_format(date_format, expected):
    fake = run_target([import_response("DONE")], config={"date_format": date_format})

    assert fake.files[0].splitlines()[1].split(",")[2] == expected
    assert fake.requests[0]["dateFormat"] == date_format


def test_unknown_column_name_fails():
    mappings = [
        *SAMPLE_CONFIG["column_mapping"],
        {"columnName": "emial", "propertyName": "email", "columnObjectTypeId": "0-1"},
    ]
    with pytest.raises(InvalidColumnMappingException, match="emial"):
        run_target([], config={"column_mapping": mappings})


def test_duplicate_column_name_fails():
    mappings = [*SAMPLE_CONFIG["column_mapping"], SAMPLE_CONFIG["column_mapping"][0]]
    with pytest.raises(InvalidColumnMappingException, match="email"):
        run_target([], config={"column_mapping": mappings})


@pytest.mark.parametrize("state", ["FAILED", "CANCELED", "REVERTED"])
def test_import_not_done_fails(state):
    with pytest.raises(ImportFailedException, match=state):
        run_target([import_response("STARTED"), import_response(state)])


def test_import_finished_on_create_is_checked():
    with pytest.raises(ImportFailedException, match="FAILED"):
        run_target([import_response("FAILED")])


def test_import_with_row_errors_fails(caplog):
    with pytest.raises(PartialImportException):
        run_target([import_response("DONE", {"ERRORS": 1, "CREATED_OBJECTS": 0})])

    assert "INVALID_EMAIL: bad email" in caplog.text


def test_import_timeout_fails():
    clock = iter([0, 0, 5])
    with pytest.raises(ImportTimeoutException, match="1 seconds"):
        run_target(
            [import_response("STARTED"), import_response("PROCESSING")],
            config={"import_timeout_seconds": 1},
            clock=lambda: next(clock),
        )
