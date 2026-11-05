"""HubSpot target sink class, which handles writing streams."""

from __future__ import annotations

import csv
import datetime
import json
import os
import tempfile
import time

from hubspot import HubSpot
from hubspot.crm.imports import ApiException
from singer_sdk.sinks import BatchSink

from target_hubspot.exception import (
    ImportFailedException,
    ImportTimeoutException,
    InvalidColumnMappingException,
    PartialImportException,
)

DEFAULT_DATE_FORMAT = "YEAR_MONTH_DAY"
DEFAULT_IMPORT_OPERATION = "UPDATE"
DEFAULT_IMPORT_TIMEOUT_SECONDS = 3600

# strftime patterns for the import request's `dateFormat` values
DATE_FORMATS = {
    "YEAR_MONTH_DAY": "%Y-%m-%d",
    "MONTH_DAY_YEAR": "%m/%d/%Y",
    "DAY_MONTH_YEAR": "%d/%m/%Y",
}

# https://developers.hubspot.com/docs/api/crm/imports
TERMINAL_STATES = {"DONE", "FAILED", "CANCELED", "REVERTED"}

POLL_INTERVAL_SECONDS = 2
MAX_POLL_INTERVAL_SECONDS = 30

# How many row errors to log when an import has errors
LOGGED_ERRORS_LIMIT = 10


class HubSpotSink(BatchSink):
    """HubSpot target sink class."""

    max_size = 10000  # Max records to write in one batch

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_client = HubSpot(access_token=self.config["access_token"])
        self.column_mappings = self._get_column_mappings()

    def _get_column_mappings(self) -> list[dict]:
        """Check the configured column mappings against the stream schema.

        Columns are matched to stream properties by name. Stream properties without a
        mapping are left out of the import.
        """
        mappings = self.config["column_mapping"]
        names = [mapping["columnName"] for mapping in mappings]
        properties = self.schema["properties"]

        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            msg = f"Column mapping lists these columns more than once: {duplicates}"
            raise InvalidColumnMappingException(msg)

        unknown = sorted(set(names) - set(properties))
        if unknown:
            msg = (
                f"Column mapping names columns that are not in stream "
                f"'{self.stream_name}': {unknown}. Stream properties: {sorted(properties)}"
            )
            raise InvalidColumnMappingException(msg)

        unmapped = sorted(set(properties) - set(names))
        if unmapped:
            self.logger.warning(
                "Stream '%s' properties without a column mapping are not imported: %s",
                self.stream_name,
                unmapped,
            )

        return mappings

    def _format_value(self, value) -> str:
        """Format a record value for the import file."""
        if value is None:
            return ""
        if isinstance(value, datetime.datetime):
            # HubSpot reads a UNIX timestamp in milliseconds from a CSV file for date
            # and time properties, which keeps the time and avoids time zone guesswork
            if value.tzinfo is None:
                value = value.replace(tzinfo=datetime.timezone.utc)
            return str(round(value.timestamp() * 1000))
        if isinstance(value, datetime.date):
            date_format = self.config.get("date_format", DEFAULT_DATE_FORMAT)
            return value.strftime(DATE_FORMATS[date_format])
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return str(value)

    def _write_csv(self, csv_path, records):
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(mapping["columnName"] for mapping in self.column_mappings)
            for record in records:
                writer.writerow(
                    self._format_value(record.get(mapping["columnName"]))
                    for mapping in self.column_mappings
                )

    def _get_import_operations(self) -> dict:
        """Apply the configured import operation to every object type being imported."""
        operation = self.config.get("import_operations", DEFAULT_IMPORT_OPERATION)
        object_type_ids = dict.fromkeys(
            mapping["columnObjectTypeId"] for mapping in self.column_mappings
        )
        return {object_type_id: operation for object_type_id in object_type_ids}

    def _build_import_request(self, import_name, file_name) -> dict:
        return {
            "name": import_name,
            "importOperations": self._get_import_operations(),
            "dateFormat": self.config.get("date_format", DEFAULT_DATE_FORMAT),
            "files": [
                {
                    "fileName": file_name,
                    "fileFormat": "CSV",
                    "fileImportPage": {
                        "hasHeader": True,
                        "columnMappings": self.column_mappings,
                    },
                }
            ],
        }

    def _start_import(self, csv_path, import_request):
        return self.api_client.crm.imports.core_api.create(
            files=csv_path,
            import_request=json.dumps(import_request),
        )

    def _wait_for_import(self, response):
        """Poll the import until it reaches a terminal state, backing off as it runs."""
        timeout = self.config.get(
            "import_timeout_seconds", DEFAULT_IMPORT_TIMEOUT_SECONDS
        )
        deadline = time.monotonic() + timeout
        interval = POLL_INTERVAL_SECONDS
        while response.state not in TERMINAL_STATES:
            if time.monotonic() >= deadline:
                msg = (
                    f"Import {response.id} did not finish within {timeout} seconds "
                    f"(state {response.state}). It may still complete in HubSpot."
                )
                raise ImportTimeoutException(msg)
            time.sleep(interval)
            interval = min(interval * 2, MAX_POLL_INTERVAL_SECONDS)
            response = self.api_client.crm.imports.core_api.get_by_id(int(response.id))
            self.logger.debug("Import %s Status: %s", response.id, response.state)
        return response

    def _log_import_errors(self, import_id):
        try:
            errors = self.api_client.crm.imports.public_imports_api.get_errors(
                int(import_id),
                limit=LOGGED_ERRORS_LIMIT,
                include_error_message=True,
            )
        except ApiException as ex:
            self.logger.warning(
                "Could not fetch errors for import %s: %s", import_id, ex
            )
            return
        for error in errors.results:
            self.logger.error(
                "Import %s row error %s: %s",
                import_id,
                error.error_type,
                error.error_message,
            )

    def _check_import(self, response):
        counters = (response.metadata.counters if response.metadata else None) or {}
        if response.state != "DONE":
            self._log_import_errors(response.id)
            msg = f"Import {response.id} ended in state {response.state}: {counters}"
            raise ImportFailedException(msg)
        if counters.get("ERRORS"):
            self._log_import_errors(response.id)
            msg = (
                f"Import {response.id} Had Errors Importing. See your import history "
                "https://knowledge.hubspot.com/crm-setup/view-and-analyze-previous-imports "
                f"for more information on troubleshooting errors: {counters}"
            )
            raise PartialImportException(msg)
        self.logger.info("Import %s Completed: %s", response.id, counters)

    def process_batch(self, context: dict) -> None:
        """Write out any prepped records and return once fully written.

        Args:
            context: Stream partition or context dictionary.
        """
        now_ts = datetime.datetime.now().timestamp()
        import_name = f"target-hubspot-{self.stream_name}-{now_ts}"
        file_name = f"{import_name}.csv"
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = os.path.join(tmp_dir, file_name)
            self._write_csv(csv_path, context["records"])
            import_request = self._build_import_request(import_name, file_name)
            response = self._wait_for_import(
                self._start_import(csv_path, import_request)
            )
        self._check_import(response)
