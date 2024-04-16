"""
Copyright (c) 2024 valmi.io <https://github.com/valmi-io>

Created Date: Wednesday, March 8th 2023, 9:56:52 pm
Author: Rajashekar Varkala @ valmi.io

"""

import logging
from typing import Dict, List

from decouple import Csv, config
from ninja import Router

from core.schemas import ConnectorSchema, DetailSchema, PackageSchema, PromptSchema, SyncSchema

from .models import (
    Connector,
    Package,
    Prompt,
    Sync,
    OAuthApiKeys
)
import json

from opentelemetry.metrics import get_meter_provider
# from opentelemetry import trace

from valmi_app_backend.utils import replace_values_in_json

router = Router()

# Get an instance of a logger
logger = logging.getLogger(__name__)

meter = get_meter_provider().get_meter("engine_api", "test_version_number")


# Create /syncs api counter
syncs_api_counter = meter.create_counter("syncs_api_counter")


@router.get("/syncs/", response={200: List[SyncSchema], 400: DetailSchema})
def get_all_syncs(request):

    syncs_api_counter.add(1)

    # check for admin permissions
    try:
        syncs = Sync.objects.select_related("source", "destination")

        # Replacing Oauth keys
        oauth_proxy_keys = config("OAUTH_SECRETS", default="", cast=Csv(str))

        if len(oauth_proxy_keys) > 0:
            for sync in syncs:
                src_dst = [sync.source, sync.destination]

                for obj in src_dst:
                    workspace = obj.credential.workspace
                    connector_type = obj.credential.connector.type

                    queryset = OAuthApiKeys.objects.filter(workspace=workspace, type=connector_type)

                    if queryset.exists():

                        keys = queryset.first()

                        # Replacing oauth keys with db values
                        obj.credential.connector_config = replace_values_in_json(
                            obj.credential.connector_config, keys.oauth_config)
                    else:

                        # Replacing oauth keys with .env values
                        config_str = json.dumps(obj.credential.connector_config)

                        for key in oauth_proxy_keys:
                            config_str = config_str.replace(key, config(key))
                        obj.credential.connector_config = json.loads(config_str)

        return syncs
    except Exception:
        logger.exception("syncs all error")
        return (400, {"detail": "The syncs cannot be fetched."})


@router.post("/connectors/create", response={200: ConnectorSchema, 400: DetailSchema})
def create_connector(request, payload: ConnectorSchema):
    # check for admin permissions
    data = payload.dict()
    try:
        logger.debug("creating connector")
        connector = Connector.objects.create(**data)

        return (200, connector)
    except Exception:
        logger.exception("Connector error")
        return (400, {"detail": "The specific connector cannot be created."})

@router.post("/prompts/create", response={200: PromptSchema, 400: DetailSchema})
def create_connector(request, payload: PromptSchema):
    # check for admin permissions
    data = payload.dict()
    logger.debug(data)
    try:
        logger.debug("creating prompt")
        prompts = Prompt.objects.create(**data)
        return (200, PromptSchema)
    except Exception:
        logger.exception("Prompt error")
        return (400, {"detail": "The specific prompt cannot be created."})
    

@router.post("/packages/create", response={200: PackageSchema, 400: DetailSchema})
def create_connector(request, payload: PackageSchema):
    # check for admin permissions
    logger.info("logging package schema")
    data = payload.dict()
    logger.debug(data)
    try:
        logger.debug("creating package")
        package = Package.objects.create(**data)
        return (200, PackageSchema)
    except Exception:
        logger.exception("Package error")
        return (400, {"detail": "The specific package cannot be created."})

@router.get("/connectors/", response={200: Dict[str, List[ConnectorSchema]], 400: DetailSchema})
def get_connectors(request):
    # check for admin permissions
    try:
        logger.debug("listing connectors")
        connectors = Connector.objects.all()
        src_dst_dict: Dict[str, List[ConnectorSchema]] = {}
        src_dst_dict["SRC"] = []
        src_dst_dict["DEST"] = []
        for conn in connectors:
            arr = conn.type.split("_")
            if arr[0] == "SRC":
                src_dst_dict["SRC"].append(conn)
            elif arr[0] == "DEST":
                src_dst_dict["DEST"].append(conn)
        return src_dst_dict
    except Exception:
        logger.exception("connector listing error")
        return (400, {"detail": "The list of connectors cannot be fetched."})
