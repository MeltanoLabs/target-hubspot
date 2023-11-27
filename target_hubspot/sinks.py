"""HubSpot target sink class, which handles writing streams."""

from __future__ import annotations

import csv
import datetime
import json
import os
import time

from dateutil import parser
from hubspot import HubSpot
from singer_sdk.helpers._typing import (
    DatetimeErrorTreatmentEnum,
    get_datelike_property_type,
    handle_invalid_timestamp_in_record
)
from singer_sdk.sinks import BatchSink

from target_hubspot.exception import PartialImportException


IMPORT_OPERATIONS_LOOKUP = {
    "CREATE": {"0-1": "CREATE"},
    "UPDATE": {"0-2": "UPDATE"},
    "UPSERT": {"0-3": "UPSERT"},
}

class HubSpotSink(BatchSink):
    """HubSpot target sink class."""

    max_size = 10000  # Max records to write in one batch

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_client = HubSpot(access_token=self.config["access_token"])

    def _write_csv(self, csv_filename, records):
        with open(csv_filename, "w") as f:
            self.schema["properties"].keys()
            writer = csv.DictWriter(f, fieldnames=self._get_sorted_headers())
            writer.writeheader()
            for record in records:
                writer.writerow(self._sort_record(record))

    def _validate_column_mapping(self) -> None:
        stream_len = len(self.schema["properties"].keys())
        col_mapping_len = len(self.config["column_mapping"])
        if stream_len != col_mapping_len:
            raise Exception(f"The count of properties in the input stream does not match the count of column mappings. Please check your config. Stream: {stream_len} Column Mapping: {col_mapping_len}")

    def _get_sorted_column_mappings(self):
        return sorted(self.config["column_mapping"], key=lambda d: d['columnName']) 

    def _get_sorted_headers(self):
        return sorted(self.schema["properties"])

    def _sort_record(self, record):
        return dict(sorted(record.items()))

    def _build_request_kwargs(self, csv_filename, import_name):
        import_request = {
            "name": import_name,
            "importOperations": IMPORT_OPERATIONS_LOOKUP.get(self.config["import_operations"]),
            "dateFormat": self.config["date_format"],
            "files": [
            {
                "fileName": csv_filename,
                "fileFormat": "CSV",
                "fileImportPage": {
                    "hasHeader": True,
                    "columnMappings": self._get_sorted_column_mappings()

                }
            }
            ]
        }
        filtered_kwargs = {"files": csv_filename}
        filtered_kwargs['import_request'] = json.dumps(import_request)
        return filtered_kwargs

    def _start_import(self, request_kwargs):
        response = self.api_client.crm.imports.core_api.create(**request_kwargs)
        return response.id, response.state

    def _get_import_status(self, import_id):
        response = self.api_client.crm.imports.core_api.get_by_id(import_id)
        return response.state, response.metadata

    def _validate_completion_metadata(self, import_id, counters):
        if counters.get("ERRORS"):
            raise PartialImportException(f"Import {import_id} Had Errors Importing. See your import history https://knowledge.hubspot.com/crm-setup/view-and-analyze-previous-imports for more information on troubleshooting errors: {counters}")
        self.logger.info(f"Import {import_id} Completed: {counters}")

    def _import_csv_and_poll_for_status(self, request_kwargs):
        import_id, state = self._start_import(request_kwargs)
        while state not in {"DONE", "FAILED", "CANCELED"}:
            time.sleep(2)
            state, metadata = self._get_import_status(import_id)
            self.logger.debug(f"Import {import_id} Status: {state}")
        return import_id, metadata.counters

    def process_batch(self, context: dict) -> None:
        """Write out any prepped records and return once fully written.

        Args:
            context: Stream partition or context dictionary.
        """
        now_ts = datetime.datetime.now().timestamp()
        records = context["records"]
        import_name = f"target-hubspot-{self.stream_name}-{now_ts}"
        csv_filename = f"{import_name}.csv"
        try:
            self._write_csv(csv_filename, records)
            self._validate_column_mapping()
            request_kwargs = self._build_request_kwargs(csv_filename, import_name)
            import_id, completion_metadata = self._import_csv_and_poll_for_status(request_kwargs)
            self._validate_completion_metadata(import_id, completion_metadata)
        except Exception as ex:
            self.logger.error(f"Exception raised while submitting job to HubSpot: {ex}")
            raise ex
        finally:
            os.remove(csv_filename)

    def _parse_timestamps_in_record(
        self,
        record: dict,
        schema: dict,
        treatment: DatetimeErrorTreatmentEnum,
    ) -> None:
        """Parse strings to datetime.datetime values, repairing or erroring on failure.

        Attempts to parse every field that is of type date/datetime/time. If its value
        is out of range, repair logic will be driven by the `treatment` input arg:
        MAX, NULL, or ERROR.

        Args:
            record: Individual record in the stream.
            schema: TODO
            treatment: TODO
        """
        for key in record:
            datelike_type = get_datelike_property_type(schema["properties"][key])
            if datelike_type:
                date_val = record[key]
                try:
                    if record[key] is not None:
                        date_val = parser.parse(date_val)
                        # This forces all datelike types to dates, which is what the HubSpot API expects
                        date_val = date_val.date()
                        # TODO: add to SDK so date is returned instead of datetime
                        # if datelike_type == "date":
                        #     date_val = date_val.date()
                except parser.ParserError as ex:
                    date_val = handle_invalid_timestamp_in_record(
                        record,
                        [key],
                        date_val,
                        datelike_type,
                        ex,
                        treatment,
                        self.logger,
                    )
                record[key] = date_val