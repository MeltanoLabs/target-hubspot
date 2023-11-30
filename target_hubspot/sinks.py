"""HubSpot target sink class, which handles writing streams."""

from __future__ import annotations

from typing import Any, List

from singer_sdk.sinks import BatchSink

from target_hubspot.client import HubspotClient
from target_hubspot.constants import TargetConfig
from target_hubspot.model import HubspotObjectsEnum

IMPORT_OPERATIONS_LOOKUP = {
    "CREATE": {"0-1": "CREATE"},
    "UPDATE": {"0-2": "UPDATE"},
    "UPSERT": {"0-3": "UPSERT"},
}


class HubSpotSink(BatchSink):
    """
    Main service class. Entrypoint for handling records. You can view this as a black box that takes in Singer records and dumps them into HubSpot.

    Responsible:
    - Entrypoint for handling a batch of records
    - Mapping from Singer to HubspotClient's strictly defined request body types

    NOT responsible:
    - Making requests (handled by HubspotClient)
    - Handling retry logic (handled by HubspotClient)

    We use BatchSink rather than RecordSink because HubSpot supports bulk updates to things like contacts (https://legacydocs.hubspot.com/docs/methods/contacts/batch_create_or_update) and this lets us get much more throughput considering HubSpot rate limits at 100 requests per 10 seconds per end OAuth user.

    This won't matter for toy datasets, but will absolutely be meaningful for big clients, especially if we end up having to basically re-sync things every time.
    """

    _typed_config: TargetConfig # strongly typed variant that helps stop bugs
    _client: HubspotClient

    max_size = 100  # base sink attribute that determines max batch size; HubSpot supports up to 1,000, but recommends 100, so we'll stick w/ their recommendation and just remember we can tune it at a later point if desired

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._typed_config = TargetConfig(**self.config)
        self._client = HubspotClient(
            config=self._typed_config,
            logger=self.logger
        )

    def _handle_batch_contacts(self, records: List[dict]) -> None:
        def _transform_record(record: dict) -> dict:
            # transform a given record into the format HubSpot expects
            return {
                "vid": record["id"],
                "properties": [
                    {"property": key, "value": "value"}
                    for key, value
                    in record.items() if key != "id"
                ]
            }

        self.logger.info(f"Successfully updated {len(records)} records.")

    def _handle_batch_companies(self, records: List[dict]) -> None:
        raise NotImplementedError()

    def _handle_batch_deals(self, records: List[dict]) -> None:
        raise NotImplementedError()

    def process_batch(self, context: dict) -> None:
        """
        Processes list of records. Because we don't override `process_record()`, Meltano SDK automatically aggregates them into batches and feeds them in here at the `records` key of the `context` dict.
        """
        records = context["records"]
        self.logger.info(f"Processing batch. Has {len(records)} records.")
        try:
            if self._typed_config.stream_identifier == HubspotObjectsEnum.CONTACTS:
                self._handle_batch_contacts(records)
            elif self._typed_config.stream_identifier == HubspotObjectsEnum.COMPANIES:
                self._handle_batch_companies(records)
            elif self._typed_config.stream_identifier == HubspotObjectsEnum.DEALS:
                self._handle_batch_deals(records)
            else:
                raise NotImplementedError(f"Unsupported stream identifier: {self._typed_config.stream_identifier}. Available Options: {HubspotObjectsEnum.__members__.values()}")
        except Exception as e:
            self.logger.error(f"Exception raised when pushing records up to HubSpot: {e}")
            raise e
