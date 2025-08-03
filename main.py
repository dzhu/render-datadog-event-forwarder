#!/usr/bin/env python3

import json
import os

from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.events_api import EventsApi
from datadog_api_client.v2.model.alert_event_custom_attributes import AlertEventCustomAttributes
from datadog_api_client.v2.model.event_category import EventCategory
from datadog_api_client.v2.model.event_create_request import EventCreateRequest
from datadog_api_client.v2.model.event_create_request_payload import EventCreateRequestPayload
from datadog_api_client.v2.model.event_create_request_type import EventCreateRequestType
from datadog_api_client.v2.model.event_payload import EventPayload

from flask import Flask, request
from standardwebhooks.webhooks import Webhook


STATUS_MAP = {
    "server_failed": "error",
    "server_hardware_failure": "error",
    "server_unhealthy": "warn",
    "postgres_backup_failed": "warn",
    "pastgres_pitr_checkpoint_failed": "warn",
    "postgres_restore_failed": "warn",
    "postgres_unavailable": "error",
    "postgres_upgrade_failed": "warn",
    "postgres_read_replica_stale": "warn",
    "key_value_unhealthy": "warn",
}

wh = Webhook(os.environ["WH_SECRET"])

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 << 15


# Reads DD_SITE, DD_API_KEY, and DD_APP_KEY from the environment.
configuration = Configuration()
dd_client = ApiClient(configuration)
events = EventsApi(dd_client)


@app.route("/hook", methods=["POST"])
def hook():
    body = request.get_data()
    wh.verify(body, request.headers)
    data = json.loads(body)
    events.create_event(
        body=EventCreateRequestPayload(
            data=EventCreateRequest(
                attributes=EventPayload(
                    category=EventCategory.ALERT,
                    timestamp=data["timestamp"],
                    title=data["type"],
                    attributes=AlertEventCustomAttributes(
                        status=STATUS_MAP.get(data["type"], "ok"),
                        custom={
                            "event_id": data["data"]["id"],
                            "service_id": data["data"]["serviceId"],
                        },
                    ),
                ),
                type=EventCreateRequestType.EVENT,
            ),
        )
    )
    return ""
