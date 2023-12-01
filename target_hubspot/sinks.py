"""HubSpot target sink class, which handles writing streams."""

from __future__ import annotations

from typing import Any, Dict, List

from singer_sdk.sinks import BatchSink

from target_hubspot.constants import AKKIO_PROPERTY_GROUP_LABEL, AKKIO_PROPERTY_GROUP_NAME
from target_hubspot.encoder import TypeInferenceUtils
from target_hubspot.model import HubspotObjectsEnum, TargetConfig
from target_hubspot.remote.client import HubspotClient
from target_hubspot.remote.model import BatchCreateProperties, BatchUpdate, CreatePropertyGroup, HubspotGenericItemUpdatePayload, HubspotPropertyPayload

IMPORT_OPERATIONS_LOOKUP = {
    "CREATE": {"0-1": "CREATE"},
    "UPDATE": {"0-2": "UPDATE"},
    "UPSERT": {"0-3": "UPSERT"},
}

def _is_safe_key_to_modify(key: str) -> bool:
    # In order to avoid any situations where we're messing w/ or even overwriting customer data we have nothing to do with, we pretty strictly limit the properties we're willing to modify.
    return key != "id" and key.startswith("akkio")


def _sanitize_record(record: dict) -> dict:
    # sanitizes a given dict such that only values we know we want to update, and we know are safe to update, are present
    output = {}
    for key, value in record.items():
        if _is_safe_key_to_modify(key):
            output[key] = TypeInferenceUtils.coerce_to_json_serializable(value)
    return output

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
    _hubspot_client: HubspotClient


    max_size = 100  # base sink attribute that determines max batch size; HubSpot supports up to 1,000, but recommends 100, so we'll stick w/ their recommendation and just remember we can tune it at a later point if desired

    _first_record_setup_complete: bool = False  # whether we've pushed any new custom attributes up to HubSpot yet, which we want to do once at the beginning of each sync (as we can depend on schema being consistent across all records).
    def _setup_with_first_record(self, record: Dict[str, Any]) -> None:
        self._hubspot_client.create_property_group(
            payload=CreatePropertyGroup.RequestPayload(
                name=AKKIO_PROPERTY_GROUP_NAME,
                label=AKKIO_PROPERTY_GROUP_LABEL
            )
        )

        properties = [
            HubspotPropertyPayload(
                label=key, # TODO: Bit of a transform to be more user-friendly might be nice here
                name=key,
                id=key,
                type=TypeInferenceUtils.determine_hubspot_data_type_for_object(value),
                groupName=AKKIO_PROPERTY_GROUP_LABEL,
                fieldType=TypeInferenceUtils.determine_hubspot_field_type_for_object(value)
            )
            for key, value in record.items()
            if _is_safe_key_to_modify(key)
        ]
        self.logger.info(f"Pushing {len(properties)} new properties to HubSpot: {[property.name for property in properties]}")
        self._hubspot_client.batch_create_properties(
            payload=BatchCreateProperties.RequestPayload(
                inputs=properties,
            )
        )
        self._first_record_setup_complete = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._typed_config = TargetConfig(**self.config)
        self._hubspot_client = HubspotClient(
            config=self._typed_config,
            logger=self.logger
        )

    def _handle_batch_contacts(self, records: List[dict]) -> None:
        self.logger.info(f"Pushing updates to {len(records)} contacts (IDs: {[record['id'] for record in records]})")
        self._hubspot_client.batch_update_contacts(
            payload=BatchUpdate.RequestPayload(
                inputs=[
                    HubspotGenericItemUpdatePayload(
                        id=record["id"],
                        properties=_sanitize_record(record)
                    ) for record in records
                ]
            )
        )
        self.logger.info(f"Successfully updated {len(records)} HubSpot contacts.")

    def _handle_batch_companies(self, records: List[dict]) -> None:
        self.logger.info(f"Pushing updates to {len(records)} users (IDs: {[record['id'] for record in records]})")
        self._hubspot_client.batch_update_companies(
            payload=BatchUpdate.RequestPayload(
                inputs=[
                    HubspotGenericItemUpdatePayload(
                        id=record["id"],
                        properties=_sanitize_record(record)
                    ) for record in records
                ]
            )
        )
        self.logger.info(f"Successfully updated {len(records)} HubSpot companies.")

    def _handle_batch_deals(self, records: List[dict]) -> None:
        self.logger.info(f"Pushing updates to {len(records)} deals (IDs: {[record['id'] for record in records]})")
        self._hubspot_client.batch_update_companies(
            payload=BatchUpdate.RequestPayload(
                inputs=[
                    HubspotGenericItemUpdatePayload(
                        id=record["id"],
                        properties=_sanitize_record(record)
                    ) for record in records
                ]
            )
        )
        self.logger.info(f"Successfully updated {len(records)} HubSpot deals.")

    def process_batch(self, context: dict) -> None:
        """
        Processes list of records. Because we don't override `process_record()`, Meltano SDK automatically aggregates them into batches and feeds them in here at the `records` key of the `context` dict.
        """
        records = context["records"]
        self.logger.info(f"Processing batch. Has {len(records)} records.")

        if not self._first_record_setup_complete:
            # Handler for one-time operations that can't be in general setup() hook b/c they require schema knowledge
            self._setup_with_first_record(context["records"][0])

        try:
            if self._typed_config.object_type == HubspotObjectsEnum.CONTACTS:
                self._handle_batch_contacts(records)
            elif self._typed_config.object_type == HubspotObjectsEnum.COMPANIES:
                self._handle_batch_companies(records)
            elif self._typed_config.object_type == HubspotObjectsEnum.DEALS:
                self._handle_batch_deals(records)
            else:
                # TODO: We can add more / all object types here at some point in the future if we have demand, just focusing on Jon's "big three" (Contacts, Companies, Deals) for now.
                raise NotImplementedError(f"Unsupported stream identifier: {self._typed_config.object_type}. Available Options: {HubspotObjectsEnum.__members__.values()}")
        except Exception as e:
            self.logger.error(f"Exception raised when pushing records up to HubSpot: {e}")
            raise e
