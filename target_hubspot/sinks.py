"""HubSpot target sink class, which handles writing streams."""

from __future__ import annotations

import datetime
from typing import Any

from hubspot import HubSpot
from singer_sdk.sinks import BatchSink

from target_hubspot.constants import TargetConfig
from target_hubspot.exception import PartialImportException

IMPORT_OPERATIONS_LOOKUP = {
    "CREATE": {"0-1": "CREATE"},
    "UPDATE": {"0-2": "UPDATE"},
    "UPSERT": {"0-3": "UPSERT"},
}

class HubSpotSink(BatchSink):
    """
    HubSpot target sink class. Essentially a black box that takes individual records (batches) in and actually dumps them up into HubSpot.

    We use BatchSink rather than RecordSink because HubSpot supports bulk updates to things like contacts (https://legacydocs.hubspot.com/docs/methods/contacts/batch_create_or_update) and this lets us get much more throughput considering HubSpot rate limits at 100 requests per 10 seconds per end OAuth user.

    This won't matter for toy datasets, but will absolutely be meaningful for big clients, especially if we end up having to basically re-sync things every time.
    """
    _typed_config: TargetConfig # strongly typed variant that helps stop bugs
    _api_client: HubSpot

    MAX_CONTACTS_BATCH_SIZE = 1000  # hard limit to size we can make batches; see: https://legacydocs.hubspot.com/docs/methods/contacts/batch_create_or_update

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.logger.info(f"Attempting to parse this config as a strongly typed Pydantic object: {self.config}")
        self._typed_config = TargetConfig(**self.config)

    def _validate_completion_metadata(self, import_id: str, counters: dict) -> None:
        if counters.get("ERRORS"):
            raise PartialImportException(f"Import {import_id} Had Errors Importing. See your import history https://knowledge.hubspot.com/crm-setup/view-and-analyze-previous-imports for more information on troubleshooting errors: {counters}")
        self.logger.info(f"Import {import_id} Completed: {counters}")

    # def process_record(self, record: dict, context: dict) -> None:
    #     """Process a single record."""
    #     self.logger.info(f"process_record called with config {self._typed_config} and record {record} and context {context}")
    #     raise NotImplementedError("process_record is not implemented")

    def process_batch(self, context: dict) -> None:
        """Write out any prepped records and return once fully written.

        Args:
            context: Stream partition or context dictionary.
        """
        self.logger.info(f"process_batch processing context: {context}")
        now_ts = datetime.datetime.now().timestamp()
        records = context["records"]
        self.logger.info(f"Processing Records: {records}")
        import_name = f"target-hubspot-{self.stream_name}-{now_ts}"
        csv_filename = f"{import_name}.csv"
        try:
            self.logger.info(f"Processing Records: {records}")
            # df = pd.read_csv(self._typed_config.filepath)
            # self._write_csv(csv_filename, records)
            # self._validate_column_mapping()
            # request_kwargs = self._build_request_kwargs(csv_filename, import_name)
            # import_id, completion_metadata = self._import_csv_and_poll_for_status(request_kwargs)
            # self._validate_completion_metadata(import_id, completion_metadata)
            self.logger.info("Example!")
        except Exception as e:
            self.logger.error(f"Exception raised when pushing records up to HubSpot: {e}")
            raise e
